import streamlit as st
import pandas as pd
from datetime import datetime

# ---- PATCH: robust import for export module ----
try:
    # paket kimi (nvu/export.py) olduqda
    from nvu.export import export_docx, export_xlsx
except ImportError:
    # fayl kökdə və ya eyni qovluqdadırsa (məs: "export (1).py" → "export.py")
    from export import export_docx, export_xlsx
# -----------------------------------------------

from nvu.settings import get_settings

st.title("Export (DOCX/XLSX)")

# 0) DataFrame təhlükəsiz götürülməsi
df = st.session_state.get("df_clean")
if not isinstance(df, pd.DataFrame) or df.empty:
    df = st.session_state.get("df")
if not isinstance(df, pd.DataFrame) or df.empty:
    st.info("İxrac üçün məlumat yoxdur. Əvvəlcə faylı yükləyin və filtrləri tətbiq edin.")
    st.stop()

source_filename = st.session_state.get("source_filename", "")

# 1) Report obyektini topla
report = {}
# toggle-dən gələn dəyəri export-a ötür
report["tesnifat_settings"] = {"calc_amounts": bool(st.session_state.get("tesnifat_calc", False))}

for key in [
    "utilizator_counts",
    "tesnifat_table", "tesnifat_counts", "tesnifat_settings",
    "tesdiq_status_totals", "tehvil_status_totals",
    "top_erizeci", "top_marka", "top_model", "top_reng",
    "year_bins",
]:
    report[key] = st.session_state.get(key)

# --- Top-N meta (DOCX başlıqları üçün) ---
meta = st.session_state.get("top_counts_meta")
if not isinstance(meta, dict) or not meta:
    meta = {
        "erizeci_N": int(st.session_state.get("param_topN_erizeci") or st.session_state.get("topN_erizeci") or 50),
        "marka_N":   int(st.session_state.get("param_topN_marka")   or st.session_state.get("topN_marka")   or 20),
        "model_N":   int(st.session_state.get("param_topN_model")   or st.session_state.get("topN_model")   or 10),
        "reng_N":    int(st.session_state.get("param_topN_reng")    or st.session_state.get("topN_reng")    or 10),
    }
report["top_counts_meta"] = meta

# --- çatışmayan hissələr üçün əvvəlki təhlükəsiz guard-lar ---
def _drop_blanks_series(s: pd.Series) -> pd.Series:
    s1 = s.astype(str).str.replace("\u00A0", "", regex=False).str.strip()
    return s1.replace({"": pd.NA, "—": pd.NA, "-": pd.NA, "nan": pd.NA, "None": pd.NA}).dropna()

def _topn(df_in: pd.DataFrame, cols, out="Say", n=10):
    if any(c not in df_in.columns for c in cols):
        return pd.DataFrame(columns=[*cols, out])
    return (df_in.groupby(cols, dropna=False)
             .size().reset_index(name=out)
             .sort_values(out, ascending=False)
             .head(int(n)))

def _year_bins_10y(df_in: pd.DataFrame, col_name: str):
    if col_name not in df_in.columns:
        return pd.DataFrame(columns=["Buraxılış ili","Say"])
    s = pd.to_numeric(df_in[col_name], errors="coerce").dropna().astype(int)
    if s.empty:
        return pd.DataFrame(columns=["Buraxılış ili","Say"])
    decade = (s // 10) * 10
    labels = decade.astype(str) + "–" + (decade + 9).astype(str)
    return (labels.value_counts().sort_index()
            .rename_axis("Buraxılış ili").reset_index(name="Say"))

# 1) Utilizatorlar
if (report.get("utilizator_counts") is None or
    not isinstance(report.get("utilizator_counts"), pd.DataFrame) or
    report["utilizator_counts"].empty):
    col = "Utilizatorun adı" if "Utilizatorun adı" in df.columns else None
    report["utilizator_counts"] = (
        df[col].value_counts(dropna=False).rename_axis("Utilizatorun adı").reset_index(name="NV sayı")
        if col else pd.DataFrame(columns=["Utilizatorun adı","NV sayı"])
    )

# 2) Təsnifat baza (tesnifat_table yoxdursa ən azı saylar olsun)
if (report.get("tesnifat_counts") is None or
    not isinstance(report.get("tesnifat_counts"), pd.DataFrame) or
    report["tesnifat_counts"].empty):
    col = "Təsnifat" if "Təsnifat" in df.columns else None
    report["tesnifat_counts"] = (
        df[col].value_counts(dropna=False).rename_axis("Təsnifat").reset_index(name="Say")
        if col else pd.DataFrame(columns=["Təsnifat","Say"])
    )

# 3) Status cədvəlləri və s. (qalan hissə eynidir) ...
# -- buradan aşağı səndə necə idisə eyni qalsın --

# 3) Export düymələri
c1, c2 = st.columns(2)

with c1:
    if st.button("DOCX yarat", type="primary"):
        bio = export_docx(report, source_filename=source_filename)
        st.download_button(
            label="DOCX yüklə",
            data=bio,
            file_name=f"Arayis_—_{datetime.now():%Y%m%d_%H%M%S}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

with c2:
    if st.button("XLSX yarat"):
        bio = export_xlsx(report)
        st.download_button(
            label="XLSX yüklə",
            data=bio,
            file_name=f"Arayis_—_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
