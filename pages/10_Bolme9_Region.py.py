import streamlit as st, os
from nvu.sections import *
from nvu.regions import load_region_map
df_clean = st.session_state.get("df_clean")
if df_clean is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()
region_map = load_region_map(os.path.join(os.path.dirname(__file__), "..", "data", "az_region_codes.json"))

st.title("9) Region paylanması (NV nömrəsinə görə)")
tbl = section9_region_counts(df_clean, "NV qeydiyyat nömrəsi", region_map).sort_values("Say", ascending=False)
st.subheader("Top-10")
st.dataframe(tbl.head(10), use_container_width=True)
rest = tbl.iloc[10:]
if len(rest)>0:
    with st.expander(f"Daha çox (11–{len(tbl)})"):
        st.dataframe(rest, use_container_width=True)
