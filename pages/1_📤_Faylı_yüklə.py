import streamlit as st
import pandas as pd
import numpy as np

# Sənin util-larını istifadə et; import alınmasa fallback işləsin
try:
    from nvu.cleaning import load_excel, dedup_dataframe
except Exception:
    def load_excel(file):
        return pd.read_excel(file, dtype=object, engine="openpyxl")
    def dedup_dataframe(df, *cols, keep="first"):
        cols = [c for c in cols if c in df.columns]
        return df.drop_duplicates(subset=cols, keep=keep) if cols else df.drop_duplicates(keep=keep)

st.title("1) Faylı yüklə / Təmizlə")

AZ_MONTHS = {1:"Yanvar",2:"Fevral",3:"Mart",4:"Aprel",5:"May",6:"İyun",7:"İyul",8:"Avqust",9:"Sentyabr",10:"Oktyabr",11:"Noyabr",12:"Dekabr"}

# ---- Köməkçilər
def col_letter_to_index(letter: str) -> int:
    letter = letter.strip().upper()
    val = 0
    for ch in letter:
        if not ("A" <= ch <= "Z"):
            return -1
        val = val * 26 + (ord(ch) - 64)
    return val - 1

def get_column_by_letter(df: pd.DataFrame, letter: str):
    idx = col_letter_to_index(letter)
    return df.columns[idx] if 0 <= idx < len(df.columns) else None

def norm(s: str) -> str:
    s = str(s).lower()
    tr = str.maketrans("ıəöüşçğ", "ieouscg")
    return s.translate(tr)

def find_by_keywords(df: pd.DataFrame, tokens):
    for c in df.columns:
        n = norm(c)
        if all(t in n for t in tokens):
            return c
    return None

def robust_to_datetime(series: pd.Series) -> pd.Series:
    s = series.copy()
    s_str = s.astype(str).str.replace("\u00a0", " ", regex=False).str.strip()
    dt = pd.to_datetime(s_str, errors="coerce", dayfirst=True, infer_datetime_format=True)
    mask_nat = dt.isna()
    if mask_nat.any():
        s_num = pd.to_numeric(s_str.where(mask_nat), errors="coerce")
        valid = s_num.between(20000, 50000, inclusive="both")  # 1955..2090 aralığı
        if valid.any():
            base = pd.Timestamp("1899-12-30")  # Excel 1900 sistemi
            dt2 = base + pd.to_timedelta(s_num[valid], unit="D")
            dt.loc[valid.index.intersection(dt2.index)] = dt2
    return dt

SOURCES = {
    "R":  {"letter": "R",  "label": "Müraciət üzrə son əməliyyat tarixi", "kw": ["murac", "emel", "tarix"]},
    "W":  {"letter": "W",  "label": "İcra sənədi üzrə son əməliyyat",     "kw": ["icra", "tarix"]},
    "AB": {"letter": "AB", "label": "Təhvil-təslim üzrə son əməliyyat",     "kw": ["tehvil", "teslim", "tarix"]},
    "AF": {"letter": "AF", "label": "Təsdiqedici sənəd üzrə son əməliyyat", "kw": ["tesdiq", "sened", "tarix"]},
    "AM": {"letter": "AM", "label": "Birdəfəlik ödəniş sənədinin son əməliyyat tarixi", "kw": ["odenis", "tarix"]},
}

uploaded = st.file_uploader("Excel (.xlsx/.xls) yüklə", type=["xlsx","xls"])

if uploaded:
    # 1) Yüklə
    df_raw = load_excel(uploaded)
    st.write("Sətir sayı (xam):", len(df_raw))

    # 2) Dublikatları təmizlə
    df = dedup_dataframe(
        df_raw,
        "Təhvil aktının seriya nömrəsi",
        "Təsdiqedici sənədin seriyası",
        "NV qeydiyyat nömrəsi",
    ).copy()

    # 3) Mənbə sütunlarını HƏRFƏ görə tap → coverage aşağıdırsa BAŞLIĞA görə fallback et
    coverage, minmax, resolved_cols = {}, {}, {}

    for key, meta in SOURCES.items():
        colname = get_column_by_letter(df, meta["letter"])
        # Birinci cəhd (hərfə görə)
        dt = robust_to_datetime(df[colname]) if colname is not None else pd.Series(pd.NaT, index=df.index)
        cov = (100.0 * dt.notna().sum() / len(df)) if len(df) else 0.0

        # Fallback: coverage ≈ 0% və ya sütun tapılmadısa, başlıq sözlərinə görə axtar
        if (colname is None or cov < 1.0):
            by_kw = find_by_keywords(df, meta["kw"])
            if by_kw and by_kw != colname:
                colname = by_kw
                dt = robust_to_datetime(df[colname])
                cov = (100.0 * dt.notna().sum() / len(df)) if len(df) else 0.0

        resolved_cols[key] = colname

        # Yekun sahələri doldur
        if colname is None:
            df[f"dt_{key}"] = pd.NaT
            df[f"il_{key}"] = np.nan
            df[f"ay_no_{key}"] = np.nan
            df[f"ay_ad_{key}"] = np.nan
            coverage[key] = 0.0
            minmax[key] = {"min": "—", "max": "—"}
        else:
            df[f"dt_{key}"] = dt
            df[f"il_{key}"] = dt.dt.year
            df[f"ay_no_{key}"] = dt.dt.month
            df[f"ay_ad_{key}"] = df[f"ay_no_{key}"].map(AZ_MONTHS)

            coverage[key] = cov
            min_d, max_d = dt.min(), dt.max()
            minmax[key] = {
                "min": (min_d.strftime("%Y-%m-%d") if pd.notna(min_d) else "—"),
                "max": (max_d.strftime("%Y-%m-%d") if pd.notna(max_d) else "—"),
            }

    # 4) KOMPOZIT — sətir üzrə max(dt_R, dt_W, dt_AB, dt_AF, dt_AM)
    dt_cols = [c for c in ["dt_R", "dt_W", "dt_AB", "dt_AF", "dt_AM"] if c in df.columns]
    if dt_cols:
        for c in dt_cols:
            df[c] = pd.to_datetime(df[c], errors="coerce")
        df["dt_KOMPOZIT"] = df[dt_cols].max(axis=1)
    else:
        df["dt_KOMPOZIT"] = pd.NaT

    ok = df["dt_KOMPOZIT"].notna().sum()
    coverage["KOMPOZIT"] = (100.0 * ok / len(df)) if len(df) else 0.0
    min_d = df["dt_KOMPOZIT"].min(); max_d = df["dt_KOMPOZIT"].max()
    minmax["KOMPOZIT"] = {
        "min": (min_d.strftime("%Y-%m-%d") if pd.notna(min_d) else "—"),
        "max": (max_d.strftime("%Y-%m-%d") if pd.notna(max_d) else "—"),
    }

    # 5) Session state
    st.session_state["df_clean_full"] = df.copy()
    st.session_state["df_clean"] = df.copy()
    st.session_state["coverage_by_source"] = coverage
    st.session_state["minmax_by_source"] = minmax
    st.session_state["active_source_key"] = "R"
    st.session_state["filter_initialized"] = False

    # 6) Özet cədvəl (coverage / min-max)
    st.success(f"Təmizləndi. Sətirlər (təmiz): {len(df)}")
    st.caption("Tarix sütunlarının əhatəsi və min/max dəyərləri:")

    cov_rows = []
    for k, meta in SOURCES.items():
        cov_rows.append({
            "Mənbə": f"{k} — {meta['label']}",
            "Sütun (hərf)": meta["letter"],
            "Sütun (ad)": resolved_cols.get(k) or "tapılmadı",
            "Dolu %": round(st.session_state['coverage_by_source'][k], 1),
            "Min": st.session_state['minmax_by_source'][k]["min"],
            "Max": st.session_state['minmax_by_source'][k]["max"],
        })
    cov_rows.append({
        "Mənbə": "KOMPOZİT — ən son əməliyyat",
        "Sütun (hərf)": "-",
        "Sütun (ad)": "max(dt_R, dt_W, dt_AB, dt_AF, dt_AM)",
        "Dolu %": round(st.session_state["coverage_by_source"].get("KOMPOZIT", 0.0), 1),
        "Min": st.session_state["minmax_by_source"]["KOMPOZIT"]["min"],
        "Max": st.session_state["minmax_by_source"]["KOMPOZIT"]["max"],
    })
    st.dataframe(pd.DataFrame(cov_rows), use_container_width=True)

    # Nümunə görünüş
    st.dataframe(df.head(50), use_container_width=True)

else:
    st.info("Fayl yükləyin.")
