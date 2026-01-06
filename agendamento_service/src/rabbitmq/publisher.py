import pika
from src.config import Config
from src.rabbitmq.connection import get_connection
from src.rabbitmq.notification import Notification

class NotificationPublisher:
    def __init__(self):
        self.connection = get_connection()
        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange=Config.NOTIFICATION_EXCHANGE,
            exchange_type="direct",
            durable=True
        )

    def publish(self, notification: Notification):
        try:
            user_queue_name = f"notifications.user.{notification.user_id}"

            self.channel.queue_declare(
                queue=user_queue_name,
                durable=True
            )

            self.channel.queue_bind(
                exchange=Config.NOTIFICATION_EXCHANGE,
                queue=user_queue_name,
                routing_key=str(notification.user_id)
            )

            self.channel.basic_publish(
                exchange=Config.NOTIFICATION_EXCHANGE,
                routing_key=str(notification.user_id),
                body=notification.to_json(),
                properties=pika.BasicProperties(delivery_mode=2) # Mensagens persistente.
            )

        except Exception:
            raise Exception("Erro interno ao publicar notificação.")

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
