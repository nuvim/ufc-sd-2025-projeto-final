from src.rabbitmq.connection import get_connection
from src.config import Config
from src.rabbitmq.notification import Notification

class NotificationConsumer:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.queue_name = f"notifications.user.{user_id}"

        self.connection = get_connection()
        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange=Config.NOTIFICATION_EXCHANGE,
            exchange_type="direct",
            durable=True
        )

        self.channel.queue_declare(
            queue=self.queue_name,
            durable=True
        )

        self.channel.queue_bind(
            exchange=Config.NOTIFICATION_EXCHANGE,
            queue=self.queue_name,
            routing_key=str(user_id)
        )

    def consume_all(self):
        mensagens = []

        while True:
            method, _, body = self.channel.basic_get(
                queue=self.queue_name,
                auto_ack=False
            )

            if method is None:
                break

            mensagens.append(Notification.from_json(body.decode()))
            self.channel.basic_ack(method.delivery_tag)

        self.close()
        return mensagens

    def close(self):
        if self.connection.is_open:
            self.connection.close()
