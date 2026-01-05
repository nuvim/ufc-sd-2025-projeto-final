import xmlrpc.client
from datetime import datetime, time

from src.integration.users_client import UsersClient
from src.integration.validation_client import ValidationClient

from src.repository.agendamento_repository import AgendamentoRepository, AgendamentoError
from src.utils.validators import validar_enum

class AgendamentoService:
    def __init__(self):
        self.agendamento_repository = AgendamentoRepository()
        self.users_client = UsersClient()
        self.validation_client = ValidationClient()

        self.ESPECIALIDADES = {'CARDIOLOGIA', 'PEDIATRIA', 'ORTOPEDIA', 'DERMATOLOGIA'}
        self.PAGAMENTOS = {'CONVENIO', 'PARTICULAR'}
        self.STATUS = {'PENDENTE', 'CONFIRMADO', 'REJEITADO', 'CONCLUIDO', 'CANCELADO'}

    def agendar_consulta(self, token, paciente_id, medico_id, data, horario, especialidade, tipo_pagamento, dados_pagamento):
        if not all([token, paciente_id, medico_id, data, horario, especialidade, tipo_pagamento, dados_pagamento]):
             raise xmlrpc.client.Fault(1, "Todos os campos são obrigatórios.")

        try:
            if not (6 <= horario <= 16):
                raise xmlrpc.client.Fault(1, "Horário inválido. A clínica funciona das 06:00 às 17:00.")
            
            data_hora_agendada = self._data_hora_agendamento(data, horario)

            if datetime.now() > data_hora_agendada:
                raise xmlrpc.client.Fault(1, "Não é possível agendar consultas para datas passadas.")
            
            validar_enum(especialidade, self.ESPECIALIDADES, "Especialidade")
            validar_enum(tipo_pagamento, self.PAGAMENTOS, "Tipo de Pagamento")

            # Consulta role do requisitante (token == requisitante_id).
            requester_role = self.users_client.get_user_role(token, token)

            if requester_role == "PACIENTE":
                if int(token) != int(paciente_id):
                    raise xmlrpc.client.Fault(1, "Paciente só pode agendar consultas para si mesmo.")
            
            elif requester_role == "RECEPCIONISTA":
                pass
            
            else:
                raise xmlrpc.client.Fault(1, "Apenas Pacientes e Recepcionistas podem criar agendamentos.")

            paciente_role = self.users_client.get_user_role(token, paciente_id)
            if paciente_role != "PACIENTE":
                raise xmlrpc.client.Fault(1, f"O ID informado ({paciente_id}) não pertence a um Paciente.")

            medico_role = self.users_client.get_user_role(token, medico_id)
            if medico_role != "MEDICO":
                raise xmlrpc.client.Fault(1, f"O ID informado ({medico_id}) não pertence a um Médico.")


            agendamento_id = self.agendamento_repository.create(paciente_id, medico_id, data, horario, especialidade, tipo_pagamento)

            status_validacao = self.validation_client.validate_payment(
                tipo_pagamento,
                dados_pagamento
            )

            validar_enum(status_validacao, self.STATUS, "Status")

            self.agendamento_repository.update_status(agendamento_id, status_validacao)
            
            return {
                "id": agendamento_id,
                "status": status_validacao,
                "mensagem": (
                    "Agendamento confirmado."
                    if status_validacao == "CONFIRMADO"
                    else "Agendamento rejeitado."
                )
            }

        except AgendamentoError as e:
            raise xmlrpc.client.Fault(1, str(e))
            
        except Exception as e:
            msg = str(e)
            if "interno" in msg.lower():
                 raise xmlrpc.client.Fault(2, msg)
            else:
                 raise xmlrpc.client.Fault(1, msg)
            
    def consultar_agendamentos(self, token, status=None):
        if not token:
            raise xmlrpc.client.Fault(1, "Token é obrigatório.")

        try:
            if status:
                validar_enum(status, self.STATUS, "Status")

            requester_role = self.users_client.get_user_role(token, token)

            if requester_role == "PACIENTE":
                return self.agendamento_repository.list_by_paciente(paciente_id=token, status=status)

            if requester_role == "MEDICO":
                return self.agendamento_repository.list_by_medico(medico_id=token, status=status)

            if requester_role in {"RECEPCIONISTA", "ADMINISTRADOR"}:
                return self.agendamento_repository.list_all(status=status)

            raise xmlrpc.client.Fault(1, "permissão negada para consultar agendamentos.")
        
        except AgendamentoError as e:
            raise xmlrpc.client.Fault(1, str(e))

        except Exception as e:
            msg = str(e)
            if "interno" in msg.lower():
                raise xmlrpc.client.Fault(2, msg)
            else:
                raise xmlrpc.client.Fault(1, msg)
    
    def cancelar_agendamento(self, token, agendamento_id):
        if not token:
            raise xmlrpc.client.Fault(1, "Token é obrigatório.")
        
        if not agendamento_id:
            raise xmlrpc.client.Fault(1, "O id do agendamento é obrigatório.")

        try:
            requester_role = self.users_client.get_user_role(token, token)

            agendamento = self.agendamento_repository.get_by_id(agendamento_id)
            if not agendamento:
                raise xmlrpc.client.Fault(1, "Agendamento não encontrado.")

            if agendamento["status"] != "CONFIRMADO":
                raise xmlrpc.client.Fault(1, "Apenas agendamentos com status CONFIRMADO podem ser cancelados.")

            if requester_role == "PACIENTE":
                if int(token) != agendamento["paciente_id"]:
                    raise xmlrpc.client.Fault(1, "Paciente só pode cancelar seus próprios agendamentos.")

            elif requester_role == "RECEPCIONISTA":
                pass

            else:
                raise xmlrpc.client.Fault(1, "Permissão negada para cancelar agendamentos.")

            self.agendamento_repository.update_status(agendamento_id, "CANCELADO")

            return {
                "id": agendamento_id,
                "status": "CANCELADO",
                "mensagem": "Agendamento cancelado com sucesso."
            }

        except AgendamentoError as e:
            raise xmlrpc.client.Fault(1, str(e))

        except Exception as e:
            msg = str(e)
            if "interno" in msg.lower():
                raise xmlrpc.client.Fault(2, msg)
            else:
                raise xmlrpc.client.Fault(1, msg)

    def concluir_agendamento(self, token, agendamento_id):
        if not token:
            raise xmlrpc.client.Fault(1, "Token é obrigatório.")

        if not agendamento_id:
            raise xmlrpc.client.Fault(1, "O id do agendamento é obrigatório.")

        try:
            requester_role = self.users_client.get_user_role(token, token)

            if requester_role != "MEDICO":
                raise xmlrpc.client.Fault(1, "Apenas médicos podem concluir agendamentos.")

            agendamento = self.agendamento_repository.get_by_id(agendamento_id)
            if not agendamento:
                raise xmlrpc.client.Fault(1, "Agendamento não encontrado.")

            if agendamento["status"] != "CONFIRMADO":
                raise xmlrpc.client.Fault(1, "Apenas agendamentos com status CONFIRMADO podem ser concluídos.")

            if int(token) != agendamento["medico_id"]:
                raise xmlrpc.client.Fault(1, "Médico só pode concluir agendamentos sob sua responsabilidade.")

            # Evita médico concluir uma consulta que ainda não aconteceu.
            data_hora_agendada = self._data_hora_agendamento(agendamento["data"], agendamento["horario"])

            if datetime.now() < data_hora_agendada:
                raise xmlrpc.client.Fault(1, "Não é possível concluir um agendamento antes do horário marcado.")

            self.agendamento_repository.update_status(agendamento_id, "CONCLUIDO")

            return {
                "id": agendamento_id,
                "status": "CONCLUIDO",
                "mensagem": "Agendamento concluído com sucesso."
            }
        
        except AgendamentoError as e:
            raise xmlrpc.client.Fault(1, str(e))

        except Exception as e:
            msg = str(e)
            if "interno" in msg.lower():
                raise xmlrpc.client.Fault(2, msg)
            else:
                raise xmlrpc.client.Fault(1, msg)
            
    # Função helper.
    def _data_hora_agendamento(self, data, horario):
        return datetime.combine(
            datetime.fromisoformat(data).date(),
            time(hour=horario)
        )
