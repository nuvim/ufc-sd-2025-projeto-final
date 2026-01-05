from src.rabbitmq.connection import get_connection
from src.config import Config

def setup_notification_infra(user_id: int):
    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(
        exchange=Config.NOTIFICATION_EXCHANGE,
        exchange_type="direct",
        durable=True
    )

    queue_name = f"notifications.user.{user_id}"

    channel.queue_declare(
        queue=queue_name,
        durable=True
    )

    channel.queue_bind(
        exchange=Config.NOTIFICATION_EXCHANGE,
        queue=queue_name,
        routing_key=str(user_id)
    )

    connection.close()
