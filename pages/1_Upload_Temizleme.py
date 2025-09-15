import streamlit as st, os
import pandas as pd
from nvu.cleaning import load_excel, dedup_dataframe
st.title("1) Yüklə / Təmizlə")
uploaded = st.file_uploader("Excel (.xlsx/.xls) yüklə", type=["xlsx","xls"])
if uploaded:
    df = load_excel(uploaded)
    st.write("Sətir sayı (xam):", len(df))
    df_clean = dedup_dataframe(df, "Təhvil aktının seriya nömrəsi", "Təsdiqedici sənədin seriyası", "NV qeydiyyat nömrəsi")
    st.success(f"Təmizləndi. Sətirlər (təmiz): {len(df_clean)}")
    st.session_state["df_clean"] = df_clean
    st.session_state["source_filename"] = uploaded.name
    st.dataframe(df_clean.head(50), use_container_width=True)
else:
    st.info("Fayl yükləyin.")
