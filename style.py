# style.py
# DDR-REFACTOR (Aesthetic Appeal): Módulo para injetar CSS customizado.

import streamlit as st

def apply_apple_style():
    """
    Aplica um CSS customizado para emular a estética da Apple.
    """
    custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    :root {
        --primary-color: #007AFF; /* Apple Blue */
        --background-color: #F0F2F6; /* Light Gray Background */
        --card-background-color: #FFFFFF;
        --text-color: #1D1D1F; /* Near Black */
        --subtle-text-color: #6E6E73;
        --border-color: #D1D1D6;
    }

    body {
        font-family: 'Inter', sans-serif;
        background-color: var(--background-color);
        color: var(--text-color);
    }

    /* Títulos */
    h1, h2, h3 {
        font-weight: 700 !important;
    }

    /* Cards para agrupar conteúdo */
    .card {
        background-color: var(--card-background-color);
        border-radius: 18px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid var(--border-color);
    }

    /* Botão Primário (Perguntar ao Oráculo) */
    .stButton > button {
        border-radius: 12px;
        background-color: var(--primary-color);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: background-color 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #0056b3;
        color: white;
    }
    .stButton > button:focus {
        box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.5);
    }

    /* Botões Secundários (Sugestões) */
    .stButton[kind="secondary"] > button {
        border-radius: 12px;
        background-color: #EFEFF4;
        color: var(--primary-color);
        border: 1px solid #EFEFF4;
        font-weight: 600;
        transition: background-color 0.2s ease-in-out;
    }
    .stButton[kind="secondary"] > button:hover {
        background-color: #DCDCE0;
    }

    /* Caixa de Texto */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 1px solid var(--border-color);
        background-color: #F8F8F8;
        padding: 0.75rem 1rem;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.3);
    }
    
    /* Legendas e textos sutis */
    .stCaption {
        color: var(--subtle-text-color);
    }
    """
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)