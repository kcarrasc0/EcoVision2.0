# pages/2_Reconhecimento_de_Fogo.py
import streamlit as st
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
import av
from ultralytics import YOLO

# --- GUARDIÃO DE AUTENTICAÇÃO ---
if not st.session_state.get("autenticado", False):
    st.error("Acesso negado. Por favor, faça o login primeiro.")
    st.page_link("app.py", label="Ir para a página de Login", icon="🏠")
    st.stop()
# --- FIM DO GUARDIÃO ---

st.set_page_config(page_title="Reconhecimento com IA", layout="wide")
st.title("🔥 Reconhecimento de Fogo com Deep Learning (YOLOv8)")
st.warning(
    "Este é um detector de objetos profissional. "
    "Atualmente, ele usa um modelo padrão (yolov8n.pt) para provar que a câmera e a IA funcionam."
)

# --- CARREGAR O MODELO YOLO ---
@st.cache_resource
def load_yolo_model():
    model = YOLO("models/fire_model.pt") # <-- MUDANÇA
    return model

try:
    model = load_yolo_model()
    st.info("Modelo YOLOv8 padrão ('yolov8n.pt') carregado com sucesso. Ele detectará objetos comuns.")
except Exception as e:
    st.error(f"Erro ao carregar o modelo YOLO: {e}")
    st.stop()


def process_frame(frame: av.VideoFrame) -> av.VideoFrame:
    """Função de callback para processar cada frame com YOLO."""
    
    img = frame.to_ndarray(format="bgr24")
    
    # --- OTIMIZAÇÃO 1 ---
    # Instruímos o YOLO a rodar em um tamanho menor (imgsz=320)
    # e com uma confiança menor (conf=0.4), o que é muito mais rápido.
    results = model(img, stream=True, imgsz=320, conf=0.4) 
    
    # Desenha as caixas delimitadoras nos resultados
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            
            label = f"{model.names[cls]} {conf:.2f}"
            
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
    return av.VideoFrame.from_ndarray(img, format="bgr24")

# --- Inicia o componente de webcam ---
rtc_config = RTCConfiguration({
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})

webrtc_streamer(
    key="yolo_detector",
    video_frame_callback=process_frame,
    rtc_configuration=rtc_config,
    # --- OTIMIZAÇÃO 2 ---
    # Pedimos uma resolução menor da câmera para processar mais rápido
    media_stream_constraints={
        "video": {
            "width": {"ideal": 640},
            "height": {"ideal": 480}
        },
        "audio": False
    },
    async_processing=True,
)

# Botão de Logout
if st.sidebar.button("Logout"):
    st.session_state["autenticado"] = False
    st.switch_page("app.py")