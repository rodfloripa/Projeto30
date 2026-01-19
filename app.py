import os
import glob
import hashlib
import redis
from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer, util
from openai import OpenAI
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()


app = Flask(__name__)
app.json.ensure_ascii = False  # <--- ADICIONE ESTA LINHA

# --- 1. CONFIGURAÇÕES ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

client = OpenAI(api_key=OPENAI_API_KEY)
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0)

# Modelo local para busca (Retrieval) - Gratuito e rápido
print("Carregando modelo de busca local...")
embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

document_chunks = []
embeddings_cache = None

# --- 2. PROCESSAMENTO DOS PDFS ---
def process_pdfs_automatically():
    global document_chunks, embeddings_cache
    pdf_files = glob.glob("*.pdf")
    
    if not pdf_files:
        print("⚠️ AVISO: Coloque arquivos .pdf na pasta.")
        return

    all_text = ""
    for pdf_path in pdf_files:
        print(f"📖 Processando: {pdf_path}")
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                text = page.extract_text()
                if text: all_text += text + "\n"
        except Exception as e:
            print(f"❌ Erro em {pdf_path}: {e}")

    if all_text:
        # GPT aguenta contextos maiores, então usamos pedaços de 1000 caracteres
        size = 1000
        step = 800 
        document_chunks = [all_text[i:i+size] for i in range(0, len(all_text), step)]
        embeddings_cache = embedder.encode(document_chunks, convert_to_tensor=True)
        print(f"✅ Conhecimento indexado com sucesso.")

# --- 3. ROTAS ---

@app.route('/')
def home():
    if os.path.exists("index.html"):
        return open("index.html", "r", encoding="utf-8").read()
    return "API RAG OpenAI Online."

@app.route('/ask', methods=['POST'])
def ask():
    user_query = request.json.get('input_text', '').strip()
    
    if not user_query or not document_chunks:
        return jsonify({'error': 'Sistema não inicializado ou pergunta vazia.'}), 400

    # A. CACHE NO REDIS
    query_hash = hashlib.md5(user_query.lower().encode()).hexdigest()
    cache_key = f"rag_openai_v3:{query_hash}"
    cached_res = redis_client.get(cache_key)
    
    if cached_res:
        print("🚀 Resposta servida pelo Cache")
        return jsonify({'resposta': cached_res.decode('utf-8'), 'origem': 'cache_redis'})

    # B. BUSCA SEMÂNTICA LOCAL (Retrieval)
    query_embedding = embedder.encode(user_query, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, embeddings_cache, top_k=3)
    context_text = " ".join([document_chunks[hit['corpus_id']] for hit in hits[0]])

    # C. GERAÇÃO COM OPENAI (GPT-4o-mini)
    print("🧠 Consultando OpenAI...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um especialista que responde perguntas com base no contexto de PDFs fornecido. Responda de forma clara, técnica e em Português do Brasil."},
                {"role": "user", "content": f"CONTEXTO:\n{context_text}\n\nPERGUNTA:\n{user_query}"}
            ],
            temperature=0.2 # Mais baixo para ser mais fiel ao texto
        )
        answer = response.choices[0].message.content
    except Exception as e:
        return jsonify({'error': f"Erro OpenAI: {str(e)}"}), 500

    # D. SALVAR NO CACHE
    redis_client.setex(cache_key, 86400, answer)

    return jsonify({
        'resposta': answer,
        'origem': 'openai_api'
    })

if __name__ == '__main__':
    process_pdfs_automatically()
    app.run(host='0.0.0.0', port=5000)
