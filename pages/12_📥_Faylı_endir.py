import streamlit as st
import pandas as pd
from datetime import datetime

from nvu.export import export_docx, export_xlsx
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

# --- Təsnifat calc_amounts guard ---
ts = report.get("tesnifat_settings")
if not isinstance(ts, dict):
    report["tesnifat_settings"] = {"calc_amounts": bool(st.session_state.get("tesnifat_calc", False))}
# --- Fallback: report-da çatışmayan cədvəlləri df-dən avtomatik qur ---
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

# 3) Status cədvəlləri
if (report.get("tesdiq_status_totals") is None or
    not isinstance(report.get("tesdiq_status_totals"), pd.DataFrame) or
    report["tesdiq_status_totals"].empty):
    col = "Təsdiq edici sənədin statusu"
    report["tesdiq_status_totals"] = (
        _drop_blanks_series(df[col]).value_counts()
          .rename_axis(col).reset_index(name="Say")
        if col in df.columns else pd.DataFrame(columns=[col,"Say"])
    )

if (report.get("tehvil_status_totals") is None or
    not isinstance(report.get("tehvil_status_totals"), pd.DataFrame) or
    report["tehvil_status_totals"].empty):
    col = "Təhvil-təslim sənədinin statusu"
    report["tehvil_status_totals"] = (
        _drop_blanks_series(df[col]).value_counts()
          .rename_axis(col).reset_index(name="Say")
        if col in df.columns else pd.DataFrame(columns=[col,"Say"])
    )

# 4) Top-N (Parametrlərdən N dəyərlərini götürürük — artıq report["top_counts_meta"] var)
N_erizeci = int(report.get("top_counts_meta", {}).get("erizeci_N", 50))
N_marka   = int(report.get("top_counts_meta", {}).get("marka_N", 20))
N_model   = int(report.get("top_counts_meta", {}).get("model_N", 10))
N_reng    = int(report.get("top_counts_meta", {}).get("reng_N", 10))

if (report.get("top_erizeci") is None or
    not isinstance(report.get("top_erizeci"), pd.DataFrame) or
    report["top_erizeci"].empty):
    report["top_erizeci"] = _topn(df, ["Ərizəçinin tam adı"], n=N_erizeci)

if (report.get("top_marka") is None or
    not isinstance(report.get("top_marka"), pd.DataFrame) or
    report["top_marka"].empty):
    report["top_marka"] = _topn(df, ["Marka"], n=N_marka)

if (report.get("top_model") is None or
    not isinstance(report.get("top_model"), pd.DataFrame) or
    report["top_model"].empty):
    report["top_model"] = _topn(df, ["Marka","Model"], n=N_model)

if (report.get("top_reng") is None or
    not isinstance(report.get("top_reng"), pd.DataFrame) or
    report["top_reng"].empty):
    report["top_reng"] = _topn(df, ["Rəng"], n=N_reng)

# 5) İllər üzrə
if (report.get("year_bins") is None or
    not isinstance(report.get("year_bins"), pd.DataFrame) or
    report["year_bins"].empty):
    report["year_bins"] = _year_bins_10y(df, "Buraxılış ili")

# 2) PowerBI üçün “tek-sheet feed”
cfg = get_settings() or {}
colmap = (cfg.get("column_map") or {})
cands = {
    "NV_id":           [colmap.get("NV qeydiyyat nömrəsi"), "NV qeydiyyat nömrəsi", "NV", "NV_id"],
    "Utilizator":      [colmap.get("Utilizator"), "Utilizator", "İcraçı", "İşləyici"],
    "Tesnifat":        [colmap.get("Təsnifat"), "Təsnifat", "Kod/Təsnifat", "Kod"],
    "Marka":           [colmap.get("Marka"), "Marka"],
    "Model":           [colmap.get("Model"), "Model"],
    "Reng":            [colmap.get("Rəng"), "Rəng", "Reng"],
    "Mebleg_AZN":      [colmap.get("Məbləğ (AZN)"), "Məbləğ (AZN)", "Cəmi (AZN)", "Mebleg_AZN"],
    "TesdiqStatus":    [colmap.get("Təsdiq statusu"), "Təsdiq statusu", "Tesdiq_status"],
    "TehvilStatus":    [colmap.get("Təhvil statusu"), "Təhvil statusu", "Tehvil_status"],
    "dt_R":            ["dt_R", "R tarixi", "R_tarix"],
    "dt_AB":           ["dt_AB", "AB tarixi", "AB_tarix"],
    "dt_AF":           ["dt_AF", "AF tarixi", "AF_tarix"],
    "dt_KOMPOZIT":     ["dt_KOMPOZIT"],
    "il_KOMPOZIT":     ["il_KOMPOZIT", "il_R", "il_AB", "il_AF"],
    "ay_no_KOMPOZIT":  ["ay_no_KOMPOZIT", "ay_no_R", "ay_no_AB", "ay_no_AF"],
}
feed = pd.DataFrame()
for out_col, opts in cands.items():
    for c in opts:
        if c and c in df.columns:
            feed[out_col] = df[c]
            break
for c in ["dt_R", "dt_AB", "dt_AF", "dt_KOMPOZIT"]:
    if c in feed.columns:
        feed[c] = pd.to_datetime(feed[c], errors="coerce")
if "Mebleg_AZN" in feed.columns:
    feed["Mebleg_AZN"] = pd.to_numeric(feed["Mebleg_AZN"], errors="coerce")
report["powerbi_feed"] = feed

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
