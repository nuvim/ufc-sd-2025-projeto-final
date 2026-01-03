# ETAPA 1: Builder (Onde compilamos)
# Usamos a imagem oficial do Go (versão Alpine é mais leve)
FROM golang:1.25-alpine AS builder

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de dependência primeiro
# Isso é um truque de cache: se você não mudou as libs, o Docker não baixa tudo de novo
COPY go.mod go.sum ./
RUN go mod download

# Copia todo o resto do código fonte
COPY . .

# Compila o executável
# CGO_ENABLED=0 garante que o binário seja 100% estático e rode em qualquer Linux
RUN CGO_ENABLED=0 GOOS=linux go build -o server cmd/server/main.go

# ---------------------------------------------------------

# ETAPA 2: Runner (A imagem final de produção)
# Usamos uma imagem Alpine vazia (~5MB) para ficar super leve
FROM alpine:latest

WORKDIR /root/

# Copia apenas o executável da etapa anterior
COPY --from=builder /app/server .

# Expõe a porta que definimos no código
EXPOSE 50051

# Comando para iniciar o servidor
CMD ["./server"]