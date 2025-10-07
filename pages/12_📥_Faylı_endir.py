# pages/12_📥_Faylı_endir.py
import streamlit as st
import pandas as pd
from datetime import datetime

from nvu.export import export_docx, export_xlsx
from nvu.settings import get_settings

st.title("Export (DOCX/XLSX)")

# 0) DataFrame-i təhlükəsiz götür
df = st.session_state.get("df_clean")
if not isinstance(df, pd.DataFrame) or df.empty:
    df = st.session_state.get("df")
if not isinstance(df, pd.DataFrame) or df.empty:
    st.info("İxrac üçün məlumat yoxdur. Əvvəlcə faylı yükləyin və filtrləri tətbiq edin.")
    st.stop()

source_filename = st.session_state.get("source_filename", "")

# 1) Report obyektini topla (səndə necə idisə elə qalaq)
report = {}

for key in [
    "utilizator_counts",
    "tesnifat_table", "tesnifat_counts", "tesnifat_settings",
    "tesdiq_status_totals", "tehvil_status_totals",
    "top_erizeci", "top_marka", "top_model", "top_reng",
    "year_bins",
]:
    report[key] = st.session_state.get(key)

# -----------------------------  YENİ: Top-N meta  --------------------------------
# DOCX başlıqlarında N-lərin dinamik çıxması üçün report["top_counts_meta"] MUTLƏQ dolmalıdır.
meta = st.session_state.get("top_counts_meta")
if not isinstance(meta, dict) or not meta:
    # Fallback – səndə param açarları belə adlana bilər:
    # param_topN_erizeci / param_topN_marka / param_topN_model / param_topN_reng
    meta = {
        "erizeci_N": int(
            st.session_state.get("param_topN_erizeci")
            or st.session_state.get("topN_applicant")
            or st.session_state.get("topN_erizeci")
            or 50
        ),
        "marka_N": int(
            st.session_state.get("param_topN_marka")
            or st.session_state.get("topN_brand")
            or st.session_state.get("topN_marka")
            or 20
        ),
        "model_N": int(
            st.session_state.get("param_topN_model")
            or st.session_state.get("topN_model")
            or 10
        ),
        "reng_N": int(
            st.session_state.get("param_topN_reng")
            or st.session_state.get("topN_color")
            or st.session_state.get("topN_reng")
            or 10
        ),
    }
report["top_counts_meta"] = meta
# -------------------------------------------------------------------------------

# Filtr xülasəsi (sənəddə boş olanda mesaj üçün)
report["summary"] = st.session_state.get("active_filter_summary") or "Seçilmiş filtr üçün uyğun sətir tapılmadı."

# 2) Power BI üçün “tek-sheet feed” hazırla (əgər artıq edirdinsə – eyni qalır)
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

# 3) Export düymələri — dəyişməyib
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
