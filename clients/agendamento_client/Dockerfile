FROM python:3.10-slim

WORKDIR /app

COPY agendamento_client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agendamento_client/ .

COPY utils/ ./utils
RUN touch utils/__init__.py

RUN touch src/__init__.py
RUN mkdir -p src/rabbitmq && touch src/rabbitmq/__init__.py

CMD ["tail", "-f", "/dev/null"]