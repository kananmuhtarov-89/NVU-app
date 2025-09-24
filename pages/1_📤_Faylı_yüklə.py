import streamlit as st
import pandas as pd
import numpy as np

# --- Excel oxuyucu (asılılıq olmadan) ---
def load_excel(file):
    return pd.read_excel(file, dtype=object, engine="openpyxl")

st.title("1) Faylı yüklə / Təmizlə")

AZ_MONTHS = {1:"Yanvar",2:"Fevral",3:"Mart",4:"Aprel",5:"May",6:"İyun",7:"İyul",8:"Avqust",9:"Sentyabr",10:"Oktyabr",11:"Noyabr",12:"Dekabr"}

# ---------- Köməkçilər ----------
def norm(s: str) -> str:
    s = str(s).strip().lower()
    trans_from = "ıiəeöoüuşıçcğg"
    trans_to   = "iieeoouussccgg"
    tbl = str.maketrans({src: dst for src, dst in zip(trans_from, trans_to)})
    return s.translate(tbl)

def robust_to_datetime(series: pd.Series) -> pd.Series:
    s = series.copy()
    s_str = s.astype(str).str.replace("\u00a0", " ", regex=False).str.strip()
    dt = pd.to_datetime(s_str, errors="coerce", dayfirst=True, infer_datetime_format=True)
    mask_nat = dt.isna()
    if mask_nat.any():
        s_num = pd.to_numeric(s_str.where(mask_nat), errors="coerce")
        valid = s_num.between(20000, 50000, inclusive="both")  # Excel serial (~1955..2090)
        if valid.any():
            base = pd.Timestamp("1899-12-30")
            dt2 = base + pd.to_timedelta(s_num[valid], unit="D")
            dt.loc[valid.index.intersection(dt2.index)] = dt2
    return dt

# ---- Sənin verdiyin başlıqlar (tam uyğunluq ilə axtarırıq) ----
TITLE_R  = "Müraciət üzrə son əməliyyat tarixi"
TITLE_AB = "Təhvil-təslim üzrə son əməliyyat"
TITLE_AF = "Təsdiqedici sənəd üzrə son əməliyyat"
NV_COL   = "NV qeydiyyat nömrəsi"  # J sütunu

def find_column_exact(df: pd.DataFrame, title: str):
    # tam başlıq uyğunluğu, həm də normalize edilmiş
    titles = [title, norm(title)]
    for c in df.columns:
        if c == title or norm(c) == titles[1]:
            return c
    return None

uploaded = st.file_uploader("Excel (.xlsx/.xls) yüklə", type=["xlsx","xls"])

if uploaded:
    # 1) Load (RAW)
    df_raw = load_excel(uploaded)
    st.write("Sətir sayı (xam):", len(df_raw))

    # 2) Lazımi sütunları tapmaq
    col_R  = find_column_exact(df_raw, TITLE_R)
    col_AB = find_column_exact(df_raw, TITLE_AB)
    col_AF = find_column_exact(df_raw, TITLE_AF)

    if col_R is None or NV_COL not in df_raw.columns:
        st.error("Zəruri sütun tapılmadı. R və ya NV sütunu yoxdur.")
        st.stop()

    # 3) XAM cədvəldə tarixləri hesabla
    df_raw["dt_R"]  = robust_to_datetime(df_raw[col_R])
    if col_AB: df_raw["dt_AB"] = robust_to_datetime(df_raw[col_AB])
    else:      df_raw["dt_AB"] = pd.NaT
    if col_AF: df_raw["dt_AF"] = robust_to_datetime(df_raw[col_AF])
    else:      df_raw["dt_AF"] = pd.NaT

    # 4) NV üzrə **ən yeni R** dedup (fallback YOXDUR)
    df_sorted = df_raw.sort_values("dt_R", ascending=False, na_position="last")
    df = df_sorted.drop_duplicates(subset=[NV_COL], keep="first").copy()

    # 5) Il/Ay sahələri
    for key in ["R","AB","AF"]:
        dt = df.get(f"dt_{key}")
        if dt is None: 
            continue
        df[f"il_{key}"]     = dt.dt.year
        df[f"ay_no_{key}"]  = dt.dt.month
        df[f"ay_ad_{key}"]  = df[f"ay_no_{key}"].map(AZ_MONTHS)

    # 6) KOMPOZİT (max R/AB/AF) – lazımdırsa filtrdə istifadə üçün
    dt_cols = [c for c in ["dt_R","dt_AB","dt_AF"] if c in df.columns]
    if dt_cols:
        for c in dt_cols:
            df[c] = pd.to_datetime(df[c], errors="coerce")
        df["dt_KOMPOZIT"] = df[dt_cols].max(axis=1)
    else:
        df["dt_KOMPOZIT"] = pd.NaT

    # 7) Coverage və Min/Max
    coverage, minmax = {}, {}
    def cov_min_max(colname: str):
        s = df[colname]
        cov = (100.0 * s.notna().sum() / len(df)) if len(df) else 0.0
        mn, mx = s.min(), s.max()
        return round(cov,1), (mn.strftime("%Y-%m-%d") if pd.notna(mn) else "—"), (mx.strftime("%Y-%m-%d") if pd.notna(mx) else "—")

    coverage["R"],  r_min,  r_max  = cov_min_max("dt_R")
    coverage["AB"], ab_min, ab_max = cov_min_max("dt_AB")
    coverage["AF"], af_min, af_max = cov_min_max("dt_AF")
    coverage["KOMPOZIT"], k_min, k_max = cov_min_max("dt_KOMPOZIT")

    minmax = {
        "R": {"min": r_min, "max": r_max},
        "AB": {"min": ab_min, "max": ab_max},
        "AF": {"min": af_min, "max": af_max},
        "KOMPOZIT": {"min": k_min, "max": k_max},
    }

    # 8) Session state – digər səhifələr üçün
    st.session_state["df_clean_full"] = df.copy()
    st.session_state["df_clean"] = df.copy()
    st.session_state["coverage_by_source"] = coverage
    st.session_state["minmax_by_source"] = minmax
    st.session_state["active_source_key"] = "R"
    st.session_state["filter_initialized"] = False

    # 9) Yekun cədvəl (əhatə və min/max)
    st.success(f"Təmizləndi. Sətirlər (dedup): {len(df)} | Unikal NV: {df[NV_COL].nunique()}")
    st.caption("Tarix sütunlarının əhatəsi və min/max dəyərləri:")

    rows = [
        {"Mənbə": "R — Müraciət üzrə son əməliyyat tarixi", "Sütun (ad)": col_R,  "Dolu %": coverage["R"],  "Min": r_min,  "Max": r_max},
        {"Mənbə": "AB — Təhvil-təslim üzrə son əməliyyat",    "Sütun (ad)": col_AB, "Dolu %": coverage["AB"], "Min": ab_min, "Max": ab_max},
        {"Mənbə": "AF — Təsdiqedici sənəd üzrə son əməliyyat", "Sütun (ad)": col_AF, "Dolu %": coverage["AF"], "Min": af_min, "Max": af_max},
        {"Mənbə": "KOMPOZİT — ən son əməliyyat",              "Sütun (ad)": "max(R,AB,AF)", "Dolu %": coverage["KOMPOZIT"], "Min": k_min, "Max": k_max},
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # 10) Preview
    st.dataframe(df[[NV_COL, "dt_R","dt_AB","dt_AF"]].head(50), use_container_width=True)

else:
    st.info("Fayl yükləyin.")
