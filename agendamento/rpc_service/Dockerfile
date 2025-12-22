# usando uma imagem leve do Python, talvez tenha que trocar
FROM python:3.9-slim

# define a pasta de trabalho dentro do container
WORKDIR /app

# copia o código para dentro do container
COPY server.py .

# expondo a porta que vai rodar
EXPOSE 8000

# comando pra rodar o servidor, garante que o print apareça no log (python -u)
CMD ["python", "-u", "server.py"]