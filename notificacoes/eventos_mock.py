import json
import pika
import time

RABBITMQ_HOST = "rabbitmq"
EXCHANGE = "notificacoes"

eventos = [
    {
        "evento": "AGENDAMENTO_CRIADO",
        "agendamento_id": 1,
        "paciente_id": 10,
        "medico_id": 3,
        "data": "2025-12-26",
        "horario": 14,
        "status": "AGUARDANDO",
        "tipo_pagamento": "CONVENIO"
    },
    {
        "evento": "AGENDAMENTO_VALIDADO",
        "agendamento_id": 1,
        "status": "VALIDO"
    },
    {
        "evento": "AGENDAMENTO_CANCELADO",
        "agendamento_id": 1,
        "status": "CANCELADO"
    }
]

def conectar():
    while True:
        try:
            print("🔌 Conectando ao RabbitMQ...")
            return pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    heartbeat=30
                )
            )
        except pika.exceptions.AMQPConnectionError:
            print("⏳ Mock aguardando RabbitMQ...")
            time.sleep(3)

def main():
    connection = conectar()
    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="fanout"
    )

    for evento in eventos:
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key="",
            body=json.dumps(evento)
        )
        print(f"🧪 [Agendamento] Evento publicado: {evento['evento']}")
        time.sleep(2)

    print("✅ Mock de Agendamento finalizado")
    connection.close()

if __name__ == "__main__":
    main()
