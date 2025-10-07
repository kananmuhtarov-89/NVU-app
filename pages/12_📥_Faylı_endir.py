# pages/12_📥_Faylı_endir.py
import streamlit as st
import pandas as pd
from datetime import datetime

from nvu.export import export_docx, export_xlsx
from nvu.settings import get_settings

st.title("Export (DOCX/XLSX)")

# 0) Məlumat varmı?  (DataFrame-lərdə 'or' istifadə ETMƏ!)
df = st.session_state.get("df_clean")
if not isinstance(df, pd.DataFrame) or df.empty:
    df = st.session_state.get("df")

if not isinstance(df, pd.DataFrame) or df.empty:
    st.info("İxrac üçün məlumat yoxdur. Əvvəlcə faylı yükləyin və filtrləri tətbiq edin.")
    st.stop()

# 1) Report bazası
report = {}

# a) Utilizator və təsnifat blokları
for key in [
    "utilizator_counts",
    "tesnifat_table", "tesnifat_counts", "tesnifat_settings",
]:
    report[key] = st.session_state.get(key)

# b) Status/Top/İllər
for key in [
    "tesdiq_status_totals", "tehvil_status_totals",
    "top_erizeci", "top_marka", "top_model", "top_reng",
    "year_bins",
]:
    report[key] = st.session_state.get(key)

# c) Top-N meta (Parametrlər səhifəsindən)
report["top_counts_meta"] = st.session_state.get("top_counts_meta") or {}

# d) Filtr xülasəsi (tam boş halda mesaj üçün)
report["summary"] = st.session_state.get("active_filter_summary") or "Seçilmiş filtr üçün uyğun sətir tapılmadı."

# 2) Power BI üçün “tek-sheet feed” qur (sütun adlarını rahat oxunan et)
cfg = get_settings()
colmap = (cfg or {}).get("column_map", {}) or {}

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

# tipləri uyğunlaşdır
for c in ["dt_R", "dt_AB", "dt_AF", "dt_KOMPOZIT"]:
    if c in feed.columns:
        feed[c] = pd.to_datetime(feed[c], errors="coerce")
if "Mebleg_AZN" in feed.columns:
    feed["Mebleg_AZN"] = pd.to_numeric(feed["Mebleg_AZN"], errors="coerce")

report["powerbi_feed"] = feed

# 3) UI — Export düymələri
c1, c2 = st.columns(2)

with c1:
    if st.button("DOCX yarat", type="primary"):
        bio = export_docx(report, source_filename=st.session_state.get("source_filename", ""))
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

st.caption("Qeyd: XLSX faylında 'PowerBI_Feed' adlı vərəq var — Power BI → Get Data → Excel ilə həmin vərəqi seçmək kifayətdir.")
