# core_logic.py
# DDR-REFACTOR (Robustness): Corrigido o erro de tipo no unzip.

import os
import zipfile
import pandas as pd
import re
import ast
import io # Importado para criar arquivos em memória
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType
import config

def unzip_file(zip_bytes, extract_to='temp_csvs'):
    """
    Descompacta um arquivo .zip a partir de seus bytes brutos.
    Usa um arquivo em memória (io.BytesIO) para evitar erros de tipo.
    """
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
    
    # Cria um arquivo em memória a partir dos bytes do upload
    zip_in_memory = io.BytesIO(zip_bytes)
    
    # O ZipFile agora opera no arquivo em memória, que tem o método .seek()
    with zipfile.ZipFile(zip_in_memory, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return extract_to

def find_csv_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.csv')]

def load_and_combine_csvs(directory, selected_files):
    dataframes = []
    for file in selected_files:
        file_path = os.path.join(directory, file)
        try:
            df_temp = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='warn')
            dataframes.append(df_temp)
        except Exception as e:
            raise ValueError(f"Erro ao ler o arquivo {file}: {e}")
    
    if not dataframes:
        return None
    return pd.concat(dataframes, ignore_index=True)

def generate_suggested_questions(df):
    try:
        buffer = io.StringIO()
        df.info(buf=buffer)
        schema_info = buffer.getvalue()
        head_data = df.head().to_string()
        
        prompt = config.SUGGESTION_PROMPT_TEMPLATE.format(schema_info=schema_info, head_data=head_data)
        
        llm = ChatGoogleGenerativeAI(
            model=config.LLM_SUGGESTION_MODEL, 
            temperature=config.LLM_TEMPERATURE_SUGGESTION
        )
        response = llm.invoke(prompt).content
        
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return ast.literal_eval(match.group(0))
        return []
    except Exception:
        return []

def invoke_query_agent(df, question):
    llm = ChatGoogleGenerativeAI(
        model=config.LLM_AGENT_MODEL, 
        temperature=config.LLM_TEMPERATURE_AGENT
    )
    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        allow_dangerous_code=True
    )
    return agent.invoke(question)
