import os
import pandas as pd
import streamlit as st

from nvu.regions import load_region_map
from nvu.export import export_docx, export_xlsx

# =========================================
# Data
# =========================================
df_clean = st.session_state.get("df_clean")
if df_clean is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()

region_map = load_region_map(os.path.join(os.path.dirname(__file__), "..", "data", "az_region_codes.json"))

st.title("Export (DOCX/XLSX)")
source_filename = st.session_state.get("source_filename", "—")

# =========================================
# Parametrlər (sessiyadan; defaultlar)
# =========================================
N_ERIZECI = int(st.session_state.get("param_topN_erizeci", 50))
N_MARKA   = int(st.session_state.get("param_topN_marka", 20))
N_MODEL   = int(st.session_state.get("param_topN_model", 10))
N_RENG    = int(st.session_state.get("param_topN_reng", 10))

# =========================================
# Yardımçı: top-N hesablama
# =========================================
def topn_df(df: pd.DataFrame, cols, out_col="Say", n=10):
    g = (df.groupby(cols, dropna=False)
           .size()
           .reset_index(name=out_col)
           .sort_values(out_col, ascending=False)
           .head(n))
    return g

# =========================================
# Report obyekti
# =========================================
# 1) Utilizatorlar üzrə saylar
utilizator_counts = topn_df(df_clean, ["Utilizatorun adı"], out_col="NV sayı", n=10**9)  # hamısını veririk (sıralı)

# 2) Region, yaş və s. (sənin mövcud məntiqinə uyğun sadə quruluş)
region_counts = (df_clean.groupby("NV qeydiyyat nömrəsi", dropna=False)
                        .size().reset_index(name="Say"))  # əgər səndə ayrıca funksiya varsa onu istifadə et

# Təsnifat səhifəsindəki seçimlər + hazır cədvəl (əgər formalaşıbsa)
tesnifat_settings = {
    "merge_g": st.session_state.get("tesnifat_merge", True),
    "calc_amounts": st.session_state.get("tesnifat_calc", False),
}
tesnifat_table = st.session_state.get("tesnifat_table")  # None ola bilər

report = {
    # 1) Utilizatorlar
    "utilizator_counts": utilizator_counts,

    # 2) Təsnifatlar
    "tesnifat_counts": (df_clean.groupby("Təsnifat", dropna=False)
                                 .size().reset_index(name="Say")),  # fallback üçün baza
    "tesnifat_settings": tesnifat_settings,
    "tesnifat_table": tesnifat_table,

    # 3) Top-N blokları (dinamik)
    "top_erizeci": topn_df(df_clean, ["Ərizəçinin tam adı"], n=N_ERIZECI),
    "top_marka":   topn_df(df_clean, ["Marka"],               n=N_MARKA),
    "top_model":   topn_df(df_clean, ["Marka","Model"],       n=N_MODEL),
    "top_reng":    topn_df(df_clean, ["Rəng"],                n=N_RENG),

    # 4) Region/yaş və s. – lazım olduqca əlavə edirsən
    "region_counts": region_counts,
    "year_bins": (df_clean.assign(**{"Buraxılış ili":
                   pd.to_numeric(df_clean["Buraxılış ili"], errors="coerce")})
                   .dropna(subset=["Buraxılış ili"])
                   .assign(il=lambda x: x["Buraxılış ili"].astype(int))
                   .groupby("il").size().reset_index(name="Say")),
    # Top N dəyərləri başlıqlar üçün
    "top_counts_meta": {
        "erizeci_N": N_ERIZECI,
        "marka_N": N_MARKA,
        "model_N": N_MODEL,
        "reng_N": N_RENG,
    },
}

# =========================================
# UI: Export düymələri
# =========================================
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
