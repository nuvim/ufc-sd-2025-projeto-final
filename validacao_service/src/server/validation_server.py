import socket
import json
import threading

from src.config import Config
from src.validation.payment_validator import PaymentValidator

class ValidationServer:

    def __init__(self):
        self.validator = PaymentValidator()
        
    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((Config.VALIDATION_HOST, Config.VALIDATION_PORT))
            server.listen()

            while True:
                conn, _ = server.accept()
                client_thread = threading.Thread(target=self.handle_connection, args=(conn,)) # Cria uma thread para cada conexão.
                client_thread.start()

    def handle_connection(self, conn):
        with conn:
            self.handle_request(conn)

    def handle_request(self, conn):
        try:
            data = conn.recv(Config.BUFFER_SIZE)
            if not data:
                return
            
            payload = json.loads(data.decode())

            tipo_pagamento = payload["tipo_pagamento"]
            dados_pagamento = payload["dados_pagamento"]

            status = self.validator.validate(
                tipo_pagamento,
                dados_pagamento
            )

            response = {"status": status}

        except Exception as e:
            response = {"erro": "erro interno no servidor"}

        conn.sendall(json.dumps(response).encode())