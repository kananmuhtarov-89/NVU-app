import streamlit as st, os
from nvu.sections import *
from nvu.regions import load_region_map
df_clean = st.session_state.get("df_clean")
if df_clean is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()
region_map = load_region_map(os.path.join(os.path.dirname(__file__), "..", "data", "az_region_codes.json"))

st.title("5) Top-50 Ərizəçi")
tbl = section5_top50_erizeci(df_clean, "Ərizəçinin tam adı")
st.subheader("Top-20")
st.dataframe(tbl.head(20), use_container_width=True)
rest = tbl.iloc[20:]
if len(rest)>0:
    with st.expander(f"Daha çox (21–{len(tbl)})"):
        st.dataframe(rest, use_container_width=True)
