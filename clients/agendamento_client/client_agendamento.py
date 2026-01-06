import xmlrpc.client
import argparse
import os
import sys

sys.path.append(os.getcwd())

from utils.session_manager import load_session
from src.rabbitmq.consumer import NotificationConsumer

RPC_ADDRESS = os.getenv("RPC_ADDRESS")

def handle_rpc_error(e: xmlrpc.client.Fault):
    print(f"Erro XML-RPC [{e.faultCode}]: {e.faultString}")

def agendar(server, args):
    try:
        session = load_session()

        response = server.agendar_consulta(
            session,
            str(args.paciente_id),
            str(args.medico_id),
            args.data,
            int(args.horario),
            args.especialidade,
            args.tipo_pagamento,
            args.dados_pagamento
        )

        print(f"ID: {response['id']} | Status: {response['status']} | Mensagem: {response['mensagem']}")

    except xmlrpc.client.Fault as e:
        handle_rpc_error(e)
    except Exception as e:
        print(f"Erro: {e}")

def listar(server, args):
    try:
        session = load_session()

        agendamentos = server.consultar_agendamentos(session, args.status)

        if not agendamentos:
            print("Nenhum agendamento encontrado.")
            return

        for a in agendamentos:
            print(f"ID: {a['id']} | Data: {a['data']} {a['horario']}h | Status: {a['status']} | Médico: {a['medico_id']} | Paciente: {a['paciente_id']}")

    except xmlrpc.client.Fault as e:
        handle_rpc_error(e)
    except Exception as e:
        print(f"Erro: {e}")

def cancelar(server, args):
    try:
        session = load_session()

        response = server.cancelar_agendamento(session, str(args.agendamento_id))

        print(f"ID: {response['id']} | Status: {response['status']} | Mensagem: {response['mensagem']}")

    except xmlrpc.client.Fault as e:
        handle_rpc_error(e)
    except Exception as e:
        print(f"Erro: {e}")

def concluir(server, args):
    try:
        session = load_session()

        response = server.concluir_agendamento(session, str(args.agendamento_id))

        print(f"ID: {response['id']} | Status: {response['status']} | Mensagem: {response['mensagem']}")

    except xmlrpc.client.Fault as e:
        handle_rpc_error(e)
    except Exception as e:
        print(f"Erro: {e}")

def ouvir_notificacoes():
    session = load_session()

    consumer = NotificationConsumer(int(session))
    mensagens = consumer.consume_all()

    if not mensagens:
        print("Nenhuma notificação pendente.")
        return

    print("\nNotificações:\n")
    for n in mensagens:
        print(
            f"[{n.timestamp}] "
            f"Agendamento {n.agendamento_id} → {n.novo_status}\n"
            f"{n.mensagem}\n"
        )

def main():
    parser = argparse.ArgumentParser(description="Cliente XML-RPC - Agendamento Service")
    subparsers = parser.add_subparsers(dest="command", required=True)

    agendar_parser = subparsers.add_parser("agendar")
    agendar_parser.add_argument("--paciente-id", type=int, required=True)
    agendar_parser.add_argument("--medico-id", type=int, required=True)
    agendar_parser.add_argument("--data", required=True, help="YYYY-MM-DD")
    agendar_parser.add_argument("--horario", type=int, required=True)
    agendar_parser.add_argument(
        "--especialidade", 
        required=True, 
        choices=['CARDIOLOGIA', 'PEDIATRIA', 'ORTOPEDIA', 'DERMATOLOGIA']
    )
    agendar_parser.add_argument(
        "--pagamento", 
        required=True, 
        dest='tipo_pagamento',
        choices=['CONVENIO', 'PARTICULAR']
    )
    agendar_parser.add_argument("--dados-pagamento", required=True)

    listar_parser = subparsers.add_parser("listar")
    listar_parser.add_argument(
        "--status", 
        required=False, 
        choices=['PENDENTE', 'CONFIRMADO', 'REJEITADO', 'CONCLUIDO', 'CANCELADO']
    )

    cancelar_parser = subparsers.add_parser("cancelar")
    cancelar_parser.add_argument("--id", type=int, required=True, dest="agendamento_id")

    concluir_parser = subparsers.add_parser("concluir")
    concluir_parser.add_argument("--id", type=int, required=True, dest="agendamento_id")

    subparsers.add_parser("ouvir-notificacoes")

    args = parser.parse_args()

    server = xmlrpc.client.ServerProxy(RPC_ADDRESS, allow_none=True)

    match args.command:
        case "agendar":
            agendar(server, args)
        case "listar":
            listar(server, args)
        case "cancelar":
            cancelar(server, args)
        case "concluir":
            concluir(server, args)
        case "ouvir-notificacoes":
            ouvir_notificacoes()

if __name__ == "__main__":
    main()