# app.py
# DDR-REFACTOR (v1.7): Correção de ícone e exibição de resposta definitiva.

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import core_logic
import style

# --- Configuração da Página e Aplicação do Estilo ---
load_dotenv()
st.set_page_config(page_title="CSV-Oracle", page_icon="🏛️", layout="centered")
style.apply_apple_style()

# --- Funções de UI ---
def display_agent_response(response):
    """
    Processa a resposta completa do agente e exibe o resultado da forma mais completa.
    Mostra a conclusão textual E a tabela de dados, se houver.
    """
    st.success("Resposta do Oráculo:")
    
    # 1. Exibe a conclusão em linguagem natural do agente.
    st.write(response['output'])
    
    # 2. Verifica se há dados tabulares na última observação e os exibe.
    if 'intermediate_steps' in response and response['intermediate_steps']:
        last_step = response['intermediate_steps'][-1]
        last_observation = last_step[1]
        
        if isinstance(last_observation, (pd.DataFrame, pd.Series)):
            st.write("---")
            st.write("Dados de Apoio:")
            st.dataframe(last_observation)

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
        if st.session_state.get('processed_file_name') != uploaded_file.name:
            st.session_state.df = None
            st.session_state.suggested_questions = []
            with st.spinner("Processando arquivos..."):
                try:
                    temp_dir = core_logic.unzip_file(uploaded_file.getvalue(), "temp_data")
                    csv_files = core_logic.find_csv_files(temp_dir)
                    if csv_files:
                        st.session_state.df = core_logic.load_and_combine_csvs(temp_dir, csv_files)
                        st.session_state.processed_file_name = uploaded_file.name
                except ValueError as e:
                    st.error(e)
    st.markdown('</div>', unsafe_allow_html=True)

# Card 2: Análise e Interação
if st.session_state.df is not None:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("2. Interaja com o Oráculo")

        if not st.session_state.suggested_questions:
            with st.spinner("Analisando e gerando sugestões..."):
                st.session_state.suggested_questions = core_logic.generate_suggested_questions(st.session_state.df)

        if st.session_state.suggested_questions:
            st.write("Comece com uma destas perguntas ou escreva a sua:")
            if 'user_question' not in st.session_state:
                st.session_state.user_question = ""

            def set_question(question):
                st.session_state.user_question = question
            
            cols = st.columns(len(st.session_state.suggested_questions) if st.session_state.suggested_questions else 1)
            for i, q in enumerate(st.session_state.suggested_questions):
                with cols[i]:
                    st.button(q, on_click=set_question, args=(q,), use_container_width=True, type="secondary")
        
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
