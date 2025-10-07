# pages/12_📥_Faylı_endir.py
import streamlit as st
import pandas as pd
from datetime import datetime

from nvu.export import export_docx, export_xlsx
from nvu.settings import get_settings

st.title("Export (DOCX/XLSX)")

# 1) Data yoxlaması
df = st.session_state.get("df_clean")
if df is None or df.empty:
    st.info("İxrac üçün məlumat yoxdur. Əvvəlcə faylı yükləyin və filtr tətbiq edin.")
    st.stop()

# 2) Report obyektini yığ
report = st.session_state.get("report", {}) or {}

# Sessiyada formalaşmış cədvəlləri report-a kopyala (yoxdursa None qalır)
for key in [
    "utilizator_counts",
    "tesnifat_table", "tesnifat_counts", "tesnifat_settings",
    "tesdiq_status_totals", "tehvil_status_totals",
    "top_erizeci", "top_marka", "top_model", "top_reng",
    "year_bins", "top_counts_meta",
]:
    report.setdefault(key, st.session_state.get(key))

# Filtr xülasəsi (DOCX-də “Məlumat yoxdur” halında göstərmək üçün)
report["summary"] = st.session_state.get("active_filter_summary")

# 3) Power BI üçün “tek-sheet feed” qur
cfg = get_settings()
colmap = (cfg or {}).get("column_map", {}) or {}

feed_cols_candidates = {
    "NV_id":           [colmap.get("NV qeydiyyat nömrəsi"), "NV qeydiyyat nömrəsi", "NV", "NV_id"],
    "Utilizator":      [colmap.get("Utilizator"), "Utilizator", "İcraçı", "İşləyici"],
    "Tesnifat":        [colmap.get("Təsnifat"), "Təsnifat", "Kod/Təsnifat", "Kod"],
    "Marka":           [colmap.get("Marka"), "Marka"],
    "Model":           [colmap.get("Model"), "Model"],
    "Reng":            [colmap.get("Rəng"), "Rəng", "Reng"],
    "Mebleg_AZN":      [colmap.get("Məbləğ (AZN)"), "Məbləğ (AZN)", "Cəmi (AZN)", "Mebleg_AZN"],
    "TesdiqStatus":    [colmap.get("Təsdiq statusu"), "Təsdiq statusu", "Tesdiq_status"],
    "TehvilStatus":    [colmap.get("Təhvil statusu"), "Təhvil statusu", "Tehvil_status"],
    # Tarixlər (pages/1 səhifəsi bunları hesablayır)
    "dt_R":            ["dt_R", "R tarixi", "R_tarix"],
    "dt_AB":           ["dt_AB", "AB tarixi", "AB_tarix"],
    "dt_AF":           ["dt_AF", "AF tarixi", "AF_tarix"],
    "dt_KOMPOZIT":     ["dt_KOMPOZIT"],
    "il_KOMPOZIT":     ["il_KOMPOZIT", "il_R", "il_AB", "il_AF"],
    "ay_no_KOMPOZIT":  ["ay_no_KOMPOZIT", "ay_no_R", "ay_no_AB", "ay_no_AF"],
}

feed = pd.DataFrame()
for out_col, cands in feed_cols_candidates.items():
    for c in cands:
        if c and c in df.columns:
            feed[out_col] = df[c]
            break

for c in ["dt_R", "dt_AB", "dt_AF", "dt_KOMPOZIT"]:
    if c in feed.columns:
        feed[c] = pd.to_datetime(feed[c], errors="coerce")
if "Mebleg_AZN" in feed.columns:
    feed["Mebleg_AZN"] = pd.to_numeric(feed["Mebleg_AZN"], errors="coerce")

report["powerbi_feed"] = feed

# 4) Export düymələri
c1, c2 = st.columns(2)

with c1:
    if st.button("DOCX yarat"):
        bio = export_docx(report, source_filename=st.session_state.get("source_filename", ""))
        st.download_button(
            "DOCX yüklə",
            data=bio,
            file_name=f"Arayis_—_{datetime.now():%Y%m%d_%H%M%S}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

with c2:
    if st.button("XLSX yarat"):
        bio = export_xlsx(report)
        st.download_button(
            "XLSX yüklə",
            data=bio,
            file_name=f"Arayis_—_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

st.caption("XLSX faylında 'PowerBI_Feed' adlı ayrıca vərəq yaranır. Power BI → Get Data → Excel ilə bu vərəqi seçmək kifayətdir.")
