# app.py
# DevÆGENT™: CSV-Oracle v1.3 (Agente Proativo e Segurança de Segredos)

import streamlit as st
import pandas as pd
import os
import zipfile
import ast  # ## NOVO ##: Usado para converter a string de lista do LLM em uma lista Python real
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

## NOVO: Agente Analista para Sugerir Perguntas ##
def generate_suggested_questions(df, llm):
    """
    Analisa o DataFrame e usa um LLM para gerar perguntas sugeridas.
    """
    try:
        # Cria um resumo dos dados para enviar ao LLM
        schema = df.info(verbose=False, buf=None)
        head_data = df.head().to_string()
        
        prompt = f"""
        Você é um analista de dados especialista. Sua tarefa é analisar o esquema e as primeiras linhas de um conjunto de dados e gerar 3 perguntas de negócio perspicazes que um usuário poderia fazer.

        Resumo dos Dados:
        - Esquema (Colunas e Tipos de Dados):
        {schema}
        - Primeiras 5 linhas:
        {head_data}

        Com base neste resumo, gere 3 perguntas.
        Retorne APENAS uma lista Python de strings, sem nenhum texto ou explicação adicional.
        Exemplo de saída: ["Qual foi o total de vendas por cidade?", "Quem foi o cliente com mais compras?", "Qual produto teve a maior quantidade vendida?"]
        """
        
        response = llm.invoke(prompt)
        # Usa ast.literal_eval para converter a string de resposta em uma lista real
        suggested_questions = ast.literal_eval(response.content)
        return suggested_questions
    except Exception as e:
        print(f"Erro ao gerar sugestões: {e}")
        return [] # Retorna lista vazia em caso de erro

# --- Interface Principal e Orquestração ---

st.title("🧠 CSV-Oracle Proativo")
st.write("Carregue um `.zip` com seus CSVs. O Oráculo irá analisá-los e sugerir perguntas.")

# Gerenciamento de estado
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = None
if 'df' not in st.session_state:
    st.session_state.df = None
if 'suggested_questions' not in st.session_state:
    st.session_state.suggested_questions = []
if 'user_question' not in st.session_state:
    st.session_state.user_question = ""

# Fluxo 1: Upload e Descompactação
uploaded_file = st.file_uploader("Carregue seu arquivo .zip", type="zip")

if uploaded_file:
    # Limpa o estado anterior ao carregar um novo arquivo
    st.session_state.df = None
    st.session_state.suggested_questions = []
    st.session_state.user_question = ""
    
    with open("temp.zip", "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.temp_dir = unzip_file("temp.zip")
    os.remove("temp.zip")

# Fluxo 2: Seleção, Leitura e Análise Proativa
if st.session_state.temp_dir and st.session_state.df is None:
    csv_files = find_csv_files(st.session_state.temp_dir)
    if csv_files:
        selected_files = st.multiselect(
            "Selecione os arquivos CSV para analisar em conjunto:",
            csv_files,
            default=csv_files
        )
        if st.button("Analisar Arquivos Selecionados"):
            dataframes = []
            for file in selected_files:
                file_path = os.path.join(st.session_state.temp_dir, file)
                try:
                    df_temp = pd.read_csv(file_path, sep=None, engine='python')
                    dataframes.append(df_temp)
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo {file}: {e}")
            
            if dataframes:
                st.session_state.df = pd.concat(dataframes, ignore_index=True)
                st.success(f"{len(selected_files)} arquivo(s) carregado(s) e combinado(s)!")
                st.write("Amostra dos dados combinados:")
                st.dataframe(st.session_state.df.head())

                # ## NOVO: Aciona o Agente Analista ##
                with st.spinner("Analisando os dados para sugerir perguntas..."):
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.5)
                    st.session_state.suggested_questions = generate_suggested_questions(st.session_state.df, llm)

# Fluxo 3: Exibição das Sugestões e Caixa de Pergunta
if st.session_state.df is not None:
    st.divider()
    
    # ## NOVO: Exibe as perguntas sugeridas como botões ##
    if st.session_state.suggested_questions:
        st.subheader("Sugestões de Análise:")
        cols = st.columns(len(st.session_state.suggested_questions))
        for i, question in enumerate(st.session_state.suggested_questions):
            with cols[i]:
                if st.button(question, use_container_width=True):
                    st.session_state.user_question = question # Preenche a caixa de texto ao clicar

    # Caixa de texto que pode ser preenchida manualmente ou pelos botões
    user_question = st.text_input(
        "Faça sua pergunta sobre os dados combinados:", 
        value=st.session_state.user_question,
        key="text_input_question"
    )

    if user_question:
        if not os.getenv("GOOGLE_API_KEY"):
            st.error("Chave da API do Google não encontrada! Verifique seu arquivo .env ou os Secrets no Streamlit Cloud.")
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
