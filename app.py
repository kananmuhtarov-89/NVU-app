import streamlit as st

st.set_page_config(page_title="NVU Platform", layout="wide")

# Session state
if "page" not in st.session_state:
    st.session_state.page = "home"

# Style
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
    letter-spacing: 0.3px;
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
    transition: 0.3s ease;
}

.card-wrap:hover {
    transform: translateY(-4px);
    box-shadow: 0 16px 36px rgba(18, 59, 99, 0.14);
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
    background: linear-gradient(90deg, #184f81 0%, #256aa6 100%);
    color: white;
}

.back-btn .stButton > button {
    width: auto !important;
    padding: 10px 20px;
}
</style>
""", unsafe_allow_html=True)

# Home page
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
            <div class="card-sub">Maliyyə sənədləri və ödəniş proseslərinin nəzarəti üçün modul</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Giriş", key="btn3"):
            st.session_state.page = "odenis"
            st.rerun()

# Module page
else:
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

    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← Geri qayıt"):
        st.session_state.page = "home"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
