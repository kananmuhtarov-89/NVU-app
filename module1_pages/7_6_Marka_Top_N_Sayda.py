import streamlit as st
from nvu.sections import section6_top20_marka

df_clean = st.session_state.get("df_clean")

if df_clean is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()

TOP_MARKA = int(st.session_state.get("param_topN_marka", 20))

st.title(f"6) Top-{TOP_MARKA} Marka")
st.dataframe(
    section6_top20_marka(df_clean, "Marka", n=TOP_MARKA),
    use_container_width=True
)
