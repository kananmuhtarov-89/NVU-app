import streamlit as st, os
from nvu.sections import *
from nvu.regions import load_region_map
df_clean = st.session_state.get("df_clean")
if df_clean is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()
region_map = load_region_map(os.path.join(os.path.dirname(__file__), "..", "data", "az_region_codes.json"))

import pandas as pd
from nvu.export import export_docx, export_xlsx
st.title("Export (DOCX/XLSX)")
source_filename = st.session_state.get("source_filename","—")
report = {
    "utilizator_counts": section1_utilizator(df_clean, "Utilizatorun adı", "NV qeydiyyat nömrəsi"),
    "tesnifat_counts": section2_tesnifat(df_clean, "Təsnifat"),
    "tesdiq_status_totals": section3_status_totals(df_clean, "Təsdiq edici sənədin statusu"),
    "tehvil_status_totals": section4_status_totals(df_clean, "Təhvil-təslim sənədinin statusu"),
    "top50_erizeci": section5_top50_erizeci(df_clean, "Ərizəçinin tam adı"),
    "top20_marka": section6_top20_marka(df_clean, "Marka"),
    "top20_model": section7_top20_model(df_clean, "Marka", "Model"),
    "top20_reng": section8_top20_reng(df_clean, "Rəng"),
    "region_counts": section9_region_counts(df_clean, "NV qeydiyyat nömrəsi", region_map),
    "year_bins": section10_year_bins(df_clean, "Buraxılış ili"),
}
c1, c2 = st.columns(2)
with c1:
    if st.button("DOCX yarat"):
        bio = export_docx(report, source_filename)
        st.download_button("DOCX yüklə", data=bio, file_name=f"Arayis_{source_filename}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
with c2:
    if st.button("XLSX yarat"):
        bio = export_xlsx(report)
        st.download_button("XLSX yüklə", data=bio, file_name=f"Arayis_{source_filename}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
