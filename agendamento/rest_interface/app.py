from flask import Flask, request, jsonify
import xmlrpc.client
import os

app = Flask(__name__)

# conecta ao servidor RPC. 
# rpc-service é o nome definido no docker-compose
rpc_host = os.getenv('RPC_HOST', 'rpc-service')
rpc_url = f"http://{rpc_host}:8000/RPC2"

print(f"Conectando ao serviço RPC em: {rpc_url}")
rpc_proxy = xmlrpc.client.ServerProxy(rpc_url)

@app.route('/agendar', methods=['POST'])
def agendar():
    dados = request.json
    if not dados:
        return jsonify({"erro": "JSON invalido"}), 400

    # extraindo os dados, incluindo a especialidade que foi pedido no pdf
    medico_id = dados.get('medico_id')
    paciente_id = dados.get('paciente_id')
    data_hora = dados.get('data_hora')
    especialidade = dados.get('especialidade')

    # validação simples antes de enviar
    if not all([medico_id, paciente_id, data_hora, especialidade]):
         return jsonify({"erro": "Faltam dados (medico_id, paciente_id, data_hora, especialidade)"}), 400

    try:
        # chama a função no server.py
        print(f"[REST] Enviando para RPC: Medico {medico_id}, Data {data_hora}")
        resposta = rpc_proxy.agendar_consulta(medico_id, paciente_id, data_hora, especialidade)
        return jsonify(resposta), 200
    except Exception as e:
        return jsonify({"erro": f"Falha na comunicacao com RPC: {str(e)}"}), 500

@app.route('/consultas', methods=['GET'])
def listar():
    try:
        # chama a função de listar do server.py
        resposta = rpc_proxy.listar_consultas()
        return jsonify(resposta), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/agendar/<int:id_consulta>', methods=['PUT'])
def atualizar_consulta(id_consulta):
    dados = request.json
    novo_status = dados.get('status')
    
    if not novo_status:
        return jsonify({"erro": "Faltou enviar o novo status"}), 400

    try:
        # chama a função nova de atualizar no rpc
        resposta = rpc_proxy.atualizar_status(id_consulta, novo_status)
        return jsonify(resposta), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)