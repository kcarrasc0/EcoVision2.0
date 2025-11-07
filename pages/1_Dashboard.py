# pages/1_Dashboard.py
import streamlit as st
import pandas as pd
import os # Usaremos para extrair o nome do bioma do arquivo

# --- GUARDIÃO DE AUTENTICAÇÃO ---
if not st.session_state.get("autenticado", False):
    st.error("Acesso negado. Por favor, faça o login primeiro.")
    st.page_link("app.py", label="Ir para a página de Login", icon="🏠")
    st.stop()
# --- FIM DO GUARDIÃO ---

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard EcoVision", layout="wide")
st.title("📊 Dashboard de Monitoramento de Queimadas")

# --- CARREGAMENTO DE DADOS ---

# !! IMPORTANTE !!
# Substitua 'SEU-USUARIO' e 'SEU-REPOSITORIO' pelo caminho real no GitHub
# O caminho deve apontar para a pasta ONDE os CSVs estão.
BASE_URL = "https://raw.githubusercontent.com/SEU-USUARIO/SEU-REPOSITORIO/main/data/" # Ajuste essa URL

# Lista dos arquivos CSV que você mostrou
nomes_biomas = [
    "amazonia",
    "caatinga",
    "cerrado",
    "mata_atlantica",
    "pampa",
    "pantanal"
]

@st.cache_data  # Cache para performance! Só carrega os dados 1 vez.
def carregar_dados_completos():
    """Carrega, une e processa todos os 6 CSVs de biomas."""
    lista_de_dataframes = []
    
    for bioma in nomes_biomas:
        url_csv = f"{BASE_URL}{bioma}.csv"
        try:
            df = pd.read_csv(url_csv)
            # Adiciona a coluna 'bioma' baseada no nome do arquivo
            df['bioma'] = bioma.replace("_", " ").title() 
            lista_de_dataframes.append(df)
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo {url_csv}: {e}")
            
    if not lista_de_dataframes:
        st.error("Nenhum dado pôde ser carregado. Verifique a URL base e os nomes dos arquivos.")
        st.stop()
        
    # Une todos os dataframes em um só
    df_completo = pd.concat(lista_de_dataframes, ignore_index=True)
    
    # *** Processamento Básico (Adicione mais se necessário) ***
    # Exemplo: Converter coluna 'data' para datetime (se existir)
    # Assumindo que você tem colunas 'estado' e 'focos' (ajuste se for diferente)
    if 'estado' not in df_completo.columns or 'focos' not in df_completo.columns:
        st.warning("Colunas 'estado' ou 'focos' não encontradas. Os filtros/gráficos podem falhar.")
        # Criando colunas de exemplo se não existirem (APENAS PARA TESTE)
        if 'estado' not in df_completo.columns:
            df_completo['estado'] = 'Estado Exemplo'
        if 'focos' not in df_completo.columns:
            df_completo['focos'] = 1
            
    # Limpeza: Remover linhas onde estado é nulo
    df_completo.dropna(subset=['estado'], inplace=True)
    
    return df_completo

# Carrega o dataframe principal
df_principal = carregar_dados_completos()


# --- SIDEBAR DE FILTROS ---
st.sidebar.title("Filtros")

# Opções para os filtros (do DataFrame principal)
opcoes_biomas = ['Todos'] + sorted(df_principal['bioma'].unique())
opcoes_estados = ['Todos'] + sorted(df_principal['estado'].unique())

bioma_selecionado = st.sidebar.selectbox("Selecione o Bioma", opcoes_biomas)
estado_selecionado = st.sidebar.selectbox("Selecione o Estado", opcoes_estados)

# --- APLICAÇÃO DOS FILTROS ---
df_filtrado = df_principal.copy()

if bioma_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['bioma'] == bioma_selecionado]

if estado_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['estado'] == estado_selecionado]


# --- EXIBIÇÃO DO DASHBOARD ---

st.header(f"Exibindo dados para: {bioma_selecionado} | {estado_selecionado}")

# 1. Métricas Principais (KPIs)
total_focos = df_filtrado['focos'].sum()
st.metric("Total de Focos de Queimada", f"{total_focos:,.0f}")

# 2. Gráfico (Ex: Focos por Bioma - se 'Todos' estiver selecionado)
if bioma_selecionado == 'Todos':
    st.subheader("Focos Totais por Bioma")
    focos_por_bioma = df_filtrado.groupby('bioma')['focos'].sum().sort_values(ascending=False)
    st.bar_chart(focos_por_bioma)

# 3. Gráfico (Ex: Focos por Estado - se 'Todos' estiver selecionado)
if estado_selecionado == 'Todos' and not df_filtrado.empty:
    st.subheader("Top 10 Estados com mais focos")
    focos_por_estado = df_filtrado.groupby('estado')['focos'].sum().nlargest(10)
    st.bar_chart(focos_por_estado)

# 4. Tabela de Dados
st.subheader("Dados Detalhados")
st.dataframe(df_filtrado)

# 5. Botão de Download (substitui a rota de API do Node.js)
csv_para_download = df_filtrado.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Exportar dados filtrados para .csv",
    data=csv_para_download,
    file_name=f"ecovision_focos_{bioma_selecionado}_{estado_selecionado}.csv",
    mime="text/csv",
    key='download-csv'
)

# Botão de Logout
if st.sidebar