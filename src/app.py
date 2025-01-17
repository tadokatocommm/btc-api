import requests
from datetime import datetime

def extrair_dados_bitcoin():
    """Pega os dados da API e transforma num JSON."""
    url = 'https://api.coinbase.com/v2/prices/spot'
    resposta = requests.get(url)  # Faz uma requisição para a API da Coinbase
    return resposta.json()  # Retorna os dados da resposta no formato JSON

def tratar_dados_bitcoin(dados_json):
    # Essa função recebe o JSON armazenado na variável dados_json e processa os dados para extrair as informações desejadas.
    valor = dados_json['data']['amount']  
    criptomoeda = dados_json['data']['base']  
    moeda = dados_json['data']['currency']  
                
    dados_tratados = [{  # Organiza os dados em uma lista de dicionários
            "valor": valor,
            "criptomoeda": criptomoeda,
            "moeda": moeda
        }]
        
    return dados_tratados  # Retorna os dados tratados

if __name__ == "__main__":
    # Extração dos dados
    dados_json = extrair_dados_bitcoin()  # A função extrair_dados_bitcoin é chamada, pega os dados da API e guarda o JSON aqui.
    dados_tratados = tratar_dados_bitcoin(dados_json)  # A função tratar_dados_bitcoin organiza os dados do JSON e guarda o resultado.
    print(dados_tratados)  # Exibe os dados tratados
