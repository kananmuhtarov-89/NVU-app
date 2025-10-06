import streamlit as st

st.title("📊 Təsnifatlar üzrə")

st.session_state.setdefault("toggle_birlestir_tesnifat", True)
st.session_state.setdefault("toggle_meblegleri_hesabla", True)

st.session_state["toggle_birlestir_tesnifat"] = st.toggle(
    "Təsnifatları birləşdir (M1+M1G…)", st.session_state["toggle_birlestir_tesnifat"]
)
st.session_state["toggle_meblegleri_hesabla"] = st.toggle(
    "Məbləğləri hesabla (Cəmi AZN)", st.session_state["toggle_meblegleri_hesabla"]
)
