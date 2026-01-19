# Projeto30

Uma RAG econômica para empresas que não querem gastar muito com a API da OpenAI.

Utiliza um banco de dados Redis para salvar perguntas recorrentes e diminuir o uso da API.

Para rodar:

crie o .env

OPENAI_API_KEY=sk...

REDIS_HOST=redis

docker-compose up

curl -X POST http://localhost:5000/ask \
     -H "Content-Type: application/json" \
     -d '{"input_text": "Quais as vantagens do ZenML?"}'

<br><br>

![Diagrama da RAG](https://github.com/rodfloripa/Projeto30/blob/main/img.png)
<p align="center">
  Fig1. RAG
</p>
