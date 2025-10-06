# pages/0_Parametrlər.py — v3
import streamlit as st

st.title("Parametrlər")

def _set_default(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

# Top-N parametrləri
_set_default("param_topN_erizeci", 10)
_set_default("param_topN_marka",   10)
_set_default("param_topN_model",   10)
_set_default("param_topN_reng",    10)

# Boş sətrləri daxil et? (default: Xeyr)
_set_default("param_include_blanks", False)

c1, c2 = st.columns(2)
with c1:
    st.session_state["param_topN_erizeci"] = st.number_input("Top-N (Ərizəçi)", 3, 100, st.session_state["param_topN_erizeci"])
    st.session_state["param_topN_marka"]   = st.number_input("Top-N (Marka)",   3, 100, st.session_state["param_topN_marka"])
with c2:
    st.session_state["param_topN_model"]   = st.number_input("Top-N (Model)",   3, 100, st.session_state["param_topN_model"])
    st.session_state["param_topN_reng"]    = st.number_input("Top-N (Rəng)",    3, 100, st.session_state["param_topN_reng"])

st.toggle("Boş status sətrlərini də daxil et (tövsiyə olunmur)", key="param_include_blanks")

st.success("Parametrlər yadda saxlanıldı. Export bu dəyərləri istifadə edəcək.")
