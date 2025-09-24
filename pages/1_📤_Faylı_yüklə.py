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

# ---------- Köməkçilər ----------
def norm(s: str) -> str:
    """Başlıq normalizasiyası (diakritiklər → latın, lower)."""
    s = str(s).strip().lower()
    tr = str.maketrans("ıİəƏöÖüÜşŞçÇğĞ", "iIeeoOuUsScCgG")
    return s.translate(tr)

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

def robust_to_datetime(series: pd.Series) -> pd.Series:
    """Tolerant tarix parsinqi: NBSP/boşluq təmizlənməsi, müxtəlif formatlar, Excel serial."""
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

# ---------- Başlıq əsaslı xəritələmə ----------
# Sənin göndərdiyin dəqiq başlıqlar:
EXACT_TITLES = {
    "R": [
        "müraciət üzrə son əməliyyat tarixi",
        "muraciet uzre son emeliyyat tarixi",
    ],
    "W": [
        "icra sənədi üzrə son əməliyyat",
        "icra senedi uzre son emeliyyat",
        "icra sənədi üzrə son əməliyyat tarixi",
        "icra senedi uzre son emeliyyat tarixi",
    ],
    "AB": [
        "təhvil-təslim üzrə son əməliyyat",
        "tehvil-teslim uzre son emeliyyat",
        "təhvil-təslim üzrə son əməliyyat tarixi",
        "tehvil-teslim uzre son emeliyyat tarixi",
    ],
    "AF": [
        "təsdiqedici sənəd üzrə son əməliyyat",
        "tesdiqedici sened uzre son emeliyyat",
        "təsdiqedici sənəd üzrə son əməliyyat tarixi",
        "tesdiqedici sened uzre son emeliyyat tarixi",
    ],
    "AM": [
        "birdəfəlik ödəniş sənədinin son əməliyyat tarixi",
        "birdefelik odenis senedinin son emeliyyat tarixi",
        "birdəfəlik ödəniş sənədinin son əməliyyat",
        "birdefelik odenis senedinin son emeliyyat",
    ],
}

# Açar sözlərlə (əməliyyat şərti mütləqdir) – “nömrə” sütunlarını istisna edir
KEYWORD_SETS = {
    "R":  [["murac", "emeliyyat"]],                          # "tarix" opsional
    "W":  [["icra", "emeliyyat"]],
    "AB": [["tehvil", "emeliyyat"], ["teslim", "emeliyyat"]],
    "AF": [["tesdiq", "sened", "emeliyyat"]],
    "AM": [["birdefelik", "odenis", "emeliyyat"]],
}

def find_best_column(df: pd.DataFrame, key: str, letter_hint: str):
    """
    1) Tam başlıq uyğunluğu (EXACT_TITLES)
    2) Açar sözlərlə axtarış (KEYWORD_SETS) — 'emeliyyat' mütləqdir
    3) Fallback: sütun hərfinə görə (letter_hint)
    Bir neçə namizəd olarsa, tarixə çevrilə bilənləri pars edib **coverage**-a görə ən yaxşını seç.
    """
    cols = list(df.columns)
    ncols = {c: norm(c) for c in cols}
    candidates = []

    # 1) exact match
    exacts = [norm(t) for t in EXACT_TITLES.get(key, [])]
    for c in cols:
        if ncols[c] in exacts:
            candidates.append(("exact", c))

    # 2) keyword match (AND qaydası)
    if not candidates:
        for token_set in KEYWORD_SETS.get(key, []):
            token_set = [t for t in token_set]  # already ascii-like
            for c in cols:
                nc = ncols[c]
                if all(t in nc for t in token_set):
                    candidates.append(("kw", c))

    # 3) fallback by letter
    if not candidates:
        col_by_letter = get_column_by_letter(df, letter_hint)
        if col_by_letter is not None:
            candidates.append(("letter", col_by_letter))

    if not candidates:
        return None, pd.Series(pd.NaT, index=df.index), 0.0

    # Namizədlər arasından ən yaxşısını seç: tarix parsinqi coverage-ı ən yüksək olan
    best_col, best_cov, best_dt = None, -1.0, None
    for _, c in candidates:
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

uploaded = st.file_uploader("Excel (.xlsx/.xls) yüklə", type=["xlsx","xls"])

if uploaded:
    # 1) Yüklə
    df_raw = load_excel(uploaded)
    st.write("Sətir sayı (xam):", len(df_raw))

    # 2) Dublikatları təmizlə  (keep="last" istədiyimiz davranışdır)
DEDUP_KEYS = [
    "Təhvil aktının seriya nömrəsi",
    "Təsdiqedici sənədin seriyası",
    "NV qeydiyyat nömrəsi",
]

try:
    # Sənin nvu.cleaning modulun keep-i dəstəkləyirsə bunu işlədəcək
    df = dedup_dataframe(df_raw, *DEDUP_KEYS, keep="last").copy()
except TypeError:
    # Bəzi repolarda dedup_dataframe keep parametrini qəbul etmir → pandas ilə et
    keys = [c for c in DEDUP_KEYS if c in df_raw.columns]
    df = (df_raw.drop_duplicates(subset=keys, keep="last").copy() if keys else df_raw.copy())


    # 3) Xəritələmə: əvvəl başlıqla, sonra keyword, sonra hərflə (R/W/AB/AF/AM)
    coverage, minmax, resolved_cols = {}, {}, {}
    for key, meta in SOURCES.items():
        colname, dt, cov = find_best_column(df, key, meta["letter"])
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
            min_d, max_d = dt.min(), dt.max()
            minmax[key] = {
                "min": (min_d.strftime("%Y-%m-%d") if pd.notna(min_d) else "—"),
                "max": (max_d.strftime("%Y-%m-%d") if pd.notna(max_d) else "—"),
            }

    # 4) KOMPOZİT — sətir üzrə max(dt_R, dt_W, dt_AB, dt_AF, dt_AM)
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
