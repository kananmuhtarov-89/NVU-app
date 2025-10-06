# pages/2_Təsnifatlar_üzrə.py — v3
import streamlit as st

st.title("Təsnifatlar üzrə")

def _set_default(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

# default ON
_set_default("toggle_birlestir_tesnifat", True)
_set_default("toggle_meblegleri_hesabla", True)

st.session_state["toggle_birlestir_tesnifat"] = st.toggle(
    "Təsnifatları birləşdir (M1+M1G…)", value=st.session_state["toggle_birlestir_tesnifat"]
)
st.session_state["toggle_meblegleri_hesabla"] = st.toggle(
    "Məbləğləri hesabla (Cəmi AZN)", value=st.session_state["toggle_meblegleri_hesabla"]
)

st.caption("Seçimlər sessiyada saxlanılır və Export çıxışında eyni şəkildə tətbiq olunur.")
