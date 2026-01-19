# Projeto30

Uma RAG econômica para empresas que não querem gastar muito com a API da OpenAI

Utiliza um banco de dados para salvar perguntas recorrentes.

Para rodar:

docker-compose up

curl -X POST http://localhost:5000/ask \
     -H "Content-Type: application/json" \
     -d '{"input_text": "Quais as vantagens do ZenML?"}'

![Diagrama da RAG](URL_da_imagem)
