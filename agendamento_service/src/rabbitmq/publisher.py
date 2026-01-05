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
        self.channel.basic_publish(
            exchange=Config.NOTIFICATION_EXCHANGE,
            routing_key=str(notification.user_id),
            body=notification.to_json(),
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
