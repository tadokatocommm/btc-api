import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Lê as variáveis separadas do arquivo .env (sem SSL)
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

def ler_dados_postgres():
    """Lê os dados do banco PostgreSQL e retorna como DataFrame."""
    try:
        # Cria a URL de conexão usando SQLAlchemy
        DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        
        # Cria a conexão com SQLAlchemy
        engine = create_engine(DATABASE_URL)
        
        # Lê os dados do banco de dados PostgreSQL
        query = "SELECT * FROM bitcoin_precos ORDER BY timestamp DESC"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no PostgreSQL: {e}")
        return pd.DataFrame()

def main():
    st.set_page_config(page_title="Dashboard de Preços do Bitcoin", layout="wide")
    st.title("📊 Dashboard de Preços do Bitcoin")
    st.write("Este dashboard exibe os dados do preço do Bitcoin coletados periodicamente em um banco PostgreSQL.")

    df = ler_dados_postgres()

    if not df.empty:
        st.subheader("📋 Dados Recentes")
        st.dataframe(df)

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by='timestamp')
        
        st.subheader("📈 Evolução do Preço do Bitcoin")
        st.line_chart(data=df, x='timestamp', y='valor', use_container_width=True)

        st.subheader("🔢 Estatísticas Gerais")
        col1, col2, col3 = st.columns(3)
        col1.metric("Preço Atual", f"${df['valor'].iloc[-1]:,.2f}")
        col2.metric("Preço Máximo", f"${df['valor'].max():,.2f}")
        col3.metric("Preço Mínimo", f"${df['valor'].min():,.2f}")
    else:
        st.warning("Nenhum dado encontrado no banco de dados PostgreSQL.")

if __name__ == "__main__":
    main()