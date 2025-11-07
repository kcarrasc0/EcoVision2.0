# pages/1_Dashboard.py
import streamlit as st
import pandas as pd

# --- GUARDIÃO DE AUTENTICAÇÃO ---
if not st.session_state.get("autenticado", False):
    st.error("Acesso negado. Por favor, faça o login primeiro.")
    st.page_link("app.py", label="Ir para a página de Login", icon="🏠")
    st.stop()
# --- FIM DO GUARDIÃO ---

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard EcoVision", layout="wide")
st.title("📊 Dashboard de Monitoramento de Queimadas")

# --- URLs DE DADOS ---
# !! IMPORTANTE !! Lembre-se de ajustar esta URL
BASE_URL = "https://raw.githubusercontent.com/SEU-USUARIO/SEU-REPOSITORIO/main/data/" 

# --- FUNÇÃO 1: CARREGAR DADOS DOS BIOMAS (os 6 arquivos) ---
@st.cache_data
def carregar_dados_biomas():
    nomes_biomas = ["amazonia", "caatinga", "cerrado", "mata_atlantica", "pampa", "pantanal"]
    lista_de_dataframes = []
    
    for bioma in nomes_biomas:
        url_csv = f"{BASE_URL}{bioma}.csv"
        try:
            # Tenta com ';' e depois com ',' como delimitador
            try:
                df = pd.read_csv(url_csv, delimiter=';')
            except pd.errors.ParserError:
                df = pd.read_csv(url_csv, delimiter=',')
                
            df['bioma'] = bioma.replace("_", " ").title() 
            lista_de_dataframes.append(df)
        except Exception as e:
            st.warning(f"Não foi possível carregar {url_csv}: {e}")
            
    if not lista_de_dataframes:
        st.error("Nenhum dado de bioma foi carregado.")
        return pd.DataFrame()
        
    df_completo = pd.concat(lista_de_dataframes, ignore_index=True)
    
    # Padronização: assume que 'focos' e 'estado' existem
    if 'focos' not in df_completo.columns or 'estado' not in df_completo.columns:
        st.error("Os arquivos de bioma não contêm as colunas 'focos' ou 'estado'. Esta análise pode falhar.")
        return pd.DataFrame()
        
    return df_completo

# --- FUNÇÃO 2: CARREGAR DADOS DE ESTADOS (queimadas_brasil.csv) ---
@st.cache_data
def carregar_dados_estados():
    url_csv = f"{BASE_URL}queimadas_brasil.csv"
    try:
        df_completo = pd.read_csv(url_csv, delimiter=";")
        df_completo.rename(columns={'uf': 'estado', 'focuses': 'focos'}, inplace=True)
        
        if 'estado' not in df_completo.columns or 'focos' not in df_completo.columns:
            st.error("Arquivo 'queimadas_brasil.csv' não contém 'uf' ou 'focuses'.")
            return pd.DataFrame()
            
        df_completo.dropna(subset=['estado'], inplace=True)
        return df_completo
    except Exception as e:
        st.error(f"Erro fatal ao carregar 'queimadas_brasil.csv': {e}")
        return pd.DataFrame()

# --- SIDEBAR E SELEÇÃO DE VISÃO ---
st.sidebar.title("Filtros")

tipo_analise = st.sidebar.radio(
    "Selecione o tipo de análise:",
    ("Análise por Bioma", "Análise por Estado (UF)")
)

# --- LÓGICA PRINCIPAL DA PÁGINA ---

if tipo_analise == "Análise por Bioma":
    st.header("Visão 1: Análise por Bioma")
    df_biomas = carregar_dados_biomas()
    
    if not df_biomas.empty:
        # Filtro de Bioma
        opcoes_biomas = ['Todos'] + sorted(df_biomas['bioma'].unique())
        bioma_selecionado = st.sidebar.selectbox("Selecione o Bioma", opcoes_biomas, key='filtro_bioma')
        
        # Aplicar filtro
        if bioma_selecionado == 'Todos':
            df_filtrado = df_biomas
        else:
            df_filtrado = df_biomas[df_biomas['bioma'] == bioma_selecionado]
            
        # Dashboard
        st.metric("Total de Focos (Biomas)", f"{df_filtrado['focos'].sum():,.0f}")
        st.subheader("Focos por Estado (nesta visão)")
        focos_por_estado = df_filtrado.groupby('estado')['focos'].sum().nlargest(10)
        st.bar_chart(focos_por_estado)
        
        st.subheader("Dados Detalhados (Biomas)")
        st.dataframe(df_filtrado)
        
        # Download
        csv_dl = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar Visão (Biomas)", csv_dl, "dados_biomas.csv", "text/csv")

else: # tipo_analise == "Análise por Estado (UF)"
    st.header("Visão 2: Análise por Estado (UF)")
    df_estados = carregar_dados_estados()
    
    if not df_estados.empty:
        # Filtro de Estado
        opcoes_estados = ['Todos'] + sorted(df_estados['estado'].unique())
        estado_selecionado = st.sidebar.selectbox("Selecione o Estado (UF)", opcoes_estados, key='filtro_estado')
        
        # Aplicar filtro
        if estado_selecionado == 'Todos':
            df_filtrado = df_estados
        else:
            df_filtrado = df_estados[df_estados['estado'] == estado_selecionado]
        
        # Dashboard
        st.metric("Total de Focos (Estados)", f"{df_filtrado['focos'].sum():,.0f}")
        
        # Gráfico de Focos por Classe (a coluna 'class' do seu CSV)
        if 'class' in df_filtrado.columns:
            st.subheader("Focos por Classe (nesta visão)")
            focos_por_classe = df_filtrado.groupby('class')['focos'].sum().sort_values(ascending=False)
            st.bar_chart(focos_por_classe)
        
        st.subheader("Dados Detalhados (Estados)")
        st.dataframe(df_filtrado)
        
        # Download
        csv_dl = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("Exportar Visão (Estados)", csv_dl, "dados_estados.csv", "text/csv")


# Botão de Logout (sempre no final)
if st.sidebar.button("Logout"):
    st.session_state["autenticado"] = False
    st.switch_page("app.py")