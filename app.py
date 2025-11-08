# app.py
import streamlit as st

st.set_page_config(
    page_title="EcoVision Login",
    page_icon="🌿",
    layout="centered"
)

def check_password():
    """Valida a senha e atualiza o st.session_state."""
    if (
        st.session_state.get("username") == st.secrets["USUARIO_ESTATICO"] and
        st.session_state.get("password") == st.secrets["SENHA_ESTATICA"]
    ):
        # Se correto, marca como autenticado
        st.session_state["autenticado"] = True
        
        # Limpa as senhas da sessão por segurança
        if "password" in st.session_state:
            del st.session_state["password"]
        if "username" in st.session_state:
            del st.session_state["username"]
            
    else:
        st.session_state["autenticado"] = False
        st.error("Usuário ou senha incorreta")

# --- Lógica Principal da Página ---

# 1. Se o usuário já está logado, redireciona para o dashboard
if st.session_state.get("autenticado", False):
    st.switch_page("pages/1_Dashboard.py")

# 2. Se não está logado, mostra o formulário de login
st.title("🌿 EcoVision Login")
st.write("Por favor, insira suas credenciais para acessar o sistema. Usuario e senha: cop30")

st.text_input("Usuário", key="username")
st.text_input("Senha", type="password", key="password")

st.button("Entrar", on_click=check_password)