FROM python:3.9-slim

WORKDIR /app

# copia e instala dependências primeiro (aproveita cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia o código da interface
COPY app.py .

EXPOSE 5000

CMD ["python", "-u", "app.py"]