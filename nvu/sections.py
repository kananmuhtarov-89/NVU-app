import pandas as pd
import streamlit as st
from nvu.cleaning import to_decade_bins

# -------------------------
# NVU TOP və CƏDVƏL BÖLMƏLƏRİ
# -------------------------

def section_top_erizeci(df):
    N = st.session_state.get("param_topN_erizeci", 20)
    tbl = (
        df.groupby("Ərizəçi adı")
          .size()
          .reset_index(name="Say")
          .sort_values("Say", ascending=False)
          .head(N)
    )
    tbl.insert(0, "Sıra №", range(1, len(tbl) + 1))
    return tbl

def section_top_marka(df):
    N = st.session_state.get("param_topN_marka", 20)
    tbl = (
        df.groupby("Marka")
          .size()
          .reset_index(name="Say")
          .sort_values("Say", ascending=False)
          .head(N)
    )
    tbl.insert(0, "Sıra №", range(1, len(tbl) + 1))
    return tbl

def section_top_model(df):
    N = st.session_state.get("param_topN_model", 20)
    tbl = (
        df.groupby("Model")
          .size()
          .reset_index(name="Say")
          .sort_values("Say", ascending=False)
          .head(N)
    )
    tbl.insert(0, "Sıra №", range(1, len(tbl) + 1))
    return tbl

def section_top_reng(df):
    N = st.session_state.get("param_topN_reng", 20)
    tbl = (
        df.groupby("Rəng")
          .size()
          .reset_index(name="Say")
          .sort_values("Say", ascending=False)
          .head(N)
    )
    tbl.insert(0, "Sıra №", range(1, len(tbl) + 1))
    return tbl

def section_yas_interval(df):
    if "Buraxılış ili" not in df.columns:
        return pd.DataFrame()
    tbl = to_decade_bins(df["Buraxılış ili"]).value_counts().reset_index()
    tbl.columns = ["İl aralığı", "Say"]
    tbl = tbl.sort_values("İl aralığı")
    return tbl
