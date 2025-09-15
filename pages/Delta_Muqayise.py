
import streamlit as st, pandas as pd
st.title("İki faylın müqayisəsi (Delta)")
left, right = st.columns(2)
with left:
    A = st.file_uploader("Fayl A (.xlsx/.xls)", type=["xlsx","xls"])
with right:
    B = st.file_uploader("Fayl B (.xlsx/.xls)", type=["xlsx","xls"])

if A and B:
    try:
        a = pd.read_excel(A); b = pd.read_excel(B)
        st.success("Fayllar oxundu.")
        st.subheader("Sətir sayı dəyişikliyi")
        st.write({"A": len(a), "B": len(b), "Delta": len(b)-len(a)})
    except Exception as e:
        st.error(f"Xəta: {e}")
else:
    st.info("Hər iki faylı seçin.")
