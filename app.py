import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="NVU Platform", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "home"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #f4f8fc 0%, #eaf2fb 100%);
}

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 700;
    color: #123b63;
    margin-top: 20px;
    margin-bottom: 40px;
}

.card-wrap {
    background: #ffffff;
    border-radius: 22px;
    padding: 28px 22px;
    min-height: 220px;
    box-shadow: 0 10px 30px rgba(18, 59, 99, 0.10);
    border: 1px solid #dbe7f3;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.card-icon {
    font-size: 42px;
    margin-bottom: 18px;
}

.card-title {
    text-align: center;
    font-size: 24px;
    font-weight: 700;
    color: #163a5c;
    line-height: 1.4;
}

.card-sub {
    text-align: center;
    font-size: 15px;
    color: #5e7388;
    margin-top: 10px;
    line-height: 1.6;
}

.info-box {
    max-width: 900px;
    margin: 80px auto 0 auto;
    background: #ffffff;
    border: 1px solid #d8e6f3;
    border-radius: 22px;
    padding: 40px 30px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(18, 59, 99, 0.10);
}

.info-title {
    font-size: 30px;
    font-weight: 700;
    color: #123b63;
    margin-bottom: 16px;
}

.info-text {
    font-size: 18px;
    line-height: 1.8;
    color: #4f6478;
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    border: none;
    background: linear-gradient(90deg, #1f5f99 0%, #2d79bd 100%);
    color: white;
    font-size: 18px;
    font-weight: 600;
    padding: 12px 18px;
    margin-top: 14px;
}

.stButton > button:hover {
    color: white;
}

.result-box {
    background: white;
    border-radius: 16px;
    padding: 18px 20px;
    border: 1px solid #dbe7f3;
    box-shadow: 0 6px 18px rgba(18, 59, 99, 0.08);
    margin-bottom: 12px;
    color: #163a5c;
    font-size: 17px;
    line-height: 1.7;
}

.block-btn .stButton > button {
    width: auto !important;
    padding: 10px 20px;
}

.small-note {
    color: #5e7388;
    font-size: 14px;
    margin-top: -10px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

def to_amount(series: pd.Series) -> pd.Series:
    s = series.fillna("").astype(str)
    s = s.str.replace(" ", "", regex=False).str.replace(",", ".", regex=False)
    s = s.str.extract(r"([-+]?\d*\.?\d+)")[0]
    return pd.to_numeric(s, errors="coerce").fillna(0)

def process_amounts(df_raw: pd.DataFrame, sales_input: str):
    if df_raw.shape[1] < 5:
        return None, "Faylda ən azı 5 sütun olmalıdır."

    satis = pd.to_numeric(df_raw.iloc[:, 0], errors="coerce").ffill()
    mebleg = to_amount(df_raw.iloc[:, 4])

    df = pd.DataFrame({"Satis": satis, "Mebleg": mebleg})
    df = df.dropna(subset=["Satis"]).copy()
    df["Satis"] = df["Satis"].astype(int)

    sales_list = [int(x) for x in re.split(r"[,\s;]+", sales_input.strip()) if x.isdigit()]
    if not sales_list:
        return None, "Düzgün satış nömrəsi daxil edilmədi."

    results = []
    total_say = 0
    total_mebleg = 0.0

    for s in sales_list:
        sub = df[df["Satis"] == s]
        say = int(sub["Mebleg"].gt(0).sum())
        meb = float(sub["Mebleg"].sum())

        total_say += say
        total_mebleg += meb

        results.append(f"{s}-ci NV: Say={say}, Məbləğ={meb:g}")

    results.append(f"TOTAL: Say={total_say}, Məbləğ={total_mebleg:g}")
    return results, None

if st.session_state.page == "home":
    st.markdown('<div class="main-title">NVU Rəqəmsal İdarəetmə Platforması</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown("""
        <div class="card-wrap">
            <div class="card-icon">📄</div>
            <div class="card-title">Arayışların Avtomatlaşdırılmış Hazırlanması</div>
            <div class="card-sub">Arayışların operativ və vahid formatda hazırlanması üçün modul</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Giriş", key="btn1"):
            st.session_state.page = "arayis"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="card-wrap">
            <div class="card-icon">🧾</div>
            <div class="card-title">Aktların Avtomatlaşdırılmış Tərtibi</div>
            <div class="card-sub">Akt sənədlərinin strukturlaşdırılmış və sürətli tərtibi üçün modul</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Giriş", key="btn2"):
            st.session_state.page = "akt"
            st.rerun()

    with col3:
        st.markdown("""
        <div class="card-wrap">
            <div class="card-icon">💳</div>
            <div class="card-title">Maliyyə Ödənişlərinə Nəzarət və Yoxlama Sistemi</div>
            <div class="card-sub">Satış sıralamasına görə say və məbləğin hesablanması üçün modul</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Giriş", key="btn3"):
            st.session_state.page = "odenis"
            st.rerun()

elif st.session_state.page in ["arayis", "akt"]:
    st.markdown('<div class="main-title">NVU Rəqəmsal İdarəetmə Platforması</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <div class="info-title">Modul üzrə məlumat</div>
        <div class="info-text">
            Bu modul üzrə hazırda texniki təkmilləşdirmə və optimallaşdırma işləri aparılır.
            Modul yaxın zamanda tam istifadəyə veriləcək.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="block-btn">', unsafe_allow_html=True)
    if st.button("← Geri qayıt"):
        st.session_state.page = "home"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "odenis":
    st.markdown('<div class="main-title">Maliyyə Ödənişlərinə Nəzarət və Yoxlama Sistemi</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Excel faylı əlavə et", type=["xlsx", "xls"])
    st.markdown('<div class="small-note">Qeyd: proqram həmişə faylın 1-ci sheet-ni götürür.</div>', unsafe_allow_html=True)

    sales_input = st.text_input("Satış nömrələri", placeholder="Məs: 1188,1220")

    df_raw = None
    if uploaded_file is not None:
        try:
            df_raw = pd.read_excel(uploaded_file, sheet_name=0)
            st.success("Excel faylı uğurla oxundu.")
        except Exception as e:
            st.error(f"Fayl oxunmadı: {e}")

    if st.button("Hesabla"):
        if uploaded_file is None:
            st.warning("Əvvəlcə Excel faylı əlavə et.")
        elif not sales_input.strip():
            st.warning("Satış nömrələrini daxil et.")
        else:
            results, err = process_amounts(df_raw, sales_input)
            if err:
                st.error(err)
            else:
                for line in results:
                    st.markdown(f'<div class="result-box">{line}</div>', unsafe_allow_html=True)

    st.markdown('<div class="block-btn">', unsafe_allow_html=True)
    if st.button("← Geri qayıt", key="back_from_odenis"):
        st.session_state.page = "home"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
