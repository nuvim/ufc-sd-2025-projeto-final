import pika
import json
import os

class NotificationConsumer:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.queue_name = f"notifications.user.{user_id}"
        
        # Configurações de conexão
        # Se estiver rodando via 'docker exec', o host é 'rabbitmq'
        # Se for rodar localmente fora do docker, seria 'localhost'
        self.host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        self.credentials = pika.PlainCredentials("guest", "guest")

    def _get_channel(self):
        """Abre conexão e canal de forma segura."""
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host, port=5672, credentials=self.credentials)
        )
        channel = connection.channel()
        return connection, channel

    def consume_all(self):
        mensagens = []
        connection, channel = self._get_channel()

        try:
            channel.exchange_declare(
                exchange="notifications", 
                exchange_type="direct", 
                durable=True
            )
            
            channel.queue_declare(
                queue=self.queue_name, 
                durable=True
            )
            
            channel.queue_bind(
                exchange="notifications", 
                queue=self.queue_name, 
                routing_key=str(self.user_id)
            )

            # 2. Loop de Consumo (Polling)
            print(f"📭 Checando caixa de entrada: {self.queue_name}...", flush=True)
            
            while True:
                # basic_get NÃO bloqueia. Se tiver msg, pega. Se não, retorna None.
                method_frame, header_frame, body = channel.basic_get(
                    queue=self.queue_name, 
                    auto_ack=False
                )

                if method_frame is None:
                    break  # Fila vazia, terminamos.

                # Processa a mensagem
                payload = json.loads(body.decode())
                mensagens.append(payload)

                # Confirma o recebimento (remove da fila)
                channel.basic_ack(method_frame.delivery_tag)

        except Exception as e:
            print(f"❌ Erro ao conectar no RabbitMQ: {e}")
            mensagens = [] # Retorna vazio em caso de erro de conexão
        
        finally:
            if connection and connection.is_open:
                connection.close()
        
        return mensagens