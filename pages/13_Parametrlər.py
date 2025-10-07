# pages/13_Parametrlər.py
import streamlit as st
from nvu.settings import get_settings, set_settings, download_settings_button, upload_settings

st.title("Parametrlər")

# 1) Konfiqurasiyanı yüklə
cfg = get_settings()

# 2) Top-N dəyərləri (UI)
st.subheader("2) Top-N dəyərləri")
c1, c2, c3, c4 = st.columns(4)
cfg["topN"]["applicant"] = c1.number_input("Top-N Ərizəçi", min_value=1, max_value=200, value=cfg["topN"]["applicant"], step=1)
cfg["topN"]["brand"]     = c2.number_input("Top-N Marka",    min_value=1, max_value=200, value=cfg["topN"]["brand"],     step=1)
cfg["topN"]["model"]     = c3.number_input("Top-N Model",    min_value=1, max_value=200, value=cfg["topN"]["model"],     step=1)
cfg["topN"]["color"]     = c4.number_input("Top-N Rəng",     min_value=1, max_value=200, value=cfg["topN"]["color"],     step=1)

# --- Sync Top-N to session_state for Export/Other pages (minimal patch) ---
st.session_state["param_topN_erizeci"] = int(cfg["topN"]["applicant"])
st.session_state["param_topN_marka"]   = int(cfg["topN"]["brand"])
st.session_state["param_topN_model"]   = int(cfg["topN"]["model"])
st.session_state["param_topN_reng"]    = int(cfg["topN"]["color"])


# 3) Top-N dəyərlərini sessiyaya da yaz (export üçün dinamik başlıq)
st.session_state["top_counts_meta"] = {
    "erizeci_N": int(cfg["topN"]["applicant"]),
    "marka_N":   int(cfg["topN"]["brand"]),
    "model_N":   int(cfg["topN"]["model"]),
    "reng_N":    int(cfg["topN"]["color"]),
}

st.info("Top-N dəyərləri yadda saxlanıldı və sessiyaya yazıldı: "
        f"Ərizəçi={cfg['topN']['applicant']}, Marka={cfg['topN']['brand']}, "
        f"Model={cfg['topN']['model']}, Rəng={cfg['topN']['color']}")

# 4) Parametrləri yadda saxla / yüklə (opsional)
st.divider()
if st.button("Parametrləri yadda saxla"):
    set_settings(cfg)
    st.success("Parametrlər yadda saxlandı.")

c5, c6 = st.columns(2)
with c5:
    download_settings_button()
with c6:
    upload_settings()
