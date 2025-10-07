# pages/12__Faylı_endir.py
import pandas as pd
import streamlit as st
from nvu.export import export_docx, export_xlsx

df = st.session_state.get("df_clean")
if df is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()

st.title("Export (DOCX/XLSX)")
source_filename = st.session_state.get("source_filename", "—")

# ---------------- Parametrlər ----------------
TOP_ERIZECI = int(st.session_state.get("param_topN_erizeci", 50))
TOP_MARKA   = int(st.session_state.get("param_topN_marka", 20))
TOP_MODEL   = int(st.session_state.get("param_topN_model", 10))
TOP_RENG    = int(st.session_state.get("param_topN_reng", 10))

TES_TABLE_READY = st.session_state.get("tesnifat_table")   # DataFrame və ya None
TES_MERGE_G     = bool(st.session_state.get("tesnifat_merge", True))
TES_CALC_AMOUNT = bool(st.session_state.get("tesnifat_calc", True))   # default ON

# ---------------- Köməkçilər ----------------
def col_exists(c): return c in df.columns

def drop_blanks_series(s: pd.Series) -> pd.Series:
    # NaN, "", whitespace, NBSP, "—", "-" → boş say
    s1 = s.astype(str)
    s1 = s1.str.replace("\u00A0", "", regex=False)  # NBSP
    s1 = s1.str.strip()
    s1 = s1.replace({"": pd.NA, "—": pd.NA, "-": pd.NA})
    return s1.dropna()

def topn(df_in: pd.DataFrame, cols, out="Say", n=10):
    if any(c not in df_in.columns for c in cols):
        return pd.DataFrame(columns=[*cols, out])
    g = (df_in.groupby(cols, dropna=False)
         .size().reset_index(name=out)
         .sort_values(out, ascending=False)
         .head(int(n)))
    return g

def year_bins_10y(col_name: str):
    if col_name not in df.columns:
        return pd.DataFrame(columns=["Buraxılış ili","Say"])
    s = pd.to_numeric(df[col_name], errors="coerce").dropna().astype(int)
    if s.empty:
        return pd.DataFrame(columns=["Buraxılış ili","Say"])
    decade = (s // 10) * 10
    labels = decade.astype(int).astype(str) + "–" + (decade + 9).astype(str)
    out = (labels.value_counts()
                 .sort_index()
                 .rename_axis("Buraxılış ili")
                 .reset_index(name="Say"))
    return out

# ---------------- Report ----------------
report = {}

# 1) Utilizator sayları
if col_exists("Utilizatorun adı"):
    util = (df["Utilizatorun adı"].value_counts(dropna=False)
            .rename_axis("Utilizatorun adı")
            .reset_index(name="NV sayı"))
else:
    util = pd.DataFrame(columns=["Utilizatorun adı","NV sayı"])
report["utilizator_counts"] = util

# 2) Təsnifat
report["tesnifat_settings"] = {"merge_g": TES_MERGE_G, "calc_amounts": TES_CALC_AMOUNT}
report["tesnifat_table"] = TES_TABLE_READY  # Word Açıqlamanı çıxmayacaq
if col_exists("Təsnifat"):
    report["tesnifat_counts"] = (df["Təsnifat"].value_counts(dropna=False)
                                 .rename_axis("Təsnifat")
                                 .reset_index(name="Say"))
else:
    report["tesnifat_counts"] = pd.DataFrame(columns=["Təsnifat","Say"])

# 3) Status cədvəlləri — BLANK-ları çıx
if col_exists("Təsdiq edici sənədin statusu"):
    s = drop_blanks_series(df["Təsdiq edici sənədin statusu"])
    report["tesdiq_status_totals"] = (s.value_counts()
                                      .rename_axis("Təsdiq edici sənədin statusu")
                                      .reset_index(name="Say"))
else:
    report["tesdiq_status_totals"] = pd.DataFrame(columns=["Təsdiq edici sənədin statusu","Say"])

if col_exists("Təhvil-təslim sənədinin statusu"):
    s = drop_blanks_series(df["Təhvil-təslim sənədinin statusu"])
    report["tehvil_status_totals"] = (s.value_counts()
                                      .rename_axis("Təhvil-təslim sənədinin statusu")
                                      .reset_index(name="Say"))
else:
    report["tehvil_status_totals"] = pd.DataFrame(columns=["Təhvil-təslim sənədinin statusu","Say"])

# 4) Top-N cədvəlləri
report["top_erizeci"] = topn(df, ["Ərizəçinin tam adı"], n=TOP_ERIZECI)
report["top_marka"]   = topn(df, ["Marka"], n=TOP_MARKA)
report["top_model"]   = topn(df, ["Marka","Model"], n=TOP_MODEL)
report["top_reng"]    = topn(df, ["Rəng"], n=TOP_RENG)

# 5) Yaş — 10 illik intervallar
report["year_bins"] = year_bins_10y("Buraxılış ili")

# 6) Top-N meta (başlıqlar üçün)
report["top_counts_meta"] = {
    "erizeci_N": TOP_ERIZECI,
    "marka_N": TOP_MARKA,
    "model_N": TOP_MODEL,
    "reng_N": TOP_RENG,
}

# ---------------- Export düymələri ----------------
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
