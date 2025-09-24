import streamlit as st
import pandas as pd
import numpy as np

# --- Local loader (deploy-da asılılıq olmasın) ---
def load_excel(file):
    return pd.read_excel(file, dtype=object, engine="openpyxl")

st.title("1) Faylı yüklə / Təmizlə")

AZ_MONTHS = {1:"Yanvar",2:"Fevral",3:"Mart",4:"Aprel",5:"May",6:"İyun",7:"İyul",8:"Avqust",9:"Sentyabr",10:"Oktyabr",11:"Noyabr",12:"Dekabr"}

# ---------- Köməkçilər (ASCII-safe) ----------
def norm(s: str) -> str:
    s = str(s).strip().lower()
    trans_from = "ıiəeöoüuşıçcğg"
    trans_to   = "iieeoouussccgg"
    tbl = str.maketrans({src: dst for src, dst in zip(trans_from, trans_to)})
    return s.translate(tbl)

def col_letter_to_index(letter: str) -> int:
    letter = str(letter).strip().upper()
    val = 0
    for ch in letter:
        if not ("A" <= ch <= "Z"):
            return -1
        val = val * 26 + (ord(ch) - 64)
    return val - 1

def get_column_by_letter(df: pd.DataFrame, letter: str):
    idx = col_letter_to_index(letter)
    return df.columns[idx] if 0 <= idx < len(df.columns) else None

def robust_to_datetime(series: pd.Series) -> pd.Series:
    s = series.copy()
    s_str = s.astype(str).str.replace("\u00a0", " ", regex=False).str.strip()
    dt = pd.to_datetime(s_str, errors="coerce", dayfirst=True, infer_datetime_format=True)
    mask_nat = dt.isna()
    if mask_nat.any():
        s_num = pd.to_numeric(s_str.where(mask_nat), errors="coerce")
        valid = s_num.between(20000, 50000, inclusive="both")  # Excel serial range ~1955..2090
        if valid.any():
            base = pd.Timestamp("1899-12-30")
            dt2 = base + pd.to_timedelta(s_num[valid], unit="D")
            dt.loc[valid.index.intersection(dt2.index)] = dt2
    return dt

# ---------- Sənin verdiyin başlıqlara uyğun xəritələmə ----------
EXACT_TITLES = {
    "R": ["muraciet uzre son emeliyyat tarixi","müraciət üzrə son əməliyyat tarixi"],
    "W": ["icra senedi uzre son emeliyyat","icra senedi uzre son emeliyyat tarixi","icra sənədi üzrə son əməliyyat","icra sənədi üzrə son əməliyyat tarixi"],
    "AB":["tehvil-teslim uzre son emeliyyat","tehvil-teslim uzre son emeliyyat tarixi","təhvil-təslim üzrə son əməliyyat","təhvil-təslim üzrə son əməliyyat tarixi"],
    "AF":["tesdiqedici sened uzre son emeliyyat","tesdiqedici sened uzre son emeliyyat tarixi","təsdiqedici sənəd üzrə son əməliyyat","təsdiqedici sənəd üzrə son əməliyyat tarixi"],
    "AM":["birdefelik odenis senedinin son emeliyyat tarixi","birdefelik odenis senedinin son emeliyyat","birdəfəlik ödəniş sənədinin son əməliyyat tarixi","birdəfəlik ödəniş sənədinin son əməliyyat"],
}
# Açar sözlər (AND) – “emeliyyat” şərtini saxlayırıq ki, nömrə sütununa düşməyək
KEYWORD_SETS = {
    "R":  [["murac", "emeliyyat"]],
    "W":  [["icra", "emeliyyat"]],
    "AB": [["tehvil", "emeliyyat"], ["teslim", "emeliyyat"]],
    "AF": [["tesdiq", "sened", "emeliyyat"]],
    "AM": [["birdefelik", "odenis", "emeliyyat"]],
}

def find_best_column(df: pd.DataFrame, key: str, letter_hint: str):
    cols = list(df.columns)
    ncols = {c: norm(c) for c in cols}
    candidates = []

    # 1) Tam başlıq
    exacts = [norm(t) for t in EXACT_TITLES.get(key, [])]
    for c in cols:
        if ncols[c] in exacts:
            candidates.append(c)

    # 2) Açar sözlər
    if not candidates:
        for token_set in KEYWORD_SETS.get(key, []):
            for c in cols:
                nc = ncols[c]
                if all(t in nc for t in token_set):
                    candidates.append(c)

    # 3) Fallback: sütun hərfi
    if not candidates:
        col_by_letter = get_column_by_letter(df, letter_hint)
        if col_by_letter is not None:
            candidates.append(col_by_letter)

    if not candidates:
        return None, pd.Series(pd.NaT, index=df.index), 0.0

    # Namizədlərdən tarixə ən çox çevriləni seç
    best_col, best_cov, best_dt = None, -1.0, None
    for c in candidates:
        dt = robust_to_datetime(df[c])
        cov = (100.0 * dt.notna().sum() / len(df)) if len(df) else 0.0
        if cov > best_cov:
            best_col, best_cov, best_dt = c, cov, dt

    return best_col, best_dt, best_cov

SOURCES = {
    "R":  {"letter": "R",  "label": "Müraciət üzrə son əməliyyat tarixi"},
    "W":  {"letter": "W",  "label": "İcra sənədi üzrə son əməliyyat"},
    "AB": {"letter": "AB", "label": "Təhvil-təslim üzrə son əməliyyat"},
    "AF": {"letter": "AF", "label": "Təsdiqedici sənəd üzrə son əməliyyat"},
    "AM": {"letter": "AM", "label": "Birdəfəlik ödəniş sənədinin son əməliyyat tarixi"},
}

NV_COL_TITLE = "NV qeydiyyat nömrəsi"  # J sütunu başlığı

uploaded = st.file_uploader("Excel (.xlsx/.xls) yüklə", type=["xlsx","xls"])

if uploaded:
    # 1) Load (raw)
    df_raw = load_excel(uploaded)
    st.write("Sətir sayı (xam):", len(df_raw))

    # 2) Əvvəlcə R sütununu xam cədvəldə tap və dt_R çıxar
    r_colname, dt_r_raw, r_cov_raw = find_best_column(df_raw, "R", "R")
    if r_colname is None:
        st.error("R sütunu (Müraciət üzrə son əməliyyat tarixi) tapılmadı.")
        st.stop()

    df_raw["dt_R"] = dt_r_raw  # xam cədvəldə R tarixlərini saxlayırıq

    # 3) NV üzrə **ən yeni R** məntiqi ilə dedup:
    if NV_COL_TITLE in df_raw.columns:
        # ən yeni R yuxarıda olsun, NaT-lər sonda qalsın
        df_sorted = df_raw.sort_values(["dt_R"], ascending=False, na_position="last")
        df = df_sorted.drop_duplicates(subset=[NV_COL_TITLE], keep="first").copy()
    else:
        # NV sütunu yoxdursa, sadəcə sonu saxla (fallback)
        df = df_raw.drop_duplicates(keep="last").copy()

    # 4) İndi seçilmiş (dedup) cədvəldə bütün mənbələri (R/W/AB/AF/AM) yenidən qur
    coverage, minmax, resolved_cols = {}, {}, {}

    # R — artıq biliriksə də, dedup cədvəldə bir daha hesablayaq
    r_colname_final, dt_r, r_cov = find_best_column(df, "R", "R")
    resolved_cols["R"] = r_colname_final
    df["dt_R"] = dt_r
    df["il_R"] = dt_r.dt.year
    df["ay_no_R"] = dt_r.dt.month
    df["ay_ad_R"] = df["ay_no_R"].map(AZ_MONTHS)
    coverage["R"] = r_cov
    r_min, r_max = dt_r.min(), dt_r.max()
    minmax["R"] = {"min": (r_min.strftime("%Y-%m-%d") if pd.notna(r_min) else "—"),
                   "max": (r_max.strftime("%Y-%m-%d") if pd.notna(r_max) else "—")}

    # Digər mənbələr (yalnız xəritələ və pars et; dedup qərarına təsir etmir)
    for key in ["W","AB","AF","AM"]:
        colname, dt, cov = find_best_column(df, key, SOURCES[key]["letter"])
        resolved_cols[key] = colname
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
            dmin, dmax = dt.min(), dt.max()
            minmax[key] = {"min": (dmin.strftime("%Y-%m-%d") if pd.notna(dmin) else "—"),
                           "max": (dmax.strftime("%Y-%m-%d") if pd.notna(dmax) else "—")}

    # 5) KOMPOZIT (filtr üçün lazım ola bilər; dedupda istifadə ETMİRİK)
    dt_cols = [c for c in ["dt_R","dt_W","dt_AB","dt_AF","dt_AM"] if c in df.columns]
    if dt_cols:
        for c in dt_cols:
            df[c] = pd.to_datetime(df[c], errors="coerce")
        df["dt_KOMPOZIT"] = df[dt_cols].max(axis=1)
    else:
        df["dt_KOMPOZIT"] = pd.NaT

    ok = df["dt_KOMPOZIT"].notna().sum()
    coverage["KOMPOZIT"] = (100.0 * ok / len(df)) if len(df) else 0.0
    kmin, kmax = df["dt_KOMPOZIT"].min(), df["dt_KOMPOZIT"].max()
    minmax["KOMPOZIT"] = {"min": (kmin.strftime("%Y-%m-%d") if pd.notna(kmin) else "—"),
                          "max": (kmax.strftime("%Y-%m-%d") if pd.notna(kmax) else "—")}

    # 6) Session state
    st.session_state["df_clean_full"] = df.copy()
    st.session_state["df_clean"] = df.copy()
    st.session_state["coverage_by_source"] = coverage
    st.session_state["minmax_by_source"] = minmax
    st.session_state["active_source_key"] = "R"     # default filtr R-dir
    st.session_state["filter_initialized"] = False

    # 7) Özet cədvəl
    st.success(f"Təmizləndi. Sətirlər (təmiz): {len(df)}")
    st.caption("Tarix sütunlarının əhatəsi və min/max dəyərləri:")

    cov_rows = []
    for k in ["R","W","AB","AF","AM"]:
        cov_rows.append({
            "Mənbə": f"{k} — {SOURCES[k]['label']}",
            "Sütun (hərf)": SOURCES[k]["letter"],
            "Sütun (ad)": resolved_cols.get(k) or "tapılmadı",
            "Dolu %": round(coverage.get(k,0.0), 1),
            "Min": minmax.get(k, {"min":"—"})["min"],
            "Max": minmax.get(k, {"max":"—"})["max"],
        })
    cov_rows.append({
        "Mənbə": "KOMPOZİT — ən son əməliyyat",
        "Sütun (hərf)": "-",
        "Sütun (ad)": "max(dt_R, dt_W, dt_AB, dt_AF, dt_AM)",
        "Dolu %": round(coverage.get("KOMPOZIT", 0.0), 1),
        "Min": minmax["KOMPOZIT"]["min"],
        "Max": minmax["KOMPOZIT"]["max"],
    })
    st.dataframe(pd.DataFrame(cov_rows), use_container_width=True)

    # Preview
    st.dataframe(df.head(50), use_container_width=True)

else:
    st.info("Fayl yükləyin.")
