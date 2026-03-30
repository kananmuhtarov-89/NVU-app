# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 19:43:45 2026

@author: kanan
"""

import streamlit as st

# Page config
st.set_page_config(page_title="NVU Platform", layout="wide")

# --- STYLE ---
st.markdown("""
<style>
.main-title {
    text-align: center;
    font-size: 36px;
    font-weight: 700;
    color: #0B3C5D;
    margin-bottom: 40px;
}

.card {
    background-color: #ffffff;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    text-align: center;
    height: 200px;
}

.card-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 20px;
}

.block-message {
    text-align: center;
    font-size: 20px;
    color: #444;
    margin-top: 100px;
}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "page" not in st.session_state:
    st.session_state.page = "home"

# --- HOME PAGE ---
if st.session_state.page == "home":

    st.markdown('<div class="main-title">NVU Rəqəmsal İdarəetmə Platforması</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="card"><div class="card-title">Arayışların Avtomatlaşdırılmış Hazırlanması</div></div>', unsafe_allow_html=True)
        if st.button("Giriş", key="b1"):
            st.session_state.page = "arayis"

    with col2:
        st.markdown('<div class="card"><div class="card-title">Aktların Avtomatlaşdırılmış Tərtibi</div></div>', unsafe_allow_html=True)
        if st.button("Giriş", key="b2"):
            st.session_state.page = "akt"

    with col3:
        st.markdown('<div class="card"><div class="card-title">Maliyyə Ödənişlərinə Nəzarət və Yoxlama Sistemi</div></div>', unsafe_allow_html=True)
        if st.button("Giriş", key="b3"):
            st.session_state.page = "odenis"

# --- MODULE PAGES ---
else:
    st.markdown('<div class="main-title">Modul</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="block-message">
    Bu modul üzrə hazırda texniki təkmilləşdirmə və optimallaşdırma işləri aparılır. 
    Yaxın zamanda istifadəyə veriləcək.
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Geri"):
        st.session_state.page = "home"