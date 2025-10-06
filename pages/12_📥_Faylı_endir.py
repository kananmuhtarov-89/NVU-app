import streamlit as st
import pandas as pd
from nvu.export import build_report, export_docx

st.title("📥 Faylı endir (Export)")

uploaded = st.file_uploader("Excel/CSV faylı yüklə", type=["xlsx", "xls", "csv"])
if not uploaded:
    st.info("Xahiş olunur, fayl yükləyin.")
    st.stop()

# Məlumatı oxu
try:
    if uploaded.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"Fayl oxunarkən xəta: {e}")
    st.stop()

st.success(f"Yükləndi: {uploaded.name}")
st.dataframe(df.head(), use_container_width=True)

# Mümkün status sütun adları – ehtiyac olduqca genişləndir
status_name_candidates = [
    "Təsdiqedici sənədin statusu",
    "Təsdiq edici sənədin statusu",
    "Təhvil-təslim sənədinin statusu",
    "Təhvil təslim statusu",
]
status_cols = [c for c in status_name_candidates if c in df.columns]

# Report qur
report = build_report(
    df=df,
    session_state=st.session_state,
    status_cols=status_cols,
)

# Ön-baxış: 10 illik intervallar
st.subheader("NV yaşları – 10 illik intervallar (ön-baxış)")
dec_tbl = report["tables"]["decades"]
if dec_tbl is not None and not dec_tbl.empty:
    st.dataframe(dec_tbl, use_container_width=True)
else:
    st.write("Uyğun 'Buraxılış ili' sütunu tapılmadı.")

# Top cədvəllər (ön-baxış)
for key in ["top_applicant", "top_brand", "top_model", "top_color"]:
    tbl = report["tables"].get(key)
    if tbl is not None and not tbl.empty:
        st.subheader(key.replace("top_", "Top-").title())
        st.dataframe(tbl, use_container_width=True)

st.markdown("---")
if st.button("Word faylı yarat və endir"):
    try:
        data = export_docx(report)
        st.download_button(
            label="Hesabatı yüklə (DOCX)",
            data=data,
            file_name="ESLI_Arayis_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        st.error(f"Word çıxışı zamanı xəta: {e}")
