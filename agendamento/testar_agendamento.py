import requests
import json
import time

BASE_URL = "http://localhost:5000"

def imprimir_resposta(passo, response):
    print(f"\n--- {passo} ---")
    print(f"Status Code: {response.status_code}")
    try:
        print("Resposta:", json.dumps(response.json(), indent=4))
    except:
        print("Resposta (texto):", response.text)

# agendamento com sucesso
url_agendar = f"{BASE_URL}/agendar"
payload_1 = {
    "medico_id": 1,
    "paciente_id": 556217, # Seu ID
    "data_hora": "2026-02-10 09:00",
    "especialidade": "Cardiologia"
}
resp = requests.post(url_agendar, json=payload_1)
imprimir_resposta("Teste 1: Agendar Consulta (funciona)", resp)


# TESTE 2: Teste de Conflito de Horário
# enviando os mesmos dados do anterior
# o pdf quer um mecanismo para evitar conflitos 
resp = requests.post(url_agendar, json=payload_1)
imprimir_resposta("Teste 2: Tentar Agendar no Mesmo Horário (não funciona)", resp)


# TESTE 3: Mesmo Médico, Outro Horário
payload_2 = {
    "medico_id": 1,
    "paciente_id": 999999, # Outro paciente
    "data_hora": "2026-02-10 10:00", # Uma hora depois
    "especialidade": "Cardiologia"
}
resp = requests.post(url_agendar, json=payload_2)
imprimir_resposta("Teste 3: Mesmo médico, outro horário (funciona)", resp)


# TESTE 4: Atualizar Status da Consulta
# confirmando a consulta do id 1
url_atualizar = f"{BASE_URL}/agendar/1"
payload_status = { "status": "confirmada" }

resp = requests.put(url_atualizar, json=payload_status)
imprimir_resposta("Teste 4: Atualiza Status para 'confirmada'", resp)


# TESTE 5: Listar Todas as Consultas
url_listar = f"{BASE_URL}/consultas"
resp = requests.get(url_listar)
imprimir_resposta("Teste 5: Listar o Banco de Dados Mockado", resp)