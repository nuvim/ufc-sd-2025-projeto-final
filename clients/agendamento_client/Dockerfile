FROM python:3.10-slim

WORKDIR /app

COPY agendamento_client/ .

COPY utils/ ./utils

RUN touch utils/__init__.py

CMD ["tail", "-f", "/dev/null"]