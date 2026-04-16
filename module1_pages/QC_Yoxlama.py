
import streamlit as st, pandas as pd
from nvu.settings import get_settings
from nvu.qc import qc_report

st.title("Keyfiyyət Yoxlaması (QC)")

df = st.session_state.get("df_raw_clean")
if df is None:
    st.warning("Əvvəlcə **1) Yüklə / Təmizlə** səhifəsində fayl yüklə."); st.stop()

cfg = get_settings()
colmap = cfg.get("column_map",{})
dedup_keys = cfg.get("dedup_keys", [])

issues = qc_report(df, colmap, dedup_keys)
for name, table in issues.items():
    st.subheader(name)
    if table is not None and not table.empty:
        st.dataframe(table, use_container_width=True)
        st.download_button(f"{name} — CSV endir", data=table.to_csv(index=False).encode("utf-8"),
                           file_name=f"QC_{name}.csv", mime="text/csv")
    else:
        st.success("Problem tapılmadı.")
