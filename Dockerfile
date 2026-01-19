FROM python:3.10-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia os requisitos e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código e o PDF
COPY . .

# Porta do Flask
EXPOSE 5000

CMD ["python", "app.py"]
