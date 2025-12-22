from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# MOCK DO BANCO DE DADOS
agendamentos_mock = []
ultimo_id = 0  # contador pra gerar os ids

def verificar_disponibilidade(medico_id, data_hora):
    for agendamento in agendamentos_mock:
        # verificando se é o mesmo medico, o mesmo horario e se a consulta nao esta cancelada
        if (agendamento['medico_id'] == medico_id and 
            agendamento['data_hora'] == data_hora and 
            agendamento['status'] != 'cancelada'):
            return False # se ta ocupado
    return True # se ta livre

def agendar_consulta(medico_id, paciente_id, data_hora, especialidade):
    global ultimo_id
    print(f"[RPC] Novo pedido: Medico {medico_id} ({especialidade}) as {data_hora}")
    
    # verificação de conflitos
    if not verificar_disponibilidade(medico_id, data_hora):
        return {"status": "erro", "mensagem": "Horario indisponivel para este medico."}
    
    # campos pedidos no pdf
    ultimo_id += 1
    novo_agendamento = {
        "id": ultimo_id,
        "medico_id": medico_id,
        "paciente_id": paciente_id,
        "data_hora": data_hora,
        "especialidade": especialidade,
        "status": "agendada" # status inicial padrão
    }
    agendamentos_mock.append(novo_agendamento)
    
    return {"status": "sucesso", "mensagem": "Consulta agendada!", "id_consulta": ultimo_id}

def listar_consultas():
    return agendamentos_mock

def atualizar_status(id_consulta, novo_status):
    print(f"[RPC] Atualizando consulta {id_consulta} para {novo_status}")
    
    # procura a consulta pelo id na lista
    for agendamento in agendamentos_mock:
        if agendamento['id'] == id_consulta:
            agendamento['status'] = novo_status
            return {"status": "sucesso", "mensagem": f"Status alterado para {novo_status}"}
    
    return {"status": "erro", "mensagem": "Consulta nao encontrada"}

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

with SimpleXMLRPCServer(('0.0.0.0', 8000), requestHandler=RequestHandler, allow_none=True) as server:
    server.register_introspection_functions()
    server.register_function(agendar_consulta, 'agendar_consulta')
    server.register_function(listar_consultas, 'listar_consultas')
    server.register_function(atualizar_status, 'atualizar_status')
    print("Serviço de Agendamento rodando com regras de negócio...")
    server.serve_forever()