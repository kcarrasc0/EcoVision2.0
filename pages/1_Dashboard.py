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
BASE_URL = "https://raw.githubusercontent.com/kcarrasc0/EcoVision2.0/refs/heads/main/data/" 

# Lista dos arquivos CSV de biomas
nomes_biomas = [
    "amazonia",
    "caatinga",
    "cerrado",
    "mata_atlantica",
    "pampa",
    "pantanal"
]

# --- FUNÇÃO DE CARREGAMENTO (AGORA CORRIGIDA) ---
@st.cache_data
def carregar_dados_biomas():
    lista_de_dataframes = []
    
    for bioma in nomes_biomas:
        url_csv = f"{BASE_URL}{bioma}.csv"
        try:
            # CORREÇÃO 1: Usando encoding='latin1' e delimiter=';'
            df = pd.read_csv(url_csv, delimiter=';', encoding='latin1')
            
            # Adiciona a coluna 'bioma' baseada no nome do arquivo
            df['bioma'] = bioma.replace("_", " ").title() 
            lista_de_dataframes.append(df)
        except Exception as e:
            st.warning(f"Não foi possível carregar {url_csv}: {e}")
            
    if not lista_de_dataframes:
        st.error("Nenhum dado de bioma foi carregado. Verifique a BASE_URL e os nomes dos arquivos.")
        return pd.DataFrame()
        
    df_completo = pd.concat(lista_de_dataframes, ignore_index=True)
    
    # CORREÇÃO 2: Verificando as colunas reais ('uf' e 'focuses')
    colunas_necessarias = ['uf', 'focuses']
    if not all(col in df_completo.columns for col in colunas_necessarias):
        st.error("Os arquivos de bioma não contêm as colunas 'uf' ou 'focuses'. A análise falhou.")
        return pd.DataFrame()
        
    # Padronização: Renomeando colunas para português
    df_completo.rename(columns={'uf': 'estado', 'focuses': 'focos'}, inplace=True)
    
    df_completo.dropna(subset=['estado'], inplace=True)
    return df_completo

# --- Carrega os dados ---
df_principal = carregar_dados_biomas()

# Se o dataframe estiver vazio após a tentativa de carga, para aqui.
if df_principal.empty:
    st.stop()

# --- SIDEBAR DE FILTROS (AGORA AMBOS FUNCIONAM) ---
st.sidebar.title("Filtros")

# Filtro de Bioma
opcoes_biomas = ['Todos'] + sorted(df_principal['bioma'].unique())
bioma_selecionado = st.sidebar.selectbox("Selecione o Bioma", opcoes_biomas)

# Filtro de Estado
opcoes_estados = ['Todos'] + sorted(df_principal['estado'].unique())
estado_selecionado = st.sidebar.selectbox("Selecione o Estado (UF)", opcoes_estados)

# --- APLICAÇÃO DOS FILTROS ---
df_filtrado = df_principal.copy()

if bioma_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['bioma'] == bioma_selecionado]

if estado_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['estado'] == estado_selecionado]

# --- EXIBIÇÃO DO DASHBOARD ---
st.header(f"Exibindo dados para: {bioma_selecionado} | {estado_selecionado}")

# 1. Métricas
total_focos = df_filtrado['focos'].sum()
st.metric("Total de Focos de Queimada", f"{total_focos:,.0f}")

# 2. Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Focos por Bioma")
    focos_por_bioma = df_filtrado.groupby('bioma')['focos'].sum().sort_values(ascending=False)
    st.bar_chart(focos_por_bioma)

with col2:
    st.subheader("Top 10 Estados")
    focos_por_estado = df_filtrado.groupby('estado')['focos'].sum().nlargest(10)
    st.bar_chart(focos_por_estado)

# 3. Tabela de Dados
st.subheader("Dados Detalhados")
st.dataframe(df_filtrado)

# 4. Botão de Download
csv_para_download = df_filtrado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Exportar dados filtrados para .csv",
    data=csv_para_download,
    file_name=f"ecovision_focos_filtrados.csv",
    mime="text/csv"
)

# Botão de Logout
if st.sidebar.button("Logout"):
    st.session_state["autenticado"] = False
    st.switch_page("app.py")