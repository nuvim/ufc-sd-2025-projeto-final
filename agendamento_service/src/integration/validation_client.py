import socket
import json
from src.config import Config

class ValidationClient:

    def validate_payment(self, tipo_pagamento, dados_pagamento):
        payload = {
            "tipo_pagamento": tipo_pagamento,
            "dados_pagamento": dados_pagamento
        }

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((Config.VALIDATION_HOST, Config.VALIDATION_PORT))

                client.sendall(json.dumps(payload).encode())
                response = client.recv(Config.BUFFER_SIZE)

            data = json.loads(response.decode())
            if "erro" in data:
                raise Exception(data["erro"])

            return data["status"]

        except Exception as e:
            raise
