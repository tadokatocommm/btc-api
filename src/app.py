import os
import time
import requests
import logging
import logfire
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from logging import basicConfig, getLogger
from flask import Flask
from threading import Thread

# ------------------------------------------------------
# Configuração Logfire
logfire.configure()
basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = getLogger(__name__)
logger.setLevel(logging.INFO)
logfire.instrument_requests()

# ------------------------------------------------------
# Importar Base e BitcoinPreco do database.py
from database import Base, BitcoinPreco

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Lê as variáveis separadas do arquivo .env
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Monta a URL de conexão ao banco PostgreSQL (sem SSL)
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Cria o engine e a sessão
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Configuração do Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Aplicação rodando na porta correta!"

def criar_tabela():
    """Cria a tabela no banco de dados, se não existir."""
    Base.metadata.create_all(engine)
    logger.info("Tabela criada/verificada com sucesso!")

def extrair_dados_bitcoin():
    """Extrai o JSON completo da API da Coinbase."""
    url = 'https://api.coinbase.com/v2/prices/spot'
    resposta = requests.get(url)
    if resposta.status_code == 200:
        return resposta.json()
    else:
        logger.error(f"Erro na API: {resposta.status_code}")
        return None

def tratar_dados_bitcoin(dados_json):
    """Transforma os dados brutos da API e adiciona timestamp."""
    valor = float(dados_json['data']['amount'])
    criptomoeda = dados_json['data']['base']
    moeda = dados_json['data']['currency']
    timestamp = datetime.now()
    
    dados_tratados = {
        "valor": valor,
        "criptomoeda": criptomoeda,
        "moeda": moeda,
        "timestamp": timestamp
    }
    return dados_tratados

def salvar_dados_postgres(dados):
    """Salva os dados no banco PostgreSQL."""
    session = Session()
    try:
        novo_registro = BitcoinPreco(**dados)
        session.add(novo_registro)
        session.commit()
        logger.info(f"[{dados['timestamp']}] Dados salvos no PostgreSQL!")
    except Exception as ex:
        logger.error(f"Erro ao inserir dados no PostgreSQL: {ex}")
        session.rollback()
    finally:
        session.close()

def pipeline_bitcoin():
    """Executa a pipeline de ETL do Bitcoin com spans do Logfire."""
    while True:
        try:
            with logfire.span("Executando pipeline ETL Bitcoin"):
                
                with logfire.span("Extrair Dados da API Coinbase"):
                    dados_json = extrair_dados_bitcoin()
                
                if not dados_json:
                    logger.error("Falha na extração dos dados. Abortando pipeline.")
                    time.sleep(15)
                    continue
                
                with logfire.span("Tratar Dados do Bitcoin"):
                    dados_tratados = tratar_dados_bitcoin(dados_json)
                
                with logfire.span("Salvar Dados no Postgres"):
                    salvar_dados_postgres(dados_tratados)

                logger.info("Pipeline finalizada com sucesso!")
            time.sleep(15)
        except Exception as e:
            logger.error(f"Erro inesperado durante a pipeline: {e}")
            time.sleep(15)

if __name__ == "__main__":
    criar_tabela()
    logger.info("Iniciando aplicação...")

    # Cria uma thread para rodar a pipeline em paralelo
    thread_etl = Thread(target=pipeline_bitcoin)
    thread_etl.daemon = True
    thread_etl.start()

    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
