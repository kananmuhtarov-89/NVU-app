# pages/12__Faylı_endir.py — v3
import streamlit as st
import pandas as pd
from nvu.export import build_report, export_docx

st.title("Faylı endir (Export)")

file = st.file_uploader("Faylı yüklə (Excel/CSV)", type=["xlsx", "xls", "csv"])
if not file:
    st.info("Xahiş olunur, fayl yükləyin.")
    st.stop()

# Məlumatı oxu
try:
    if file.name.lower().endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
except Exception as e:
    st.error(f"Fayl oxunarkən xəta: {e}")
    st.stop()

# Status sütunlarını ehtimalla tap (adlar səndə fərqli ola bilər — siyahını genişləndirə bilərik)
status_name_candidates = [
    "Təsdiq edici sənədin statusu",
    "Təsdiqedici sənədin statusu",
    "Təhvil-təslim sənədinin statusu",
    "Təhvil təslim statusu",
]
status_cols_guess = [c for c in status_name_candidates if c in df.columns]

# Parametr: boşları daxil et?
include_blanks = bool(st.session_state.get("param_include_blanks", False))

# Report qur
report = build_report(
    df,
    st.session_state,
    status_cols=status_cols_guess,
    include_blanks=include_blanks,
)

st.subheader("Ön-baxış")
for key, tbl in report["tables"].items():
    st.write(f"**{key}**")
    st.dataframe(tbl, use_container_width=True)

st.markdown("---")
if st.button("Word faylı yarat və endir"):
    try:
        data = export_docx(report)
        st.download_button(
            "Hesabatı yüklə (DOCX)",
            data=data,
            file_name="ESLI_Arayis_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        st.error(f"Word çıxışı zamanı xəta: {e}")
