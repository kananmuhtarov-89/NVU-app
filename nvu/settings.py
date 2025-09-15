
import json, os, streamlit as st

DEFAULTS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "default_settings.json")

CANON_COLS = [
    "Utilizatorun adı","Təsnifat","Təsdiqedici sənədin seriyası","Təhvil aktının seriya nömrəsi",
    "Ərizəçinin tam adı","Marka","Model","Rəng","NV qeydiyyat nömrəsi","Buraxılış ili",
    "Təsdiq edici sənədin statusu","Təhvil-təslim sənədinin statusu"
]

def load_defaults() -> dict:
    with open(DEFAULTS_PATH,"r",encoding="utf-8") as f:
        return json.load(f)

def get_settings() -> dict:
    if "settings" not in st.session_state:
        st.session_state["settings"] = load_defaults()
    return st.session_state["settings"]

def set_settings(cfg: dict):
    st.session_state["settings"] = cfg

def download_settings_button(filename="app_settings.json"):
    cfg = get_settings()
    st.download_button("Parametrləri yüklə (JSON)", data=json.dumps(cfg, ensure_ascii=False, indent=2).encode("utf-8"),
                       file_name=filename, mime="application/json")

def upload_settings():
    uploaded = st.file_uploader("Parametrləri yüklə (JSON)", type=["json"], key="settings_uploader")
    if uploaded:
        try:
            cfg = json.load(uploaded)
            set_settings(cfg)
            st.success("Parametrlər yeniləndi.")
        except Exception as e:
            st.error(f"Parametrlər oxunmadı: {e}")
