# Avaliação Parcial 3 - Sistemas Distribuídos (2025.2)
## Sistema de Gerenciamento de Clínica Médica

Este projeto implementa um sistema distribuído para gerenciamento de consultas médicas, utilizando uma arquitetura de microsserviços containerizados. O sistema integra tecnologias como gRPC, XML-RPC, RabbitMQ e Sockets.

---

### Arquitetura do Sistema

O Lado Servidor é composto por quatro módulos principais:
1.  **Users Service (gRPC implementado na linguagem go):** Gerencia autenticação e perfis de usuários.
2.  **Agendamento Service (XML-RPC implementado na linguagem python):** Gerencia horários e consultas.
3.  **Validation Service (Sockets TCP implementado na linguagem python):** Valida pagamentos e convênios.
4.  **Notification Service (RabbitMQ implementado na linguagem python):** Envia atualizações de status.

---

### Como Rodar o Projeto

#### 1. Inicializar o Lado Servidor
Na raiz do projeto (onde está o arquivo `docker-compose.yml`), execute o comando abaixo. O Docker irá construir os serviços locais e **baixar automaticamente as imagens dos clientes** do Docker Hub.

```bash
docker compose up -d
```

#### 2. Executar os Clientes
Para interagir com o sistema utilizando os clientes de forma interativa, utilize os comandos abaixo:

**Cliente de Usuários (Autenticação e CRUD de usuários):**
```bash
docker exec -it clinica_users_client python client_users.py + <nome do comando> + <args>
```

**Cliente de Agendamento (Consultas e Notificações):**
```bash
docker exec -it clinica_agendamento_client python client_agendamento.py + <nome do comando> + <args>
```

Quanto aos comandos disponíveis, recomendamos consultar a planilha de scripts.

### Estrutura de Arquivos

```text
.
├── agendamento_service/   # Serviço de Agendamento
├── users_service/         # Serviço de Usuários
├── validacao_service/     # Serviço de Validação
├── clients/               # Código fonte dos Clientes
├── database/              # Scripts de inicialização do Banco
├── docker-compose.yml     # Orquestração dos containers
├── .gitignore             # Especifica arquivos e pastas a serem ignorados pelo Git.
└── README.md              # Este arquivo
```

Observações: 
* A pasta clients/ está incluída apenas para consulta do código fonte. O docker-compose.yml está configurado para baixar e utilizar as imagens clientes hospedadas no Docker Hub.
* O serviço de notificações está contido dentro de agendamento_service/src/rabbitmq (Publicador) e clients/agendamento_client/src/rabbitmq (Consumidor)
