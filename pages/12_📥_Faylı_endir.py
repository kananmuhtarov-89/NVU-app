# pages/12__Faylı_endir.py
import os
import pandas as pd
import streamlit as st

from nvu.export import export_docx, export_xlsx

# =========================
# Data yoxlaması
# =========================
df = st.session_state.get("df_clean")
if df is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()

st.title("Export (DOCX/XLSX)")
source_filename = st.session_state.get("source_filename", "—")

# =========================
# Parametrlər (sessiyadan)
# =========================
TOP_ERIZECI = int(st.session_state.get("param_topN_erizeci", 50))
TOP_MARKA   = int(st.session_state.get("param_topN_marka", 20))
TOP_MODEL   = int(st.session_state.get("param_topN_model", 10))
TOP_RENG    = int(st.session_state.get("param_topN_reng", 10))

# Təsnifat səhifəsindəki seçimlər
TES_MERGE_G    = bool(st.session_state.get("tesnifat_merge", True))
TES_CALC_AM    = bool(st.session_state.get("tesnifat_calc", False))
TES_TABLE_READY = st.session_state.get("tesnifat_table")  # DataFrame və ya None

# =========================
# Köməkçi funksiyalar
# =========================
def col_exists(c): return c in df.columns

def topn(df_in: pd.DataFrame, cols, out="Say", n=10):
    if any(c not in df_in.columns for c in cols):
        return pd.DataFrame(columns=[*cols, out])
    g = (df_in.groupby(cols, dropna=False)
                .size().reset_index(name=out)
                .sort_values(out, ascending=False)
                .head(int(n)))
    return g

def value_counts_df(series_name: str):
    if series_name not in df.columns:
        return pd.DataFrame(columns=[series_name, "Say"])
    return (df[series_name].value_counts(dropna=False)
                         .rename_axis(series_name)
                         .reset_index(name="Say"))

# =========================
# Report obyekti
# =========================
report = {}

# 1) Utilizatorlar: NV sayı
if col_exists("Utilizatorun adı"):
    util = (df["Utilizatorun adı"].value_counts(dropna=False)
             .rename_axis("Utilizatorun adı")
             .reset_index(name="NV sayı"))
else:
    util = pd.DataFrame(columns=["Utilizatorun adı","NV sayı"])
report["utilizator_counts"] = util

# 2) Təsnifatlar (fallback üçün baza) + səhifədən hazır cədvəl
report["tesnifat_settings"] = {"merge_g": TES_MERGE_G, "calc_amounts": TES_CALC_AM}
report["tesnifat_table"] = TES_TABLE_READY  # None ola bilər
if col_exists("Təsnifat"):
    report["tesnifat_counts"] = df["Təsnifat"].value_counts(dropna=False).rename_axis("Təsnifat").reset_index(name="Say")
else:
    report["tesnifat_counts"] = pd.DataFrame(columns=["Təsnifat","Say"])

# 3) Status cədvəlləri
report["tesdiq_status_totals"] = value_counts_df("Təsdiq edici sənədin statusu")
report["tehvil_status_totals"] = value_counts_df("Təhvil-təslim sənədinin statusu")

# 4) Top-N cədvəlləri (Parametrlərə uyğun)
report["top_erizeci"] = topn(df, ["Ərizəçinin tam adı"], n=TOP_ERIZECI)
report["top_marka"]   = topn(df, ["Marka"], n=TOP_MARKA)
report["top_model"]   = topn(df, ["Marka","Model"], n=TOP_MODEL)
report["top_reng"]    = topn(df, ["Rəng"], n=TOP_RENG)

# 5) (Opsional) yaş paylanması — varsa
if col_exists("Buraxılış ili"):
    y = pd.to_numeric(df["Buraxılış ili"], errors="coerce").dropna().astype(int)
    report["year_bins"] = y.value_counts().sort_index().rename_axis("Buraxılış ili").reset_index(name="Say")
else:
    report["year_bins"] = pd.DataFrame(columns=["Buraxılış ili","Say"])

# Top N meta başlıqlar üçün
report["top_counts_meta"] = {
    "erizeci_N": TOP_ERIZECI,
    "marka_N": TOP_MARKA,
    "model_N": TOP_MODEL,
    "reng_N": TOP_RENG,
}

# =========================
# Export Düymələri
# =========================
c1, c2 = st.columns(2)
with c1:
    if st.button("DOCX yarat"):
        bio = export_docx(report, source_filename)
        st.download_button(
            "DOCX yüklə",
            data=bio,
            file_name=f"Arayis_{source_filename}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
with c2:
    if st.button("XLSX yarat"):
        bio = export_xlsx(report)
        st.download_button(
            "XLSX yüklə",
            data=bio,
            file_name=f"Arayis_{source_filename}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
