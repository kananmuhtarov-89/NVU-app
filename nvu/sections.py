import pandas as pd
import streamlit as st
from nvu.cleaning import to_decade_bins

# Sütun adlarını tapmaq üçün sadə helper
def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for k in candidates:
        if k in df.columns:
            return k
    lower = {str(c).lower(): c for c in df.columns}
    for k in candidates:
        lk = str(k).lower()
        if lk in lower:
            return lower[lk]
    return None

# ---- Top cədvəlləri (UI) ----

def section_top_erizeci(df: pd.DataFrame) -> pd.DataFrame:
    col = _find_col(df, ["Ərizəçi", "Ərizəçi adı", "Applicant", "Müştəri", "Musteri"])
    if not col: return pd.DataFrame()
    N = int(st.session_state.get("param_topN_erizeci", 20))
    tbl = (
        df[col].astype(str)
        .replace({"nan": "(bilinmir)", "None": "(bilinmir)", "": "(bilinmir)"})
        .value_counts()
        .head(N)
        .reset_index()
    )
    tbl.columns = [col, "Say"]
    tbl.insert(0, "Sıra №", range(1, len(tbl) + 1))
    return tbl

def section_top_marka(df: pd.DataFrame) -> pd.DataFrame:
    col = _find_col(df, ["Marka", "Brand"])
    if not col: return pd.DataFrame()
    N = int(st.session_state.get("param_topN_marka", 20))
    tbl = (
        df[col].astype(str)
        .replace({"nan": "(bilinmir)", "None": "(bilinmir)", "": "(bilinmir)"})
        .value_counts()
        .head(N)
        .reset_index()
    )
    tbl.columns = [col, "Say"]
    tbl.insert(0, "Sıra №", range(1, len(tbl) + 1))
    return tbl

def section_top_model(df: pd.DataFrame) -> pd.DataFrame:
    col = _find_col(df, ["Model"])
    if not col: return pd.DataFrame()
    N = int(st.session_state.get("param_topN_model", 20))
    tbl = (
        df[col].astype(str)
        .replace({"nan": "(bilinmir)", "None": "(bilinmir)", "": "(bilinmir)"})
        .value_counts()
        .head(N)
        .reset_index()
    )
    tbl.columns = [col, "Say"]
    tbl.insert(0, "Sıra №", range(1, len(tbl) + 1))
    return tbl

def section_top_reng(df: pd.DataFrame) -> pd.DataFrame:
    col = _find_col(df, ["Rəng", "Reng", "Color"])
    if not col: return pd.DataFrame()
    N = int(st.session_state.get("param_topN_reng", 20))
    tbl = (
        df[col].astype(str)
        .replace({"nan": "(bilinmir)", "None": "(bilinmir)", "": "(bilinmir)"})
        .value_counts()
        .head(N)
        .reset_index()
    )
    tbl.columns = [col, "Say"]
    tbl.insert(0, "Sıra №", range(1, len(tbl) + 1))
    return tbl

# ---- 10 illik intervallar (UI) ----

def section_yas_interval(df: pd.DataFrame) -> pd.DataFrame:
    year_col = _find_col(df, ["Buraxılış ili", "İl", "Il", "İlk qeyd ili", "FirstRegYear"])
    if not year_col: 
        return pd.DataFrame(columns=["İl aralığı", "Say"])
    bins = to_decade_bins(pd.to_numeric(df[year_col], errors="coerce"))
    tbl = (
        bins[bins != "Naməlum"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    tbl.columns = ["İl aralığı", "Say"]
    tbl.insert(0, "Sıra №", range(1, len(tbl) + 1))
    return tbl
