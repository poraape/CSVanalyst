# app.py
# DevÆGENT™: CSV-Oracle v1.6 (Exibição Inteligente de Resultados)

import streamlit as st
import pandas as pd
import os
import zipfile
import ast
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from dotenv import load_dotenv

# --- Configuração da Página e Chave de API ---
load_dotenv()

st.set_page_config(
    page_title="CSV-Oracle Proativo",
    page_icon="💡",
    layout="centered"
)

# --- Agentes Funcionais (Módulos de Trabalho) ---
# As funções unzip_file, find_csv_files, e generate_suggested_questions permanecem as mesmas da v1.5

def unzip_file(zip_path, extract_to='temp_csvs'):
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return extract_to

def find_csv_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.csv')]

def generate_suggested_questions(df, llm):
    try:
        import io
        buffer = io.StringIO()
        df.info(buf=buffer)
        schema_info = buffer.getvalue()
        head_data = df.head().to_string()
        
        prompt = f"""
        Você é um analista de dados sênior. Com base no esquema e nas primeiras linhas de dados abaixo, gere 3 perguntas de negócio relevantes e acionáveis.
        Retorne sua resposta como uma lista Python de strings, e nada mais.
        Exemplo de saída: ["Qual foi o total de vendas por categoria?", "Quais são os 5 principais clientes por valor de compra?", "Existe alguma correlação entre a quantidade e o preço unitário?"]
        """
        
        response = llm.invoke(prompt).content
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

## NOVO: Função de Exibição Inteligente ##
def display_agent_response(response):
    """
    Processa a resposta completa do agente e exibe o resultado da forma mais apropriada.
    Prioriza a última 'Observação' dos passos intermediários.
    """
    st.success("Resposta do Oráculo:")

    # Prioridade 1: Tentar extrair a última observação (o dado real)
    if 'intermediate_steps' in response and response['intermediate_steps']:
        last_observation = response['intermediate_steps'][-1][1]
        
        # Se a observação for um DataFrame ou uma Série, use st.dataframe
        if isinstance(last_observation, (pd.DataFrame, pd.Series)):
            st.dataframe(last_observation)
        # Senão, use st.write para exibir como texto
        else:
            st.write(last_observation)
    # Prioridade 2 (Fallback): Se não houver passos, exibir a saída final
    elif 'output' in response:
        st.write(response['output'])
    # Prioridade 3 (Fallback final): Se a resposta for um mistério
    else:
        st.write("O agente não produziu uma saída reconhecível.")


# --- Interface Principal e Orquestração ---
# (O fluxo principal permanece o mesmo da v1.4/v1.5, mas com a chamada da nova função de exibição)

st.title("💡 CSV-Oracle Proativo")
st.write("Carregue um `.zip` com seus CSVs. O Oráculo irá analisá-los e sugerir perguntas.")

if 'df' not in st.session_state:
    st.session_state.df = None
if 'suggested_questions' not in st.session_state:
    st.session_state.suggested_questions = []

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
                        
                        # ## AQUI ESTÁ A MUDANÇA ##
                        # Em vez de uma simples chamada st.write, usamos nossa nova função inteligente.
                        display_agent_response(response)

                    except Exception as e:
                        st.error(f"Ocorreu um erro durante a consulta: {e}")
        else:
            st.warning("Por favor, digite uma pergunta.")
