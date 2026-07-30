FROM python:3.12-slim

WORKDIR /app

COPY ws_gateway/requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

COPY core/ ./core/
COPY netcommon/ ./netcommon/
COPY ws_gateway/ ./ws_gateway/

CMD ["python", "-m", "ws_gateway.main"]
