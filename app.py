# app.py
# DevÆGENT™: CSV-Oracle v1.5 (Correção de Parser de Sugestões)

import streamlit as st
import pandas as pd
import os
import zipfile
import ast
import re # Importado para o parser robusto
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from dotenv import load_dotenv

# --- Configuração da Página e Chave de API ---
load_dotenv()

st.set_page_config(
    page_title="CSV-Oracle Proativo",
    page_icon="🧠",
    layout="centered"
)

# --- Agentes Funcionais (Módulos de Trabalho) ---
def unzip_file(zip_path, extract_to='temp_csvs'):
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return extract_to

def find_csv_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.csv')]

def generate_suggested_questions(df, llm):
    """
    Analisa o DataFrame e usa um LLM para gerar perguntas sugeridas.
    Usa regex para extrair a lista da resposta do LLM, tornando-a mais robusta.
    """
    try:
        # Usamos to_string() para garantir que a informação seja passada como texto
        schema_info = df.info(verbose=False, buf=None)
        if schema_info is None: # df.info() imprime no buffer, precisamos capturá-lo
            import io
            buffer = io.StringIO()
            df.info(buf=buffer)
            schema_info = buffer.getvalue()

        head_data = df.head().to_string()
        
        prompt = f"""
        Você é um analista de dados sênior. Com base no esquema e nas primeiras linhas de dados abaixo, gere 3 perguntas de negócio relevantes e acionáveis.

        Esquema:
        {schema_info}
        Amostra de Dados:
        {head_data}

        Retorne sua resposta como uma lista Python de strings, e nada mais.
        Exemplo de saída: ["Qual foi o total de vendas por categoria?", "Quais são os 5 principais clientes por valor de compra?", "Existe alguma correlação entre a quantidade e o preço unitário?"]
        """
        
        response = llm.invoke(prompt).content
        
        # Procura por qualquer coisa que se pareça com uma lista '[...]' na resposta
        match = re.search(r'\[.*\]', response, re.DOTALL)
        
        if match:
            list_str = match.group(0)
            return ast.literal_eval(list_str)
        else:
            st.warning("O LLM não retornou uma lista de sugestões no formato esperado.")
            return []

    except Exception as e:
        st.warning(f"Não foi possível gerar sugestões: {e}")
        return []

# --- O resto do código permanece o mesmo da v1.4 ---
# (Interface Principal e Orquestração)

# Gerenciamento de estado
if 'df' not in st.session_state:
    st.session_state.df = None
if 'suggested_questions' not in st.session_state:
    st.session_state.suggested_questions = []

# Fluxo 1: Upload e Descompactação
uploaded_file = st.file_uploader("Carregue seu arquivo .zip", type="zip")

if uploaded_file:
    st.session_state.df = None
    st.session_state.suggested_questions = []
    
    with open("temp.zip", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    temp_dir = unzip_file("temp.zip")
    os.remove("temp.zip")

    csv_files = find_csv_files(temp_dir)
    if csv_files:
        with st.spinner("Processando arquivos..."):
            dataframes = []
            for file in csv_files:
                file_path = os.path.join(temp_dir, file)
                try:
                    df_temp = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='warn')
                    dataframes.append(df_temp)
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo {file}: {e}")
            
            if dataframes:
                st.session_state.df = pd.concat(dataframes, ignore_index=True)

# Fluxo 2: Análise Proativa e Exibição dos Dados (Automático)
if st.session_state.df is not None and not st.session_state.suggested_questions:
    st.success(f"{len(st.session_state.df.columns)} colunas e {len(st.session_state.df)} linhas carregadas e combinadas!")
    st.write("Amostra dos dados:")
    st.dataframe(st.session_state.df.head())

    with st.spinner("Analisando os dados para sugerir perguntas..."):
        if not os.getenv("GOOGLE_API_KEY"):
            st.warning("Chave da API não configurada. Não é possível gerar sugestões.")
        else:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.5)
            st.session_state.suggested_questions = generate_suggested_questions(st.session_state.df, llm)

# Fluxo 3: Interação com o Usuário (Sugestões e Pergunta)
if st.session_state.df is not None:
    st.divider()
    
    if st.session_state.suggested_questions:
        st.subheader("Sugestões de Análise:")
        if 'user_question' not in st.session_state:
            st.session_state.user_question = ""

        def set_question(question):
            st.session_state.user_question = question

        for q in st.session_state.suggested_questions:
            st.button(q, on_click=set_question, args=(q,), use_container_width=True)
    
    user_question = st.text_input(
        "Faça sua pergunta ou clique em uma sugestão acima:",
        key="user_question"
    )

    if st.button("Perguntar ao Oráculo"):
        if user_question:
            if not os.getenv("GOOGLE_API_KEY"):
                st.error("Chave da API do Google não encontrada!")
            else:
                with st.spinner("O Oráculo Gemini está consultando os dados..."):
                    try:
                        llm_agent = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)
                        agent = create_pandas_dataframe_agent(
                            llm_agent,
                            st.session_state.df,
                            verbose=True,
                            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                            handle_parsing_errors=True,
                            allow_dangerous_code=True
                        )
                        
                        response = agent.invoke(user_question)
                        st.success("Resposta do Oráculo:")
                        st.write(response['output'])

                    except Exception as e:
                        st.error(f"Ocorreu um erro durante a consulta: {e}")
        else:
            st.warning("Por favor, digite uma pergunta.")
