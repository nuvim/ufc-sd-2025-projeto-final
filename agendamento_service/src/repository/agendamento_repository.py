import psycopg2
from src.database.connection import get_connection

class AgendamentoError(Exception):
    pass

class AgendamentoRepository:
    def create(self, paciente_id, medico_id, data, horario, especialidade, tipo_pagamento):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                INSERT INTO agendamento (paciente_id, medico_id, data, horario, especialidade, tipo_pagamento)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """
            cursor.execute(query, (paciente_id, medico_id, data, horario, especialidade, tipo_pagamento))
            novo_id = cursor.fetchone()[0]
            conn.commit()
            return novo_id

        except psycopg2.IntegrityError as e:
            conn.rollback()
            erro_str = str(e)
            
            if "uk_horario_medico" in erro_str:
                raise AgendamentoError("Médico indisponível neste horário.")
            if "uk_horario_paciente" in erro_str:
                raise AgendamentoError("Paciente já possui um agendamento neste horário.")
            
            raise AgendamentoError("Dados inválidos (verifique se paciente/médico existem).")
            
        except Exception as e:
            conn.rollback()
            raise e 
        
        finally:
            cursor.close()
            conn.close()

    def get_by_id(self, agendamento_id):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT id, paciente_id, medico_id, data, horario, status
                FROM agendamento
                WHERE id = %s
            """
            cursor.execute(query, (agendamento_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "id": row[0],
                "paciente_id": row[1],
                "medico_id": row[2],
                "data": str(row[3]),
                "horario": row[4],
                "status": row[5]
            }

        finally:
            cursor.close()
            conn.close()


    def list_all(self, status=None):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            if status:
                query = """
                    SELECT id, paciente_id, medico_id, data, horario,
                           especialidade, tipo_pagamento, status
                    FROM agendamento
                    WHERE status = %s
                    ORDER BY data, horario
                """
                cursor.execute(query, (status,))
            else:
                query = """
                    SELECT id, paciente_id, medico_id, data, horario,
                           especialidade, tipo_pagamento, status
                    FROM agendamento
                    ORDER BY data, horario
                """
                cursor.execute(query)

            rows = cursor.fetchall()

            return [self._row_to_dict(row) for row in rows]

        finally:
            cursor.close()
            conn.close()

    def list_by_paciente(self, paciente_id, status=None):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            if status:
                query = """
                    SELECT id, paciente_id, medico_id, data, horario,
                           especialidade, tipo_pagamento, status
                    FROM agendamento
                    WHERE paciente_id = %s AND status = %s
                    ORDER BY data, horario
                """
                cursor.execute(query, (paciente_id, status))
            else:
                query = """
                    SELECT id, paciente_id, medico_id, data, horario,
                           especialidade, tipo_pagamento, status
                    FROM agendamento
                    WHERE paciente_id = %s
                    ORDER BY data, horario
                """
                cursor.execute(query, (paciente_id,))

            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

        finally:
            cursor.close()
            conn.close()

    def list_by_medico(self, medico_id, status=None):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            if status:
                query = """
                    SELECT id, paciente_id, medico_id, data, horario,
                           especialidade, tipo_pagamento, status
                    FROM agendamento
                    WHERE medico_id = %s AND status = %s
                    ORDER BY data, horario
                """
                cursor.execute(query, (medico_id, status))
            else:
                query = """
                    SELECT id, paciente_id, medico_id, data, horario,
                           especialidade, tipo_pagamento, status
                    FROM agendamento
                    WHERE medico_id = %s
                    ORDER BY data, horario
                """
                cursor.execute(query, (medico_id,))

            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

        finally:
            cursor.close()
            conn.close()

    def _row_to_dict(self, row):
        return {
            "id": row[0],
            "paciente_id": row[1],
            "medico_id": row[2],
            "data": str(row[3]),
            "horario": row[4],
            "especialidade": row[5],
            "tipo_pagamento": row[6],
            "status": row[7]
        }

    def update_status(self, agendamento_id, status):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            query = """
                UPDATE agendamento
                SET status = %s
                WHERE id = %s
            """
            cursor.execute(query, (status, agendamento_id))

            if cursor.rowcount == 0:
                raise AgendamentoError("Agendamento não encontrado.")

            conn.commit()

        except psycopg2.Error:
            conn.rollback()
            raise AgendamentoError("Erro interno no servidor.")

        finally:
            cursor.close()
            conn.close()