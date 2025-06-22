# app.py
# DevÆGENT™: CSV-Oracle v1.1 (Edição Gemini API)

## DevÆGENT Explica: Importações
# Importamos as ferramentas necessárias. Note a adição de 'ChatGoogleGenerativeAI'
# e a remoção de qualquer coisa relacionada à OpenAI.
import streamlit as st
import pandas as pd
import os
import zipfile
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from dotenv import load_dotenv

# --- Configuração da Página e Chave de API ---

## DevÆGENT Explica: Carregando a Chave Secreta
# Esta linha lê o arquivo .env que você criou e torna a GOOGLE_API_KEY
# disponível para o nosso programa de forma segura.
load_dotenv()

# Configuração da página do Streamlit.
st.set_page_config(
    page_title="CSV-Oracle (Gemini Edition)",
    page_icon="✨",
    layout="centered"
)

# --- Agentes Funcionais (Módulos de Trabalho) ---

## DevÆGENT Explica: Agente 1 - Descompactador
# Esta função recebe o arquivo .zip, cria uma pasta temporária e extrai
# os CSVs para dentro dela. É um módulo simples e robusto.
def unzip_file(zip_path, extract_to='temp_csvs'):
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return extract_to

## DevÆGENT Explica: Agente 2 - Leitor e Indexador
# Esta função olha dentro da pasta temporária e lista todos os arquivos
# que terminam com .csv. Isso alimenta nosso menu de seleção.
def find_csv_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.csv')]

# --- Interface Principal e Orquestração ---

st.title("✨ CSV-Oracle com Gemini")
st.write("Converse com seus dados. Faça o upload de um arquivo `.zip` com seus CSVs.")

# Gerenciamento de estado para não perder os dados ao interagir com a UI
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = None
if 'df' not in st.session_state:
    st.session_state.df = None

# Fluxo 1: Upload e Descompactação
uploaded_file = st.file_uploader("Carregue seu arquivo .zip", type="zip")

if uploaded_file:
    with open("temp.zip", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Aciona o Agente 1
    st.session_state.temp_dir = unzip_file("temp.zip")
    os.remove("temp.zip")

# Fluxo 2: Seleção e Leitura do CSV
if st.session_state.temp_dir:
    # Aciona o Agente 2
    csv_files = find_csv_files(st.session_state.temp_dir)
    if csv_files:
        selected_csv = st.selectbox("Selecione o arquivo para analisar:", csv_files)
        if selected_csv:
            file_path = os.path.join(st.session_state.temp_dir, selected_csv)
            try:
                # O Agente 2 agora lê o arquivo escolhido e o armazena na memória.
                # 'sep=None' e 'engine="python"' ajudam o Pandas a detectar o separador (vírgula, ponto e vírgula) automaticamente.
                st.session_state.df = pd.read_csv(file_path, sep=None, engine='python')
                st.success(f"Arquivo '{selected_csv}' carregado. Veja uma amostra:")
                st.dataframe(st.session_state.df.head())
            except Exception as e:
                st.error(f"Erro ao ler o arquivo: {e}")
                st.session_state.df = None

# Fluxo 3: Pergunta e Resposta com IA
if st.session_state.df is not None:
    st.divider()
    user_question = st.text_input("Agora, faça sua pergunta:", placeholder="Ex: Qual cliente gastou mais?")

    if user_question:
        # Verificação de segurança: garante que a chave foi carregada
        if not os.getenv("GOOGLE_API_KEY"):
            st.error("Chave da API do Google não encontrada! Verifique seu arquivo .env.")
        else:
            with st.spinner("O Oráculo Gemini está analisando os dados..."):
                try:
                    ## DevÆGENT Explica: O Cérebro Cognitivo (agora com Gemini)
                    # Esta é a mudança principal.
                    # 1. Instanciamos o LLM do Google, especificando o modelo 'gemini-pro'.
                    # 2. 'temperature=0' torna a resposta mais precisa e menos "criativa",
                    #    o que é essencial para análise de dados.
                    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)

                    # 3. Criamos o agente da LangChain, passando o cérebro (llm) e os dados (df).
                    #    Este agente é especializado em traduzir perguntas em código Pandas.
                    agent = create_pandas_dataframe_agent(
                        llm,
                        st.session_state.df,
                        verbose=True,
                        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                        handle_parsing_errors=True
                    )
                    
                    # Aciona o Agente 3 (Consulta)
                    response = agent.invoke(user_question)

                    # Aciona o Agente 4 (Apresentação)
                    st.success("Resposta do Oráculo:")
                    st.write(response['output'])

                except Exception as e:
                    st.error(f"Ocorreu um erro durante a consulta: {e}")