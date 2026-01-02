import json
import pika
import time

RABBITMQ_HOST = "rabbitmq"
EXCHANGE = "notificacoes"

def callback(ch, method, properties, body):
    try:
        evento = json.loads(body)
        tipo = evento.get("evento", "DESCONHECIDO")
        agendamento = evento.get("agendamento_id", "N/A")

        if tipo == "AGENDAMENTO_CRIADO":
            print(f"🕒 Agendamento {agendamento} criado e aguardando validação")

        elif tipo == "AGENDAMENTO_VALIDADO":
            print(f"✅ Agendamento {agendamento} foi VALIDADO")

        elif tipo == "AGENDAMENTO_INVALIDO":
            print(f"❌ Agendamento {agendamento} foi INVALIDADO")
            print(f"Motivo: {evento.get('motivo', 'não informado')}")

        elif tipo == "AGENDAMENTO_CANCELADO":
            print(f"⚠️ Agendamento {agendamento} foi CANCELADO")

        else:
            print(f"🔔 Evento desconhecido recebido: {evento}")

    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")

def conectar():
    while True:
        try:
            print("🔌 Cliente conectando ao RabbitMQ...")
            return pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    heartbeat=30
                )
            )
        except pika.exceptions.AMQPConnectionError:
            print("⏳ Cliente aguardando RabbitMQ...")
            time.sleep(3)

def main():
    print("🚀 Iniciando cliente de notificações...")
    connection = conectar()
    print("✅ Cliente conectado ao RabbitMQ")
    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="fanout"
    )

    queue = channel.queue_declare(queue="", exclusive=True)
    channel.queue_bind(exchange=EXCHANGE, queue=queue.method.queue)

    print("📡 Cliente aguardando notificações...")
    channel.basic_consume(
        queue=queue.method.queue,
        on_message_callback=callback,
        auto_ack=True
    )

    channel.start_consuming()

if __name__ == "__main__":
    main()
