# 📄 Contratos de Integração

Este documento define os **contratos oficiais de comunicação** entre os componentes do sistema distribuído de gerenciamento de consultas médicas. Ele serve como referência para todos os integrantes da equipe e garante integração consistente entre Cliente, Serviços e Mensageria.

---

## 1️⃣ Visão Geral

O sistema utiliza **dois modelos principais de comunicação**:

1. **Comunicação síncrona (REST)**
   Cliente → Interfaces dos Serviços

2. **Comunicação assíncrona (RabbitMQ – Publisher/Subscriber)**
   Serviço de Notificações → Cliente

Este documento cobre:

* Contrato de **eventos** (RabbitMQ)
* Convenções de **mensageria**
* Contrato **REST esperado pelo Cliente**

---

## 2️⃣ Contrato de Mensageria (RabbitMQ)

### 2.1 Broker

* **Broker**: RabbitMQ
* **Virtual Host**: `/`
* **Usuário**: `guest`
* **Senha**: `guest`

---

### 2.2 Exchange de Notificações

| Campo            | Valor          |
| ---------------- | -------------- |
| Nome da exchange | `notificacoes` |
| Tipo             | `fanout`       |
| Durável          | Não            |
| Auto-delete      | Não            |

📌 **Justificativa**: o tipo `fanout` permite que todos os clientes conectados recebam as mesmas notificações em tempo real.

---

### 2.3 Filas (Queues)

* As filas são **criadas dinamicamente pelos clientes**
* Tipo de fila: **temporária**
* Propriedades:

  * `exclusive = true`
  * Nome gerado automaticamente (`amq.gen-*`)

📌 Isso garante que cada cliente receba notificações apenas enquanto estiver conectado.

---

## 3️⃣ Formato Padrão das Mensagens

Todas as mensagens publicadas na exchange `notificacoes` devem seguir o formato JSON abaixo:

```json
{
  "evento": "CONSULTA_CONFIRMADA",
  "consulta_id": 123,
  "paciente_id": 45,
  "medico_id": 9,
  "status": "CONFIRMADA",
  "timestamp": "2025-12-22T19:40:00"
}
```

### 3.1 Campos obrigatórios

| Campo       | Tipo              | Descrição                 |
| ----------- | ----------------- | ------------------------- |
| evento      | string            | Tipo do evento ocorrido   |
| consulta_id | int               | Identificador da consulta |
| paciente_id | int               | Identificador do paciente |
| medico_id   | int               | Identificador do médico   |
| status      | string            | Status atual da consulta  |
| timestamp   | string (ISO-8601) | Data e hora do evento     |

---

## 4️⃣ Contrato de Mensagens (RabbitMQ)

### Exchange

* Nome: `notificacoes`
* Tipo: `fanout`
* Virtual Host: `/`

### Convenções Gerais

* Todas as mensagens são publicadas **pelo Serviço de Agendamento** após mudanças de estado.
* O Serviço de Notificações **não executa regras de negócio**; apenas publica eventos.
* O Cliente apenas consome mensagens.

### Eventos Padronizados

#### 4.1 AGENDAMENTO_CRIADO

Emitido quando um novo agendamento é criado.

```json
{
  "evento": "AGENDAMENTO_CRIADO",
  "agendamento_id": 42,
  "paciente_id": 10,
  "medico_id": 3,
  "data": "2025-12-26",
  "horario": 14,
  "status": "AGUARDANDO",
  "tipo_pagamento": "CONVENIO"
}
```

#### 4.2 AGENDAMENTO_VALIDADO

Emitido após validação positiva do convênio/pagamento.

```json
{
  "evento": "AGENDAMENTO_VALIDADO",
  "agendamento_id": 42,
  "paciente_id": 10,
  "medico_id": 3,
  "data": "2025-12-26",
  "horario": 14,
  "status": "VALIDO"
}
```

#### 4.3 AGENDAMENTO_INVALIDO

Emitido após validação negativa.

```json
{
  "evento": "AGENDAMENTO_INVALIDO",
  "agendamento_id": 42,
  "paciente_id": 10,
  "medico_id": 3,
  "data": "2025-12-26",
  "horario": 14,
  "status": "INVALIDO",
  "motivo": "CONVENIO_RECUSADO"
}
```

#### 4.4 AGENDAMENTO_CANCELADO

Emitido quando um agendamento é cancelado.

```json
{
  "evento": "AGENDAMENTO_CANCELADO",
  "agendamento_id": 42,
  "paciente_id": 10,
  "data": "2025-12-26",
  "horario": 14,
  "status": "CANCELADO"
}
```

---

## 5️⃣ Contrato REST – Visão do Cliente

⚠️ **Observação**: os endpoints abaixo representam o **contrato esperado** pelo Cliente. A implementação fica a cargo dos serviços responsáveis.

---

### 5.1 Serviço de Usuários

Base URL (exemplo):

```
http://usuarios:5000
```

| Método | Endpoint       | Descrição          |
| ------ | -------------- | ------------------ |
| POST   | /usuarios      | Criar novo usuário |
| POST   | /login         | Autenticação       |
| GET    | /usuarios/{id} | Consultar usuário  |

---

### 5.2 Serviço de Agendamento

Base URL (exemplo):

```
http://agendamento:5001
```

| Método | Endpoint                 | Descrição         |
| ------ | ------------------------ | ----------------- |
| POST   | /consultas               | Criar consulta    |
| GET    | /consultas/{id}          | Consultar status  |
| PUT    | /consultas/{id}/cancelar | Cancelar consulta |
| PUT    | /consultas/{id}/remarcar | Remarcar consulta |

📌 Alterações de status nesses endpoints **devem disparar eventos** no Serviço de Notificações.

---

## 6️⃣ Responsabilidades dos Componentes

### Serviço de Notificações

* Publicar eventos no RabbitMQ
* Não implementar regras de negócio
* Garantir que mensagens sigam o contrato

### Cliente

* Consumir eventos do RabbitMQ
* Exibir notificações em tempo real
* Consumir serviços via REST

---

## 7️⃣ Considerações Importantes

* RabbitMQ deve estar disponível antes do Serviço de Notificações
* Clientes devem implementar reconexão automática
* Logs devem indicar claramente eventos publicados e consumidos

---

## 8️⃣ Status do Documento

---

## 9️⃣ Próximo Passo de Implementação

Com este contrato definido, o próximo componente a ser implementado é o **Serviço de Notificações**, responsável por publicar eventos no RabbitMQ sempre que ocorrerem mudanças relevantes no sistema (ex: confirmação ou cancelamento de consultas).

O serviço deve:

* Conectar-se ao RabbitMQ com política de reconexão
* Publicar mensagens JSON conforme o contrato definido
* Não conter regras de negócio (apenas repassar eventos)

A implementação desse serviço está a cargo do **Integrante 5 – Cliente & Notificações** e deve seguir rigorosamente este documento.

* Versão: **1.0**
* Responsável: **Integrante 5 – Cliente & Notificações**
* Data: **Dezembro de 2025**

## Endpoint do Serviço de Notificações

POST /enviar
Body: Evento JSON conforme definido acima

Responsabilidade:
Receber eventos do Serviço de Agendamento e publicá-los no RabbitMQ.

