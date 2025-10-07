# pages/12_📥_Faylı_endir.py
import streamlit as st
import pandas as pd
from datetime import datetime

from nvu.export import export_docx, export_xlsx
from nvu.settings import get_settings

st.title("Export (DOCX/XLSX)")

# 0) DataFrame təhlükəsiz seçimi (pandas truth-value xətası olmasın)
df = st.session_state.get("df_clean")
if not isinstance(df, pd.DataFrame) or df.empty:
    df = st.session_state.get("df")
if not isinstance(df, pd.DataFrame) or df.empty:
    st.info("İxrac üçün məlumat yoxdur. Əvvəlcə faylı yükləyin və filtrləri tətbiq edin.")
    st.stop()

# 1) Report obyektini topla (heç nəyi buraxmırıq)
report = {}
for key in [
    "utilizator_counts",
    "tesnifat_table", "tesnifat_counts", "tesnifat_settings",
    "tesdiq_status_totals", "tehvil_status_totals",
    "top_erizeci", "top_marka", "top_model", "top_reng",
    "year_bins",
]:
    report[key] = st.session_state.get(key)

# Top-N meta (Parametrlər səhifəsindən)
report["top_counts_meta"] = st.session_state.get("top_counts_meta") or {}

# Filtr xülasəsi (tam boş halda sənəddə mesaj üçün)
report["summary"] = st.session_state.get("active_filter_summary") or "Seçilmiş filtr üçün uyğun sətir tapılmadı."

# tesnifat_settings sağlam dict olsun (calc_amounts ilə, AttributeError-un qarşısı)
ts = report.get("tesnifat_settings")
if not isinstance(ts, dict):
    report["tesnifat_settings"] = {"calc_amounts": bool(st.session_state.get("tesnifat_calc", False))}
else:
    ts.setdefault("calc_amounts", bool(st.session_state.get("tesnifat_calc", False)))

# 2) Power BI üçün “tek-sheet feed” hazırla
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

# 3) UI — Export düymələri
c1, c2 = st.columns(2)

with c1:
    if st.button("DOCX yarat", type="primary"):
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

st.caption("XLSX faylında 'PowerBI_Feed' adlı vərəq var — Power BI → Get Data → Excel ilə həmin vərəqi seçmək kifayətdir.")
