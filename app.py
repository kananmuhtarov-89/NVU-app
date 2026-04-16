import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="NVU Platform", layout="wide")

# ========================= STYLE (FIXED COLORS) =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #163a5c !important;
}

.stApp {
    background: linear-gradient(180deg, #f4f8fc 0%, #eaf2fb 100%);
    color: #163a5c !important;
}

h1, h2, h3, h4, h5, h6,
label, p, div, span {
    color: #163a5c !important;
}

.main-title {
    text-align: center;
    font-size: 40px;
    font-weight: 700;
    margin-bottom: 30px;
}

.card {
    background: white;
    border-radius: 16px;
    padding: 25px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    text-align: center;
}

.stButton > button {
    width: 100%;
    border-radius: 10px;
    background: #2d79bd;
    color: white;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ========================= STATE =========================
if "page" not in st.session_state:
    st.session_state.page = "home"

# ========================= HOME =========================
if st.session_state.page == "home":
    st.markdown('<div class="main-title">NVU Rəqəmsal İdarəetmə Platforması</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown('<div class="card">📄<br><b>Arayışların Hazırlanması</b></div>', unsafe_allow_html=True)
        if st.button("Giriş", key="b1"):
            st.session_state.page = "mod1"

    with c2:
        st.markdown('<div class="card">🧾<br><b>Aktların Tərtibi</b></div>', unsafe_allow_html=True)
        if st.button("Giriş", key="b2"):
            st.session_state.page = "mod2"

    with c3:
        st.markdown('<div class="card">💰<br><b>Maliyyə Yoxlama</b></div>', unsafe_allow_html=True)
        if st.button("Giriş", key="b3"):
            st.session_state.page = "mod3"

# ========================= MODUL 1 =========================
elif st.session_state.page == "mod1":
    st.title("Arayış modulu")

    menu = st.sidebar.selectbox("Bölmə seç", [
        "Faylı yüklə",
        "Utilizatorlar",
        "Təsnifat",
        "Region",
        "NV yaşları",
        "Faylı endir"
    ])

    if menu == "Faylı yüklə":
        st.write("Excel yüklə hissəsi")

    elif menu == "Utilizatorlar":
        st.write("Utilizatorlar bölməsi")

    elif menu == "Təsnifat":
        st.write("Təsnifat bölməsi")

    elif menu == "Region":
        st.write("Region bölməsi")

    elif menu == "NV yaşları":
        st.write("NV yaşları")

    elif menu == "Faylı endir":
        st.write("Export bölməsi")

    if st.button("Geri"):
        st.session_state.page = "home"

# ========================= MODUL 2 =========================
elif st.session_state.page == "mod2":
    st.title("Akt modulu")

    excel = st.file_uploader("Excel cədvəli", type=["xlsx"])
    word = st.file_uploader("Word şablonu", type=["docx"])

    st.text_input("Sheet adı (istəyə görə)")
    st.text_input("Satış nömrələri")

    if st.button("AKT yarat"):
        st.success("Hazır olacaq (placeholder)")

    if st.button("Geri"):
        st.session_state.page = "home"

# ========================= MODUL 3 =========================
elif st.session_state.page == "mod3":
    st.title("Maliyyə modulu")

    file = st.file_uploader("Excel faylı", type=["xlsx"])

    sales = st.text_input("Satış nömrələri")

    if file and st.button("Hesabla"):
        df = pd.read_excel(file)

        satis = pd.to_numeric(df.iloc[:,0], errors="coerce").ffill()
        meb = pd.to_numeric(df.iloc[:,4], errors="coerce").fillna(0)

        df2 = pd.DataFrame({"S":satis, "M":meb})
        df2["S"] = df2["S"].astype(int)

        total = 0

        for s in sales.split(","):
            s = int(s)
            sub = df2[df2["S"] == s]
            val = sub["M"].sum()
            st.write(f"{s}: {val}")
            total += val

        st.success(f"TOTAL: {total}")

    if st.button("Geri"):
        st.session_state.page = "home"
