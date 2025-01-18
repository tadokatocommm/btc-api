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
    try:
        Base.metadata.create_all(engine)
        logger.info("Tabela criada/verificada com sucesso!")
    except Exception as ex:
        logger.error(f"Erro ao criar/verificar tabela: {ex}")

def extrair_dados_bitcoin():
    """Extrai o JSON completo da API da Coinbase."""
    url = 'https://api.coinbase.com/v2/prices/spot'
    try:
        resposta = requests.get(url)
        if resposta.status_code == 200:
            return resposta.json()
        else:
            logger.error(f"Erro na API: {resposta.status_code}")
            return None
    except Exception as ex:
        logger.error(f"Erro ao acessar a API da Coinbase: {ex}")
        return None

def tratar_dados_bitcoin(dados_json):
    """Transforma os dados brutos da API e adiciona timestamp."""
    try:
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
    except Exception as ex:
        logger.error(f"Erro ao tratar dados: {ex}")
        return None

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
    with logfire.span("Executando pipeline ETL Bitcoin"):
        with logfire.span("Extrair Dados da API Coinbase"):
            dados_json = extrair_dados_bitcoin()

        if not dados_json:
            logger.error("Falha na extração dos dados. Abortando pipeline.")
            return

        with logfire.span("Tratar Dados do Bitcoin"):
            dados_tratados = tratar_dados_bitcoin(dados_json)

        if not dados_tratados:
            logger.error("Falha no tratamento dos dados. Abortando pipeline.")
            return

        with logfire.span("Salvar Dados no Postgres"):
            salvar_dados_postgres(dados_tratados)

        logger.info("Pipeline finalizada com sucesso!")

if __name__ == "__main__":
    # Cria a tabela no banco de dados antes de iniciar a pipeline
    criar_tabela()
    logger.info("Iniciando pipeline ETL com atualização a cada 15 segundos... (CTRL+C para interromper)")

    # Inicia o servidor Flask em uma thread separada
    from threading import Thread

    def iniciar_flask():
        app.run(host="0.0.0.0", port=5000)

    flask_thread = Thread(target=iniciar_flask)
    flask_thread.start()

    # Executa a pipeline ETL em loop contínuo
    while True:
        try:
            pipeline_bitcoin()
            time.sleep(15)
        except KeyboardInterrupt:
            logger.info("Processo interrompido pelo usuário. Finalizando...")
            break
        except Exception as e:
            logger.error(f"Erro inesperado durante a pipeline: {e}")
            time.sleep(15)
