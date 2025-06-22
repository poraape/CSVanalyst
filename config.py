# config.py
# DDR-REFACTOR (Abstracted): Centraliza configurações para fácil manutenção.

# Configurações do Modelo de IA
LLM_SUGGESTION_MODEL = "gemini-1.5-flash-latest"
LLM_AGENT_MODEL = "gemini-1.5-flash-latest"
LLM_TEMPERATURE_SUGGESTION = 0.5
LLM_TEMPERATURE_AGENT = 0.0

# Prompts
SUGGESTION_PROMPT_TEMPLATE = """
Você é um analista de dados sênior. Com base no esquema e nas primeiras linhas de dados abaixo, gere 3 perguntas de negócio relevantes e acionáveis.

Esquema:
{schema_info}
Amostra de Dados:
{head_data}

Retorne sua resposta como uma lista Python de strings, e nada mais.
Exemplo de saída: ["Qual foi o total de vendas por categoria?", "Quais são os 5 principais clientes por valor de compra?", "Existe alguma correlação entre a quantidade e o preço unitário?"]
"""