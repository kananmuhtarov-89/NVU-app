import streamlit as st
import pandas as pd
import numpy as np

# --- Local fallbacks so we don't depend on nvu.cleaning during deploy
def load_excel(file):
    return pd.read_excel(file, dtype=object, engine="openpyxl")

st.title("1) Faylı yüklə / Təmizlə")

AZ_MONTHS = {1:"Yanvar",2:"Fevral",3:"Mart",4:"Aprel",5:"May",6:"İyun",7:"İyul",8:"Avqust",9:"Sentyabr",10:"Oktyabr",11:"Noyabr",12:"Dekabr"}

# ---------- Helpers (ASCII-safe) ----------
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

# ---------- Exact titles you showed (normalized) ----------
EXACT_TITLES = {
    "R": [
        "muraciet uzre son emeliyyat tarixi",
        "müraciət üzrə son əməliyyat tarixi",
    ],
    "W": [
        "icra senedi uzre son emeliyyat",
        "icra senedi uzre son emeliyyat tarixi",
        "icra sənədi üzrə son əməliyyat",
        "icra sənədi üzrə son əməliyyat tarixi",
    ],
    "AB": [
        "tehvil-teslim uzre son emeliyyat",
        "tehvil-teslim uzre son emeliyyat tarixi",
        "təhvil-təslim üzrə son əməliyyat",
        "təhvil-təslim üzrə son əməliyyat tarixi",
    ],
    "AF": [
        "tesdiqedici sened uzre son emeliyyat",
        "tesdiqedici sened uzre son emeliyyat tarixi",
        "təsdiqedici sənəd üzrə son əməliyyat",
        "təsdiqedici sənəd üzrə son əməliyyat tarixi",
    ],
    "AM": [
        "birdefelik odenis senedinin son emeliyyat tarixi",
        "birdefelik odenis senedinin son emeliyyat",
        "birdəfəlik ödəniş sənədinin son əməliyyat tarixi",
        "birdəfəlik ödəniş sənədinin son əməliyyat",
    ],
}

# Keywords (AND). We require "emeliyyat" to avoid mapping to "...nomresi".
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

    # 1) exact title match
    exacts = [norm(t) for t in EXACT_TITLES.get(key, [])]
    for c in cols:
        if ncols[c] in exacts:
            candidates.append(c)

    # 2) keyword AND match
    if not candidates:
        for token_set in KEYWORD_SETS.get(key, []):
            for c in cols:
                nc = ncols[c]
                if all(t in nc for t in token_set):
                    candidates.append(c)

    # 3) fallback by column letter
    if not candidates:
        col_by_letter = get_column_by_letter(df, letter_hint)
        if col_by_letter is not None:
            candidates.append(col_by_letter)

    if not candidates:
        return None, pd.Series(pd.NaT, index=df.index), 0.0

    # Choose the candidate with highest datetime coverage
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

uploaded = st.file_uploader("Excel (.xlsx/.xls) yüklə", type=["xlsx","xls"])

if uploaded:
    # 1) Load
    df_raw = load_excel(uploaded)
    st.write("Sətir sayı (xam):", len(df_raw))

    # 2) Deduplicate (keep last)
    DEDUP_KEYS = [
        "Təhvil aktının seriya nömrəsi",
        "Təsdiqedici sənədin seriyası",
        "NV qeydiyyat nömrəsi",
    ]
    keys_present = [c for c in DEDUP_KEYS if c in df_raw.columns]
    if keys_present:
        df = df_raw.drop_duplicates(subset=keys_present, keep="last").copy()
    else:
        df = df_raw.drop_duplicates(keep="last").copy()

    # 3) Column mapping per source (title -> keywords -> letter)
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

    # 4) Composite date = row-wise max of sources
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

    # 5) Put into session
    st.session_state["df_clean_full"] = df.copy()
    st.session_state["df_clean"] = df.copy()
    st.session_state["coverage_by_source"] = coverage
    st.session_state["minmax_by_source"] = minmax
    st.session_state["active_source_key"] = "R"
    st.session_state["filter_initialized"] = False

    # 6) Coverage table
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

    # Preview
    st.dataframe(df.head(50), use_container_width=True)

else:
    st.info("Fayl yükləyin.")
