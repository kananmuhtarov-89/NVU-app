import streamlit as st
import pandas as pd
import numpy as np
from nvu.cleaning import load_excel, dedup_dataframe

st.title("1) Faylı yüklə / Təmizlə")

# ===== Köməkçilər =====
AZ_MONTHS = {1:"Yanvar",2:"Fevral",3:"Mart",4:"Aprel",5:"May",6:"İyun",7:"İyul",8:"Avqust",9:"Sentyabr",10:"Oktyabr",11:"Noyabr",12:"Dekabr"}

def col_letter_to_index(letter: str) -> int:
    """Excel sütun hərfini 0-based index-ə çevirir (A=0, AB=27, ...)."""
    letter = letter.strip().upper()
    val = 0
    for ch in letter:
        if not ("A" <= ch <= "Z"):
            return -1
        val = val * 26 + (ord(ch) - 64)
    return val - 1

def get_column_by_letter(df: pd.DataFrame, letter: str):
    idx = col_letter_to_index(letter)
    if 0 <= idx < len(df.columns):
        return df.columns[idx]
    return None

def robust_to_datetime(series: pd.Series) -> pd.Series:
    """Maksimum tolerantlıqla tarixi pars edir:
    - mətn təmizlənməsi (NBSP, boşluq),
    - dd.mm.yyyy / dd/mm/yyyy / dd-mm-yyyy (+ vaxt),
    - Excel serial ədəd tarixləri.
    """
    s = series.copy()
    # 1) string parse
    s_str = s.astype(str).str.replace("\u00a0", " ", regex=False).str.strip()
    dt = pd.to_datetime(s_str, errors="coerce", dayfirst=True, infer_datetime_format=True)
    # 2) serial number attempt (yalnız NaT qalanlar üçün)
    mask_nat = dt.isna()
    if mask_nat.any():
        s_num = pd.to_numeric(s_str.where(mask_nat), errors="coerce")
        # Serial aralığı (təxmini): 20000..50000 ~ illər 1955..2090
        valid = s_num.between(20000, 50000, inclusive="both")
        if valid.any():
            base = pd.Timestamp("1899-12-30")  # Excel 1900 date system
            dt2 = base + pd.to_timedelta(s_num[valid], unit="D")
            dt.loc[valid.index.intersection(dt2.index)] = dt2
    return dt

# Mənbələr: R/W/AB/AF/AM
SOURCES = {
    "R":  {"letter": "R",  "label": "Müraciət üzrə son əməliyyat tarixi"},
    "W":  {"letter": "W",  "label": "İcra sənədi üzrə son əməliyyat"},
    "AB": {"letter": "AB", "label": "Təhvil-təslim üzrə son əməliyyat"},
    "AF": {"letter": "AF", "label": "Təsdiqedici sənəd üzrə son əməliyyat"},
    "AM": {"letter": "AM", "label": "Birdəfəlik ödəniş sənədinin son əməliyyat tarixi"},
}

uploaded = st.file_uploader("Excel (.xlsx/.xls) yüklə", type=["xlsx","xls"])

if uploaded:
    # 1) Yüklə
    df_raw = load_excel(uploaded)
    st.write("Sətir sayı (xam):", len(df_raw))

    # 2) Dublikatları təmizlə (öz qaydana uyğundur)
    df = dedup_dataframe(
        df_raw,
        "Təhvil aktının seriya nömrəsi",
        "Təsdiqedici sənədin seriyası",
        "NV qeydiyyat nömrəsi",
    ).copy()

    # 3) Mənbə sütunlarını hərfə görə tap və pars et
    coverage = {}
    minmax = {}
    resolved_cols = {}
    for key, meta in SOURCES.items():
        colname = get_column_by_letter(df, meta["letter"])
        resolved_cols[key] = colname
        if colname is None:
            # sütun yoxdur
            df[f"dt_{key}"] = pd.NaT
            df[f"il_{key}"] = np.nan
            df[f"ay_no_{key}"] = np.nan
            df[f"ay_ad_{key}"] = np.nan
            coverage[key] = 0.0
            minmax[key] = {"min": "—", "max": "—"}
            continue

        dt = robust_to_datetime(df[colname])
        df[f"dt_{key}"] = dt
        df[f"il_{key}"] = dt.dt.year
        df[f"ay_no_{key}"] = dt.dt.month
        df[f"ay_ad_{key}"] = df[f"ay_no_{key}"].map(AZ_MONTHS)

        ok = dt.notna().sum()
        cov = 100.0 * ok / len(df) if len(df) else 0.0
        coverage[key] = cov
        min_d = dt.min(); max_d = dt.max()
        minmax[key] = {
            "min": (min_d.strftime("%Y-%m-%d") if pd.notna(min_d) else "—"),
            "max": (max_d.strftime("%Y-%m-%d") if pd.notna(max_d) else "—"),
        }

    # 4) KOMPOZİT tarix (ən son əməliyyat) — sətir üzrə max
    dt_cols = [c for c in df.columns if c.startswith("dt_") and len(c) <= 5]  # dt_R, dt_W, dt_AB, dt_AF, dt_AM
    if dt_cols:
        df["dt_KOMPOZIT"] = pd.to_datetime(df[dt_cols]).max(axis=1)
    else:
        df["dt_KOMPOZIT"] = pd.NaT

    # 5) Session state: tam və görünüş
    st.session_state["df_clean_full"] = df.copy()
    st.session_state["df_clean"] = df.copy()
    st.session_state["coverage_by_source"] = coverage
    st.session_state["minmax_by_source"] = minmax
    st.session_state["active_source_key"] = "R"   # default mənbə R
    st.session_state["filter_initialized"] = False

    # 6) Göstəricilər
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
    st.dataframe(pd.DataFrame(cov_rows), use_container_width=True)

    # Nümunə görünüş
    st.dataframe(df.head(50), use_container_width=True)

else:
    st.info("Fayl yükləyin.")
