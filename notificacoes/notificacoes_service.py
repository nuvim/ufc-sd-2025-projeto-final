from flask import Flask, request, jsonify
import pika, json

RABBITMQ_HOST = "rabbitmq"
EXCHANGE = "notificacoes"

app = Flask(__name__)

def publicar(evento):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key="",
        body=json.dumps(evento)
    )
    connection.close()

@app.route("/enviar", methods=["POST"])
def enviar():
    evento = request.json
    publicar(evento)
    return jsonify({"status": "enviado"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
