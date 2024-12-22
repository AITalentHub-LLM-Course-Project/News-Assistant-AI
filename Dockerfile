FROM python:3.9

ARG APP_DIR=/app
WORKDIR "$APP_DIR"
ENV PYTHONPATH "$APP_DIR"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["sh", "entrypoint.sh"]