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


def extrair_dados_bitcoin():
    """Pega os dados da API e transforma num JSON."""
    url = 'https://api.coinbase.com/v2/prices/spot'
    resposta = requests.get(url)  # Faz uma requisição para a API da Coinbase
    return resposta.json()  # Retorna os dados da resposta no formato JSON

def tratar_dados_bitcoin(dados_json):
    # Essa função recebe o JSON armazenado na variável dados_json e processa os dados para extrair as informações desejadas.
    valor = float(dados_json['data']['amount'])
    criptomoeda = dados_json['data']['base']  
    moeda = dados_json['data']['currency']  
    timestamp = datetime.now()
    dados_tratados = [{  # Organiza os dados em uma lista de dicionários
            "valor": valor,
            "criptomoeda": criptomoeda,
            "moeda": moeda,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }]
        
    return dados_tratados  # Retorna os dados tratados

if __name__ == "__main__":
    # Extração dos dados
    dados_json = extrair_dados_bitcoin()  # A função extrair_dados_bitcoin é chamada, pega os dados da API e guarda o JSON aqui.
    dados_tratados = tratar_dados_bitcoin(dados_json)  # A função tratar_dados_bitcoin organiza os dados do JSON e guarda o resultado.
    print(dados_tratados)  # Exibe os dados tratados
