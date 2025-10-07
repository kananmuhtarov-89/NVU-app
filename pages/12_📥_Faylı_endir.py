import streamlit as st
import pandas as pd
from datetime import datetime

# --- robust import (paket və ya lokal fayl) ---
try:
    from nvu.export import export_docx, export_xlsx
except ImportError:
    from export import export_docx, export_xlsx

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
report["tesnifat_settings"] = {"calc_amounts": bool(st.session_state.get("tesnifat_calc", False))}

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

# ... (sənin qalan guard/helper hissələrin eyni qala bilər)

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
