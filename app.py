# app_refactored.py
# DDR-REFACTOR (User Flow): UI reestruturada com cards e hierarquia visual.

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import core_logic
import style # Importa o novo módulo de estilo

# --- Configuração da Página e Aplicação do Estilo ---
load_dotenv()
st.set_page_config(page_title="CSV-Oracle", page_icon="🏛️", layout="centered")
style.apply_apple_style() # Aplica o CSS customizado

# --- Funções de UI ---
def display_agent_response(response):
    # ... (código inalterado)
    st.success("Resposta do Oráculo:")
    if 'intermediate_steps' in response and response['intermediate_steps']:
        last_observation = response['intermediate_steps'][-1][1]
        if isinstance(last_observation, (pd.DataFrame, pd.Series)):
            st.dataframe(last_observation)
        else:
            st.write(last_observation)
    elif 'output' in response:
        st.write(response['output'])
    else:
        st.write("O agente não produziu uma saída reconhecível.")

# --- Interface Principal e Orquestração ---
st.title("🏛️ CSV-Oracle")
st.caption("Sua central de análise de dados inteligente.")

# Gerenciamento de estado
if 'df' not in st.session_state:
    st.session_state.df = None
if 'suggested_questions' not in st.session_state:
    st.session_state.suggested_questions = []

# Card 1: Upload e Processamento
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("1. Carregue seus Dados")
    uploaded_file = st.file_uploader(
        "Arraste e solte um arquivo .zip contendo seus CSVs", 
        type="zip", 
        label_visibility="collapsed"
    )

    if uploaded_file:
        # Lógica de processamento é acionada aqui
        if st.session_state.get('processed_file_name') != uploaded_file.name:
            st.session_state.df = None
            st.session_state.suggested_questions = []
            with st.spinner("Processando arquivos..."):
                temp_dir = core_logic.unzip_file(uploaded_file.getvalue(), "temp_data")
                csv_files = core_logic.find_csv_files(temp_dir)
                if csv_files:
                    try:
                        st.session_state.df = core_logic.load_and_combine_csvs(temp_dir, csv_files)
                        st.session_state.processed_file_name = uploaded_file.name
                    except ValueError as e:
                        st.error(e)
    st.markdown('</div>', unsafe_allow_html=True)


# Card 2: Análise e Interação (Aparece após o upload)
if st.session_state.df is not None:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("2. Interaja com o Oráculo")

        # Geração de sugestões (se ainda não foram geradas)
        if not st.session_state.suggested_questions:
            with st.spinner("Analisando e gerando sugestões..."):
                st.session_state.suggested_questions = core_logic.generate_suggested_questions(st.session_state.df)

        # Exibição das sugestões
        if st.session_state.suggested_questions:
            st.write("Comece com uma destas perguntas ou escreva a sua:")
            if 'user_question' not in st.session_state:
                st.session_state.user_question = ""

            def set_question(question):
                st.session_state.user_question = question
            
            # Usando st.columns para um layout mais limpo
            cols = st.columns(len(st.session_state.suggested_questions))
            for i, q in enumerate(st.session_state.suggested_questions):
                with cols[i]:
                    st.button(q, on_click=set_question, args=(q,), use_container_width=True, type="secondary")
        
        # Caixa de pergunta e botão de ação
        user_question = st.text_input(
            "Sua pergunta:",
            key="user_question",
            placeholder="Ex: Qual foi o total de vendas por região?"
        )

        if st.button("Perguntar ao Oráculo", use_container_width=True, type="primary"):
            if user_question:
                with st.spinner("Consultando o Oráculo..."):
                    try:
                        response = core_logic.invoke_query_agent(st.session_state.df, user_question)
                        display_agent_response(response)
                    except Exception as e:
                        st.error(f"Erro na consulta: {e}")
            else:
                st.warning("Por favor, digite uma pergunta.")
        st.markdown('</div>', unsafe_allow_html=True)
