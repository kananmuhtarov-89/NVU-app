# pages/12_📥_Faylı_endir.py
import io
import streamlit as st
import pandas as pd
from datetime import datetime

from nvu.export import export_docx, export_xlsx
from nvu.settings import get_settings

st.title("Export (DOCX/XLSX)")

# --- Giriş obyektləri ---
df = st.session_state.get("df_clean")  # filtrdən keçmiş əsas cədvəl
if df is None or df.empty:
    st.info("İxrac üçün məlumat yoxdur. Əvvəlcə faylı yükləyin və filtr tətbiq edin.")
    st.stop()

report = st.session_state.get("report", {}) or {}
# Digər səhifələrdə hazırlanmış cədvəllər adətən st.session_state-dədir:
# report["utilizator_counts"], report["tesnifat_table"], status topluları, top_* və s.
# Burada ehtiyac olarsa doldura bilərik (məs: yoxdursa None saxlayırıq).

# --- Power BI üçün tek-sheet feed qurulması ---
cfg = get_settings()
colmap = (cfg or {}).get("column_map", {}) or {}

# Məntiq: st.session_state["df_clean"] içindən ən faydalı sütunları sabit adlarla çıxarıb bir vərəqdə veririk.
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
    # Tarixlər — pages/1 faylında yaranır
    "dt_R":            ["dt_R", "R tarixi", "R_tarix"],
    "dt_AB":           ["dt_AB", "AB tarixi", "AB_tarix"],
    "dt_AF":           ["dt_AF", "AF tarixi", "AF_tarix"],
    "dt_KOMPOZIT":     ["dt_KOMPOZIT"],
    "il_KOMPOZIT":     ["il_KOMPOZIT", "il_R", "il_AB", "il_AF"],         # ehtiyat
    "ay_no_KOMPOZIT":  ["ay_no_KOMPOZIT", "ay_no_R", "ay_no_AB", "ay_no_AF"],
}

feed = pd.DataFrame()
for out_col, cands in feed_cols_candidates.items():
    for c in cands:
        if c and c in df.columns:
            feed[out_col] = df[c]
            break

# Tipləri sabitlə (Power BI üçün)
for c in ["dt_R", "dt_AB", "dt_AF", "dt_KOMPOZIT"]:
    if c in feed.columns:
        feed[c] = pd.to_datetime(feed[c], errors="coerce")
if "Mebleg_AZN" in feed.columns:
    feed["Mebleg_AZN"] = pd.to_numeric(feed["Mebleg_AZN"], errors="coerce")

# report-a əlavə et
report["powerbi_feed"] = feed

# --- Yükləmə düymələri ---
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

# Kiçik info
st.caption("XLSX faylında 'PowerBI_Feed' adlı ayrıca vərəq yaradılır. Power BI-da Get Data → Excel ilə bu vərəqi seçmək kifayətdir.")
