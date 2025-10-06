import streamlit as st
import pandas as pd
from nvu.export import build_report

st.title("📥 Faylı endir")

uploaded = st.file_uploader("Excel faylı yüklə", type=["xlsx", "xls", "csv"])
if uploaded:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    st.success(f"Yükləndi: {uploaded.name}")
    st.dataframe(df.head())

    possible_status_cols = [
        "Təsdiqedici sənədin statusu",
        "Təhvil-təslim sənədinin statusu",
        "Təsdiq edici sənədin statusu",
        "Təhvil təslim statusu",
    ]
    status_cols = [c for c in possible_status_cols if c in df.columns]

    report = build_report(df, st.session_state, status_cols=status_cols)

    st.write("📊 Emal edilmiş məlumat:")
    st.dataframe(report["year_bins"].value_counts().reset_index())
