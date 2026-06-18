import streamlit as st
from nvu.sections import section7_top20_model
#from nvu.sections import section7_topn_model

df_clean = st.session_state.get("df_clean")

if df_clean is None:
    st.warning("İlk öncə **1) Faylı yüklə** səhifəsində Excel faylı yükləyin.")
    st.stop()

TOP_MODEL = int(st.session_state.get("param_topN_model", 20))

st.title(f"7) Top-{TOP_MODEL} Model (uyğunlaşdırılmış)")

st.dataframe(
    section7_top20_model(df_clean, "Marka", "Model", n=TOP_MODEL),
    use_container_width=True
)
