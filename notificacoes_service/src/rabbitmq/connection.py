import pika

from src.config import Config

def get_connection():
    credentials = pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASSWORD)

    parameters = pika.ConnectionParameters(
        host=Config.RABBITMQ_HOST,
        port=Config.RABBITMQ_PORT,
        credentials=credentials
    )

    return pika.BlockingConnection(parameters)
