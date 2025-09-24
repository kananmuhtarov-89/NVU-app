import streamlit as st
import pandas as pd
import numpy as np

# --- Excel oxuyucu ---
def load_excel(file):
    return pd.read_excel(file, dtype=object, engine="openpyxl")

st.title("1) Faylı yüklə / Təmizlə")

AZ_MONTHS = {1:"Yanvar",2:"Fevral",3:"Mart",4:"Aprel",5:"May",6:"İyun",7:"İyul",8:"Avqust",9:"Sentyabr",10:"Oktyabr",11:"Noyabr",12:"Dekabr"}

# ---------- Helpers ----------
def norm(s: str) -> str:
    s = str(s).strip().lower()
    trans_from = "ıiəeöoüuşıçcğg"
    trans_to   = "iieeoouussccgg"
    tbl = str.maketrans({src: dst for src, dst in zip(trans_from, trans_to)})
    return s.translate(tbl)

def robust_to_datetime(series: pd.Series) -> pd.Series:
    """
    1) ISO 'YYYY-MM-DD HH:MM:SS' (sənin R formatın) STRİCT
    2) General parser (dayfirst=True)
    3) Excel serial fallback
    """
    s = series.copy()
    s_str = s.astype(str).str.replace("\u00a0", " ", regex=False).str.strip()

    # strict ISO datetime first (R üçün əsas)
    dt = pd.to_datetime(s_str, format="%Y-%m-%d %H:%M:%S", errors="coerce")

    # generic fallback
    m = dt.isna()
    if m.any():
        dt2 = pd.to_datetime(s_str[m], errors="coerce", dayfirst=True, infer_datetime_format=True)
        dt.loc[m] = dt2

    # Excel serial fallback
    m = dt.isna()
    if m.any():
        s_num = pd.to_numeric(s_str[m], errors="coerce")
        valid = s_num.between(20000, 50000, inclusive="both")
        if valid.any():
            base = pd.Timestamp("1899-12-30")
            dt.loc[valid.index] = base + pd.to_timedelta(s_num[valid], unit="D")
    return dt

# ---- Dəqiq başlıqlar ----
TITLE_R  = "Müraciət üzrə son əməliyyat tarixi"
TITLE_AB = "Təhvil-təslim üzrə son əməliyyat"
TITLE_AF = "Təsdiqedici sənəd üzrə son əməliyyat"
NV_COL   = "NV qeydiyyat nömrəsi"  # J sütunu

def find_column_exact(df: pd.DataFrame, title: str):
    want_norm = norm(title)
    for c in df.columns:
        if c == title or norm(c) == want_norm:
            return c
    return None

uploaded = st.file_uploader("Excel (.xlsx/.xls) yüklə", type=["xlsx","xls"])

if uploaded:
    # 1) RAW
    df_raw = load_excel(uploaded)
    st.write("Sətir sayı (xam):", len(df_raw))

    # 2) Sütunlar
    col_R  = find_column_exact(df_raw, TITLE_R)
    col_AB = find_column_exact(df_raw, TITLE_AB)
    col_AF = find_column_exact(df_raw, TITLE_AF)

    if col_R is None or NV_COL not in df_raw.columns:
        st.error("Zəruri sütun tapılmadı (R və ya NV).")
        st.stop()

    # 3) RAW-da tarixləri qur
    df_raw["dt_R"]  = robust_to_datetime(df_raw[col_R])
    if col_AB: df_raw["dt_AB"] = robust_to_datetime(df_raw[col_AB])
    else:      df_raw["dt_AB"] = pd.NaT
    if col_AF: df_raw["dt_AF"] = robust_to_datetime(df_raw[col_AF])
    else:      df_raw["dt_AF"] = pd.NaT

    # 4) NV üzrə **ən yeni R** (fallbacks YOXDUR)
    df_sorted = df_raw.sort_values("dt_R", ascending=False, na_position="last")
    df = df_sorted.drop_duplicates(subset=[NV_COL], keep="first").copy()

    # 5) İl/Ay sahələri
    for key in ["R","AB","AF"]:
        dt = df.get(f"dt_{key}")
        if dt is None: 
            continue
        df[f"il_{key}"]     = dt.dt.year
        df[f"ay_no_{key}"]  = dt.dt.month
        df[f"ay_ad_{key}"]  = df[f"ay_no_{key}"].map(AZ_MONTHS)

    # 6) KOMPOZİT (max R/AB/AF)
    dt_cols = [c for c in ["dt_R","dt_AB","dt_AF"] if c in df.columns]
    if dt_cols:
        for c in dt_cols:
            df[c] = pd.to_datetime(df[c], errors="coerce")
        df["dt_KOMPOZIT"] = df[dt_cols].max(axis=1)
    else:
        df["dt_KOMPOZIT"] = pd.NaT

    # 7) Coverage + min/max
    def cov_min_max(colname: str):
        s = df[colname]
        cov = (100.0 * s.notna().sum() / len(df)) if len(df) else 0.0
        mn, mx = s.min(), s.max()
        return round(cov,1), (mn.strftime("%Y-%m-%d") if pd.notna(mn) else "—"), (mx.strftime("%Y-%m-%d") if pd.notna(mx) else "—")

    coverage, minmax = {}, {}
    coverage["R"],  r_min,  r_max  = cov_min_max
