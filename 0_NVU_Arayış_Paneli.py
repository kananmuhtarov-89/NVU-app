# 0_NVU_Arayış_Paneli.py
# Sidebar: tarix mənbəyi / il (default = Hamısı), ay (Hamısı) və aktiv filtrə görə df_clean hasil edilir.
# QEYD: Minimal dəyişikliklərlə default davranış düzəldilib.

import streamlit as st
import pandas as pd
from nvu.settings import get_settings

st.set_page_config(page_title="NVU Arayış Paneli", layout="wide")

# =========================================================
# 0) Giriş DataFrame-i: tam (filtrsüz) cədvəl
#    Səndə bu ad fərqli ola bilər: df_clean_full / df_full / df
# =========================================================
df_full = (
    st.session_state.get("df_clean_full")
    or st.session_state.get("df_full")
    or st.session_state.get("df")
)

# Əgər hələ fayl yüklənməyibsə, mesaj verib çıxaq
if df_full is None or len(df_full) == 0:
    st.sidebar.info("Faylı yükləyin (pages/1_📤_Faylı_yüklə.py).")
    st.write("Məlumat yoxdur. Zəhmət olmasa faylı yükləyin.")
    st.stop()

# =========================================================
# 1) Tarix sütun adları (column_map-dan)
#    Yalnız 4 mənbə: R, AB, AF, KOMPOZİT
# =========================================================
cfg = get_settings()
colmap = cfg.get("column_map", {}) or {}

def _col_from_map(colmap: dict, keys: list[str]) -> str | None:
    for k in keys:
        v = colmap.get(k)
        if v:
            return v
    return None

COL_R  = _col_from_map(colmap, ["R — Müraciət", "R—Müraciət", "R — Muraciət", "R—Muraciət"])
COL_AB = _col_from_map(colmap, ["AB — Təhvil-təslim", "AB—Təhvil-təslim", "AB — Tehvil-teslim"])
COL_AF = _col_from_map(colmap, ["AF — Təsdiqedici sənəd", "AF—Təsdiqedici sənəd", "AF — Tesdiqedici sened"])

SOURCE_LABELS = {
    "R":  "R — Müraciət",
    "AB": "AB — Təhvil-təslim",
    "AF": "AF — Təsdiqedici sənəd",
    "KOMPOZIT": "KOMPOZİT — ən son əməliyyat",
}

# =========================================================
# 2) Tarix seriyasını qur (seçilmiş mənbəyə görə)
# =========================================================
def _date_series_by_source(df: pd.DataFrame, source_key: str) -> pd.Series | None:
    sR  = pd.to_datetime(df[COL_R],  errors="coerce") if (COL_R  in df.columns) else None
    sAB = pd.to_datetime(df[COL_AB], errors="coerce") if (COL_AB in df.columns) else None
    sAF = pd.to_datetime(df[COL_AF], errors="coerce") if (COL_AF in df.columns) else None

    if source_key == "R":
        return sR
    if source_key == "AB":
        return sAB
    if source_key == "AF":
        return sAF
    if source_key == "KOMPOZIT":
        parts = [s for s in (sR, sAB, sAF) if s is not None]
        if not parts:
            return None
        return pd.concat(parts, axis=1).max(axis=1)
    return None

# =========================================================
# 3) Sidebar UI
#    DƏYİŞİKLİK #1: İl rejimi default = Hamısı (index=0)
#    DƏYİŞİKLİK #2: 2 sətirlik helper ilə year multiselect default
#    DƏYİŞİKLİK #3: İlk açılışda df_clean = df_full (il tətbiq etmə)
# =========================================================
st.sidebar.header("Filtr")

# 3.1) Tarix mənbəyi (yalnız 4 variant)
date_source_options = [SOURCE_LABELS[k] for k in ("R","AB","AF","KOMPOZIT")]
source_label = st.sidebar.selectbox("Tarix mənbəyi", date_source_options, index=0)
source_key = [k for k, v in SOURCE_LABELS.items() if v == source_label][0]  # "R"/"AB"/"AF"/"KOMPOZIT"

date_series = _date_series_by_source(df_full, source_key)
has_data = date_series is not None and date_series.notna().any()

# 3.2) İl rejimi (default = Hamısı)
year_mode = st.sidebar.radio("İl rejimi", ["Hamısı", "Seçilən illər"],
                             index=0, horizontal=True, disabled=not has_data)

# 3.3) İllər (multiselect) — yalnız “Seçilən illər” rejimində aktiv
years_available = sorted(date_series.dropna().dt.year.astype(int).unique().tolist()) if has_data else []

# ---- 2 SƏTİRLİK HELPER (default illər) ----
years_all = years_available[:]  # mövcud illər
default_years = [2024, 2025] if {2024, 2025}.issubset(set(years_all)) else years_all
# -------------------------------------------

year_select = st.sidebar.multiselect(
    "İllər",
    options=years_available,
    default=default_years,
    disabled=not (has_data and year_mode == "Seçilən illər"),
)

# 3.4) Ay rejimi (mövcud məntiqi saxlayırıq — default Hamısı)
month_mode = st.sidebar.radio("Ay rejimi", ["Hamısı", "Seçilən aylar"],
                              index=0, horizontal=True, disabled=not has_data)

AZ_MONTHS = {
    1:"Yan", 2:"Fev", 3:"Mar", 4:"Apr", 5:"May", 6:"İyn",
    7:"İyl", 8:"Avq", 9:"Sen", 10:"Okt", 11:"Noy", 12:"Dek"
}
month_opts = list(range(1, 13))
months_select = st.sidebar.multiselect(
    "Aylar",
    options=month_opts,
    format_func=lambda m: AZ_MONTHS.get(m, m),
    default=month_opts,  # “Seçilən aylar” rejiminə keçəndə hamısı ön seçili
    disabled=not (has_data and month_mode == "Seçilən aylar"),
)

# =========================================================
# 4) Filtri tətbiq et
# =========================================================
def _apply_filter(df: pd.DataFrame,
                  src_key: str,
                  years: list[int] | None,
                  months: list[int] | None) -> tuple[pd.DataFrame, str]:
    s = _date_series_by_source(df, src_key)
    if s is None:
        return df.copy(), "Tarix sütunu tapılmadı — Hamısı"

    mask = s.notna()

    # İl
    if years:
        mask &= s.dt.year.isin(years)

    # Ay
    if months:
        mask &= s.dt.month.isin(months)

    df_out = df[mask].copy()

    # Xülasə mətni
    sum_year = f"İl: {','.join(map(str, years))}" if years else "İl: Hamısı"
    sum_mon  = (f"Ay: {', '.join(AZ_MONTHS[m] for m in months)}" if months
                else "Ay: Hamısı")
    summary = f"Mənbə: {SOURCE_LABELS[src_key]} | {sum_year} | {sum_mon}"
    return df_out, summary

# DƏYİŞİKLİK #3: İlk açılışda heç bir il tətbiq ETMƏ — hamısı
if year_mode == "Hamısı":
    years_for_filter = None
else:
    years_for_filter = year_select or years_available  # seçilməyibsə də “Seçilən illər”də hamısını götür

months_for_filter = None if month_mode == "Hamısı" else (months_select or month_opts)

df_clean, summary = _apply_filter(df_full, source_key, years_for_filter, months_for_filter)

# Nəticəni paylaş (bütün səhifələr bunu oxuyur)
st.session_state["df_clean"] = df_clean
st.session_state["active_filter_summary"] = summary
st.session_state["active_source_key"] = source_key

# =========================================================
# 5) Ekranda qısa xülasə
# =========================================================
st.markdown(f"**Aktiv filtr:** {summary}")
st.caption(
    f"Sətir sayı: {len(df_clean):,} (cəmi: {len(df_full):,})".replace(",", " ")
)

# (İstəyə görə burada df_clean-in kiçik ön görüntüsünü göstərə bilərsən)
# st.dataframe(df_clean.head(10))
