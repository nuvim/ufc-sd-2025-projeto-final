CREATE TYPE usuario_tipo AS ENUM ('ADMINISTRADOR', 'MEDICO', 'RECEPCIONISTA', 'PACIENTE');
CREATE TYPE especialidade_tipo AS ENUM ('CARDIOLOGIA', 'PEDIATRIA', 'ORTOPEDIA', 'DERMATOLOGIA');
CREATE TYPE pagamento_tipo AS ENUM ('CONVENIO', 'PARTICULAR');
CREATE TYPE status_agendamento AS ENUM ('PENDENTE', 'CONFIRMADA', 'REJEITADA', 'CONCLUIDA', 'CANCELADA');

CREATE TABLE usuario (
  id BIGSERIAL PRIMARY KEY,
  nome VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  senha VARCHAR(255) NOT NULL,
  tipo usuario_tipo NOT NULL
);

CREATE TABLE agendamento (
  id BIGSERIAL PRIMARY KEY,
  especialidade especialidade_tipo NOT NULL,
  data DATE NOT NULL,
  horario INT NOT NULL,
  tipo_pagamento pagamento_tipo NOT NULL,
  status status_agendamento NOT NULL DEFAULT 'PENDENTE',
  
  paciente_id BIGINT NOT NULL,
  medico_id BIGINT NOT NULL,
  
  CONSTRAINT fk_agendamento_paciente FOREIGN KEY(paciente_id) REFERENCES usuario(id) ON DELETE CASCADE,
  CONSTRAINT fk_agendamento_medico FOREIGN KEY(medico_id) REFERENCES usuario(id) ON DELETE CASCADE,
  
  CONSTRAINT uk_horario_medico UNIQUE (medico_id, data, horario), -- Evita dois agendamentos no mesmo horário com o mesmo médico no mesmo dia.
  CONSTRAINT uk_horario_paciente UNIQUE (paciente_id, data, horario), -- Evita dois agendamentos no mesmo horário com o mesmo paciente no mesmo dia.
  CONSTRAINT chk_horario_valido CHECK (horario >= 6 AND horario <= 16) -- Horário de funcionamento das 6:00 às 17:00.
);

-- Usuários para teste inicial.
INSERT INTO usuario (nome, email, senha, tipo) VALUES 
('Gusttavo', 'gusttavo@email.com', '123', 'ADMINISTRADOR'),  -- Sistema sempre deve iniciar com uma conta ADM
('Josué', 'josue@email.com', '123', 'MEDICO'),
('Vitor', 'vitor@email.com', '123', 'RECEPCIONISTA'),
('Kauê', 'kaue@email.com', '123', 'PACIENTE');