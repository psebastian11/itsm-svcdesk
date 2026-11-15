FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip
COPY src/ ./src/
RUN groupadd --system --gid 10001 svcdesk \
    && useradd --system --uid 10001 --gid svcdesk --no-create-home svcdesk
USER svcdesk
EXPOSE 8080
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080"]
