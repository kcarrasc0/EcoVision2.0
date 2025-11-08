# pages/3_Previsao_de_Risco.py
import streamlit as st
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import numpy as np

# --- GUARDIÃO DE AUTENTICAÇÃO ---
if not st.session_state.get("autenticado", False):
    st.error("Acesso negado. Por favor, faça o login primeiro.")
    st.page_link("app.py", label="Ir para a página de Login", icon="🏠")
    st.stop()
# --- FIM DO GUARDIÃO ---

st.set_page_config(page_title="Previsão de Risco", layout="wide")
st.title("🧠 Previsão de Risco de Queimadas")

# --- 1. FUNÇÃO DE CARREGAMENTO DE DADOS (VERSÃO CORRIGIDA) ---
BASE_URL = "https://raw.githubusercontent.com/kcarrasc0/EcoVision2.0/main/data/"
nomes_biomas = ["amazonia", "caatinga", "cerrado", "mata_atlantica", "pampa", "pantanal"]

@st.cache_data
def carregar_dados_biomas():
    lista_de_dataframes = []
    for bioma in nomes_biomas:
        url_csv = f"{BASE_URL}{bioma}.csv"
        try:
            # --- A CORREÇÃO FINAL: Mudar de 'latin1' para 'utf-8-sig' ---
            df = pd.read_csv(url_csv, delimiter=';', encoding='utf-8-sig')
            
            # Normalizar os nomes das colunas (ainda uma boa prática)
            df.columns = df.columns.str.strip().str.lower()
            
            lista_de_dataframes.append(df)
            
        except Exception as e:
            st.error(f"ERRO CRÍTICO ao carregar o arquivo: {url_csv}")
            st.error(f"Detalhe: {e}")
            return pd.DataFrame()
            
    if not lista_de_dataframes:
        st.error("Nenhum dado de bioma foi carregado. Verifique a BASE_URL no código.")
        return pd.DataFrame()
        
    df_completo = pd.concat(lista_de_dataframes, ignore_index=True)
    
    # Verificar se as colunas existem ANTES de renomear
    colunas_esperadas = ['date', 'class', 'focuses', 'uf']
    if not all(col in df_completo.columns for col in colunas_esperadas):
        st.error("ERRO DE COLUNA: Um ou mais arquivos CSV não continham as colunas esperadas.")
        st.error(f"Colunas esperadas (após normalização): {colunas_esperadas}")
        st.error(f"Colunas realmente encontradas: {df_completo.columns.tolist()}")
        return pd.DataFrame()
        
    df_completo.rename(columns={'uf': 'estado', 'focuses': 'focos'}, inplace=True)
    
    # Engenharia de Features
    try:
        df_completo['date'] = pd.to_datetime(df_completo['date'], format='%Y/%m')
        df_completo['ano'] = df_completo['date'].dt.year
        df_completo['mes'] = df_completo['date'].dt.month
    except Exception as e:
        st.error(f"Erro ao processar a coluna 'date'. Verifique o formato dos dados. Erro: {e}")
        return pd.DataFrame()

    df_completo.dropna(subset=['estado', 'focos', 'ano', 'mes'], inplace=True)
    return df_completo

# --- 2. FUNÇÃO DE TREINAMENTO DO MODELO ---
@st.cache_resource
def treinar_modelo():
    df = carregar_dados_biomas()
    
    if df.empty:
        return None, None

    df_agregado = df.groupby(['estado', 'ano', 'mes'])['focos'].sum().reset_index()
    X = df_agregado[['estado', 'ano', 'mes']]
    y = df_agregado['focos']

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['estado']),
            ('num', 'passthrough', ['ano', 'mes'])
        ])

    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])

    model_pipeline.fit(X, y)
    
    return model_pipeline, sorted(df['estado'].unique())

# --- Carrega e treina o modelo ---
with st.spinner("Carregando dados históricos e treinando modelo de IA..."):
    modelo, estados_conhecidos = treinar_modelo()

if modelo is None:
    st.error("Falha ao carregar ou processar os dados. A página de previsão não pode funcionar. Verifique os erros acima.")
    st.stop()

st.success("Modelo de previsão treinado e pronto!")

# --- 3. INTERFACE DO USUÁRIO PARA PREVISÃO ---
st.header("Faça sua Previsão")
st.write("Selecione os parâmetros para estimar o número de focos de queimada.")

col1, col2, col3 = st.columns(3)

with col1:
    estado_selecionado = st.selectbox("Selecione o Estado (UF)", estados_conhecidos)
with col2:
    mes_selecionado = st.selectbox("Selecione o Mês", range(1, 13), format_func=lambda m: f"{m:02d}")
with col3:
    # --- CORREÇÃO DE BUG ---
    # Chamar carregar_dados_biomas() aqui é lento
    # Vamos usar o 'df_agregado' do treinamento para pegar o ano max
    df_para_ano = carregar_dados_biomas()
    if not df_para_ano.empty:
        ano_maximo = df_para_ano['ano'].max()
        ano_sugerido = ano_maximo + 1
    else:
        ano_sugerido = 2026 # fallback
        
    ano_selecionado = st.number_input("Insira o Ano", min_value=2000, max_value=2050, value=ano_sugerido)

if st.button("Estimar Risco de Queimadas", type="primary"):
    input_data = pd.DataFrame({
        'estado': [estado_selecionado],
        'ano': [ano_selecionado],
        'mes': [mes_selecionado]
    })
    
    try:
        previsao = modelo.predict(input_data)
        
        st.subheader("Resultado da Previsão:")
        st.metric("Número Estimado de Focos", f"{int(previsao[0]):,d}")
        
        st.warning(
            "Esta é uma estimativa baseada em padrões históricos. "
            "Não leva em conta condições climáticas em tempo real (secas, El Niño) ou novas políticas de desmatamento."
        )

        st.subheader(f"Histórico de Focos para: {estado_selecionado}")
        df_historico = carregar_dados_biomas()
        df_estado = df_historico[df_historico['estado'] == estado_selecionado]
        
        if not df_estado.empty:
            focos_por_mes = df_estado.groupby(['ano', 'mes'])['focos'].sum().reset_index()
            focos_por_mes['data'] = pd.to_datetime(focos_por_mes['ano'].astype(str) + '-' + focos_por_mes['mes'].astype(str))
            focos_por_mes_chart = focos_por_mes[['data', 'focos']].set_index('data')
            st.line_chart(focos_por_mes_chart)
        else:
            st.info("Não há dados históricos detalhados para este estado.")
            
    except Exception as e:
        st.error(f"Erro ao fazer a previsão: {e}")

# Botão de Logout
if st.sidebar.button("Logout"):
    st.session_state["autenticado"] = False
    st.switch_page("app.py")