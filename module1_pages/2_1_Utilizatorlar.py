import streamlit as st, os
from nvu.sections import *
from nvu.regions import load_region_map
df_clean = st.session_state.get("df_clean")
if df_clean is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()
region_map = load_region_map(os.path.join(os.path.dirname(__file__), "..", "data", "az_region_codes.json"))

st.title("1) Utilizatorlar üzrə qəbul edilən NV sayları")
st.dataframe(section1_utilizator(df_clean, "Utilizatorun adı", "NV qeydiyyat nömrəsi"), use_container_width=True)
