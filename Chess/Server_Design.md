# Server Design - Chess Multiplayer

אפיון מלא של ארכיטקטורת מיקרו-סרוויסים עבור מערכת שחמט מרובת משתמשים.

---

## עקרון מרכזי

ה-GameEngine הוא ה-Single Source of Truth היחיד לחוקי המשחק.
הלקוח לא מחליט. ה-Gateway לא מחליט. רק ה-Game Shard מחליט.

---

## מצב מימוש

| שירות | מצב |
|-------|-----|
| API Gateway | ממומש ✅ |
| WebSocket Gateway | ממומש חלקית ✅ (עדיין מכיל matchmaking + game logic - יופרדו) |
| Matchmaker | לא קיים עדיין כשירות נפרד ❌ |
| Game Allocator | לא קיים עדיין ❌ |
| Game Shard | לא קיים עדיין כשירות נפרד ❌ |
| Rating Service | לא קיים עדיין כשירות נפרד ❌ |
| Observability | חלקי ❌ |

---

## רכיבי המערכת

### 1. UI (Client)

רץ אצל המשתמש. אחראי על תצוגה וקלט בלבד.

**אחריות:**
- מציג את לוח המשחק לפי snapshot שמגיע מהשרת
- שולח קליקים של המשתמש לשרת
- מנהל מסך הבית: login, חיפוש משחק, יצירת/הצטרפות לחדר, היסטוריה
- מציג ספירה לאחור כשהיריב התנתק
- מציג תוצאה סופית בסיום משחק

**מה ה-UI לא עושה:**
- לא מחשב חוקי משחק
- לא מחליט אם מהלך חוקי
- לא מחזיק state של המשחק - רק מציג מה שהשרת שולח

**קבצים:**
```
UI/py/
├── network/
│   ├── ws_client.py          ← חיבור WebSocket לשרת
│   ├── api_client.py         ← קריאות HTTP ל-API Gateway
│   ├── home_flow.py          ← זרימת מסך הבית
│   ├── home_gate.py
│   ├── remote_controller.py  ← מקבל state מהשרת ומעדכן UI
│   └── move_log.py
├── gui/
│   ├── home_screen.py
│   ├── login_dialog.py
│   └── room_dialog.py
├── render/
│   └── renderer.py           ← ציור הלוח
└── animation/
    └── ...                   ← אנימציות כלים
```

---

### 2. API Gateway

מטפל בכל הבקשות שאינן real-time. HTTP בלבד.

**Endpoints:**
- `POST /register` - הרשמה
- `POST /login` - התחברות, מחזיר JWT token
- `GET /profile/{username}` - פרופיל שחקן + rating
- `GET /history/{username}` - היסטוריית משחקים

**מתחבר ל:** PostgreSQL בלבד.

**לא מתחבר ל:** Redis, WebSocket, שירותים אחרים.

**קבצים:**
```
api_gateway/
├── app.py
├── auth/
│   ├── auth_service.py
│   └── password_hasher.py
├── persistence/
│   ├── player_repository.py
│   └── game_repository.py
├── Dockerfile
└── requirements.txt
```

---

### 3. WebSocket Gateway

מנהל חיבורי WebSocket מול clients. **מנתב בלבד - לא מריץ לוגיקה.**

**אחריות:**
- מקבל חיבור WebSocket, מאמת JWT token
- שומר ב-Redis: `ws:conn:{username}` → `instance_id` (כדי שאפשר למצוא את החיבור מכל שירות)
- מנתב הודעות נכנסות:
  - `find_match` / `create_room` / `join_room` → Redis PubSub לשירות המתאים
  - `move_click` / `jump_click` → Redis PubSub: `game:input:{room_id}`
- מאזין ל-Redis PubSub: `ws:out:{instance_id}` ושולח הודעות ל-clients המחוברים אליו
- מטפל בניתוק: מוחק `ws:conn:{username}` מ-Redis, מודיע ל-Game Shard

**בעיית ריבוי מופעים:**
כל מופע מחזיק בזיכרון רק את החיבורים שנפתחו אליו.
כשה-Game Shard רוצה לשלוח state update לשחקן - הוא קורא מ-Redis את ה-`instance_id` של אותו שחקן ושולח לערוץ `ws:out:{instance_id}`. המופע הנכון מקבל ושולח ל-client.

**קבצים:**
```
ws_gateway/
├── main.py
├── net/
│   ├── ws_server.py
│   ├── connection.py
│   ├── dispatch.py
│   └── health.py
└── config.py
```

---

### 4. Matchmaker

מחפש התאמות בין שחקנים לפי rating.

**אחריות:**
- מקבל בקשת `find_match` מה-WS Gateway דרך Redis PubSub
- מחפש יריב מתאים בתור (טווח של 100 נקודות rating)
- אם מצא זוג → שולח ל-Game Allocator דרך Redis PubSub
- אם לא מצא → מוסיף לתור עם TTL
- מריץ sweep כל 10 שניות: מנקה entries שפג תוקפם ושולח `no_match_found` ל-client

**בעיית ריבוי מופעים:**
התור חייב להיות משותף לכל המופעים - לא בזיכרון של מופע אחד.

**פתרון - Redis Sorted Set:**
```
mm:queue              → Sorted Set  { member: username, score: rating }
mm:entry:{username}   → Hash        { rating, joined_at, ws_instance_id }
                                      עם EXPIRE של 70 שניות
```

- `find_match(rating)` = `ZRANGEBYSCORE mm:queue [rating-100] [rating+100]`
- כל מופע של Matchmaker יכול לקרוא ולכתוב לאותו Sorted Set
- אין race condition כי `ZREM` ב-Redis הוא atomic

**TTL ו-Timeout:**
- כל entry מקבל `EXPIRE 70s` ב-Redis
- Matchmaker sweep כל 10s: בודק `joined_at`, אם עבר 60s → שולח `no_match_found` → מוחק

**קבצים:**
```
matchmaker/
├── main.py
├── matchmaker_service.py
├── redis_queue.py        ← Sorted Set במקום in-memory dict
└── config.py
```

---

### 5. Game Allocator

מחליט על איזה Game Shard ירוץ כל room חדש.

**אחריות:**
- מקבל "room חדש" מה-Matchmaker או מ-WS Gateway (create_room)
- בוחר את ה-Shard עם הכי פחות עומס
- שומר ב-Redis: `room:shard:{room_id}` → `shard_id`
- מודיע ל-Shard הנבחר להתחיל את המשחק דרך Redis PubSub: `game:start:{shard_id}`
- מעדכן: `shard:load:{shard_id}` + 1

**בעיית ריבוי מופעים:**
כל הכתיבה ל-Redis היא atomic, אז אין race condition גם אם יש כמה מופעים של Allocator.

**Redis:**
```
room:shard:{room_id}   → String   shard_id          (TTL: משך המשחק + buffer)
shard:load:{shard_id}  → Integer  מספר rooms פעילים
```

**קבצים:**
```
game_allocator/
├── main.py
├── allocator_service.py
└── config.py
```

---

### 6. Game Server Shard

מריץ את המשחקים בפועל. **Single Source of Truth.**

**אחריות:**
- מריץ GameEngine מה-core לכל room שהוקצה לו
- מקבל קליקים דרך Redis PubSub: `game:input:{room_id}`
- מריץ TickLoop ושולח state updates דרך Redis PubSub: `ws:out:{instance_id}`
- מטפל בניתוק שחקן: מתחיל DisconnectTimer של 20 שניות
- מטפל בחיבור מחדש: שולח snapshot מלא
- בסיום משחק: שומר היסטוריה ב-PostgreSQL, מפרסם GAME_ENDED, מוחק `room:shard:{room_id}` מ-Redis
- **לא** מחשב ELO - זו אחריות של Rating Service
 

**Reconnect:**
כששחקן מתחבר מחדש → WS Gateway קורא `room:shard:{room_id}` מ-Redis → שולח בקשת reconnect לShard הנכון → ה-Shard שולח snapshot מלא → ה-DisconnectTimer מבוטל.

**קבצים:**
```
game_shard/
├── main.py
├── game/
│   ├── game_session.py
│   ├── session_manager.py
│   ├── click_handler.py
│   ├── tick_loop.py
│   ├── broadcaster.py
│   └── disconnect_timer.py
├── persistence/
│   ├── game_repository.py
│   ├── move_repository.py
│   └── game_history_recorder.py
└── config.py
```

---

### 7. Rating Service

מאזין ל-GAME_ENDED ומעדכן ratings. שכבה נפרדת לחלוטין מהמשחק עצמו.

**למה נפרד מה-Game Shard?**
Game Shard אחראי על הרצת משחקים בלבד. חישוב ELO זו אחריות אחרת - אם מחר משנים את הנוסחה, לא נוגעים ב-Game Shard.

**אחריות:**
- מאזין ל-Redis PubSub: `events:game_ended`
- שולף ratings של שני השחקנים מ-PostgreSQL
- מחשב ELO חדש
- מעדכן PostgreSQL
- מפרסם `events:elo_updated` (לצורך observability / עתידי)

**בעיית ריבוי מופעים:**
אם יש כמה מופעים - שניהם יקבלו את אותו GAME_ENDED ויעדכנו פעמיים.
פתרון: `SET NX rating:lock:{room_id} EX 30` לפני העדכון. רק המופע שתפס את ה-lock מעדכן.

**קבצים:**
```
rating_service/
├── main.py
├── rating_service.py
├── elo.py            ← לוגיקה טהורה, ללא I/O
└── config.py
```

---

### 8. Observability

ניטור כל השירותים.

**אחריות:**
- Health checks לכל שירות (polling)
- איסוף logs מרוכז
- מדדים: מספר משחקים פעילים, זמן תגובה, גודל תור matchmaking

**קבצים:**
```
observability/
├── health_checker.py
└── log_aggregator.py
```

---

## Redis - מפת כל המפתחות

| מפתח | סוג | תוכן | TTL |
|------|-----|------|-----|
| `session:{token}` | Hash | username, expires | 24h |
| `ws:conn:{username}` | String | instance_id של WS Gateway | נמחק בניתוק |
| `mm:queue` | Sorted Set | username → rating | - |
| `mm:entry:{username}` | Hash | rating, joined_at, ws_instance_id | 70s |
| `room:shard:{room_id}` | String | shard_id | משך המשחק |
| `shard:load:{shard_id}` | Integer | מספר rooms פעילים | - |
| `rating:lock:{room_id}` | String | lock למניעת עדכון כפול | 30s |

---

## PostgreSQL - טבלאות

| טבלה | תוכן |
|------|------|
| `players` | username, password_hash, rating |
| `games` | room_id, white, black, winner, reason, started_at, ended_at |
| `moves` | game_id, seq, color, start, end, clock_tick |

---

## תשתית

- **Redis PubSub** - תקשורת פנימית בין שירותים
- **Redis** - shared state: sessions, תורים, מיפויים
- **PostgreSQL** - נתונים קבועים
- **Docker Compose** - פיתוח מקומי (מופע אחד מכל שירות)
- **Kubernetes / K3s** - production (scale לכל שירות בנפרד)

---

## אבטחה

- סיסמאות מוצפנות עם bcrypt + salt
- JWT tokens לאימות
- Parameterized Queries למניעת SQL Injection
- HTTPS + WSS בכל התעבורה
- Rate Limiting ב-API Gateway

---

## דיאגרמות זרימה

### התחברות

```
Client
  │
  ├─[POST /login]──────────────────► API Gateway ──► PostgreSQL
  │                                       │
  │                                   JWT token
  │◄───────────────────────────────────────┘
  │
  ├─[WS connect + JWT]─────────────► WS Gateway
  │                                       │
  │                              אימות token
  │                              Redis: ws:conn:{username} → instance_id
  │◄──── login_ok ─────────────────────────┘
```

---

### חיפוש משחק והתחלה

```
Client
  │
  ├─[find_match]───────────────────► WS Gateway
  │                                       │
  │                           Redis PubSub: mm:requests
  │                                       │
  │                                  Matchmaker
  │                                       │
  │                          ┌────────────┴────────────┐
  │                      מצא זוג                  לא מצא
  │                          │                         │
  │                          │                  Redis Sorted Set:
  │                          │                  mm:queue (TTL 70s)
  │                          │                         │
  │                          │                  [אחרי 60s sweep]
  │                          │                         │
  │◄── no_match_found ───────────────── WS Gateway ◄───┘
  │
  │                  Redis PubSub: allocator:new_room
  │                          │
  │                    Game Allocator
  │                          │
  │               בחר Shard עם הכי פחות עומס
  │               Redis: room:shard:{id} → shard_id
  │               Redis: shard:load:{shard_id} + 1
  │                          │
  │                  Redis PubSub: game:start:{shard_id}
  │                          │
  │                     Game Shard
  │                          │
  │                 יצר GameSession + TickLoop
  │                          │
  │              Redis PubSub: ws:out:{instance_id_של_כל_שחקן}
  │                          │
  │◄──── role_assigned ─── WS Gateway
  │◄──── state ────────────────────────┘
```

---

### מהלך במשחק

```
Client
  │
  ├─[move_click row,col]───────────► WS Gateway
  │                                       │
  │                           Redis PubSub: game:input:{room_id}
  │                                       │
  │                                  Game Shard
  │                                       │
  │                            GameEngine.handle_click()
  │                            (בדיקת חוקיות, עדכון state)
  │                                       │
  │                    Redis PubSub: ws:out:{instance_id_w}
  │                                   ws:out:{instance_id_b}
  │                                       │
  │                              WS Gateway (המופע הנכון)
  │                                       │
  │◄──── state ──────────────────────────►│──── state ──► Client B
```

---

### ניתוק שחקן במהלך משחק

```
Client A מתנתק
  │
WS Gateway
  │
  ├─ מוחק Redis: ws:conn:{username_A}
  ├─ Redis PubSub: game:disconnect:{room_id}
  │
Game Shard
  │
  ├─ מתחיל DisconnectTimer (20 שניות)
  ├─ כל שניה: שולח ל-Client B { type: "opponent_left", seconds_remaining: N }
  │
  ├─[Client A חוזר תוך 20s]
  │       │
  │   WS Gateway: ws:conn:{username_A} → instance_id (חדש)
  │   Redis: room:shard:{room_id} → shard_id
  │   Redis PubSub: game:reconnect:{room_id}
  │       │
  │   Game Shard:
  │   ├─ מבטל DisconnectTimer
  │   ├─ שולח snapshot מלא ל-Client A
  │   └─ שולח ל-Client B { type: "opponent_returned" }
  │
  └─[Client A לא חוזר תוך 20s]
          │
      Game Shard:
      ├─ resign(color_A) → Client B מנצח
      ├─ שולח state סופי לשני הצדדים
      ├─ שומר תוצאה ב-PostgreSQL
      ├─ מפרסם GAME_ENDED → Rating Service מחשב ELO בנפרד
      └─ מוחק Redis: room:shard:{room_id}
         מעדכן Redis: shard:load:{shard_id} - 1
```

---

### סיום משחק תקין (מלך נלכד)

```
Game Shard - TickLoop
  │
  ├─ GameEngine מזהה game_over
  ├─ שולח state סופי לשני clients דרך WS Gateway
  ├─ GameHistoryRecorder: שומר תוצאה ב-PostgreSQL
  ├─ מפרסם Redis PubSub: events:game_ended
  │       │
  │  Rating Service (שירות נפרד)
  │       ├─ SET NX rating:lock:{room_id} EX 30
  │       ├─ מחשב ELO חדש
  │       └─ מעדכן PostgreSQL
  │
  └─ מוחק Redis: room:shard:{room_id}
     מעדכן Redis: shard:load:{shard_id} - 1

Client A + Client B
  └─ מקבלים { type: "state", game_over: true, winner: "white" }
     UI מציג מסך תוצאה
```

---

### יצירת חדר ידנית (create_room / join_room)

```
Client A
  │
  ├─[create_room]──────────────────► WS Gateway
  │                                       │
  │                              Redis PubSub: allocator:new_room
  │                                       │
  │                                Game Allocator
  │                                       │
  │                           בוחר Shard, שומר room:shard:{id}
  │                                       │
  │◄──── role_assigned (white, room_id) ──┘

Client B
  │
  ├─[join_room room_id]────────────► WS Gateway
  │                                       │
  │                           Redis: room:shard:{room_id} → shard_id
  │                           Redis PubSub: game:join:{shard_id}
  │                                       │
  │                                  Game Shard
  │                                       │
  │                              מושיב שחקן שני, מתחיל משחק
  │                                       │
  │◄──── role_assigned (black) ───────────┘
  │◄──── state ───────────────────────────┘

[אם חדר מלא - שחקן נוסף מצטרף כצופה]
  ├─[join_room room_id]────────────► WS Gateway → Game Shard
  │◄──── spectating ──────────────────────────────────────────┘
  │◄──── state (ללא הצגת מהלכים אפשריים) ────────────────────┘
```

---

## Docker Compose (פיתוח מקומי)

```yaml
services:
  postgres:        # נתונים קבועים
  redis:           # shared state + PubSub
  api_gateway:     # HTTP - login, history
  ws_gateway:      # WebSocket - חיבורי clients
  matchmaker:      # חיפוש יריב
  game_allocator:  # הקצאת rooms ל-shards
  game_shard:      # הרצת משחקים
  rating_service:  # חישוב ELO
  observability:   # ניטור
```

בפיתוח מקומי - מופע אחד מכל שירות.
ב-Kubernetes - אפשר לעשות scale לכל שירות בנפרד לפי עומס.
