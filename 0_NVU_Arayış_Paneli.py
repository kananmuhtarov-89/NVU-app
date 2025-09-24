import streamlit as st

st.set_page_config(page_title="NVU Utilizasiya", page_icon="🧩", layout="wide")
st.title("NVU Utilizasiya — Analitika tətbiqi")
st.markdown("Bu tətbiq Excel faylını yükləyib **təmizləyir** və **10 bölmə** üzrə nəticələri göstərir.")
st.info("Başlamaq üçün solda **1) Yüklə / Təmizlə** səhifəsinə keçin. Aşağıdakı **İl/Ay filtri** bütün səhifələrə tətbiq olunur.")

# ========= Sidebar: İl / Ay Filtrləri =========
with st.sidebar:
    st.header("Filtr: İl / Ay")

    df_full = st.session_state.get("df_clean_full")
    has_data = df_full is not None and len(df_full) > 0

    # İl
    year_mode = st.radio("İl rejimi", ["Hamısı", "Seçilən illər"], index=0, horizontal=True, disabled=not has_data)
    years_available = sorted([int(x) for x in df_full["il"].dropna().unique().tolist()]) if has_data and "il" in df_full.columns else []
    year_select = st.multiselect("İllər", years_available, default=years_available, disabled=not (has_data and year_mode=="Seçilən illər"))

    # Ay
    month_mode = st.radio("Ay rejimi", ["Hamısı", "Seçilən aylar"], index=0, horizontal=True, disabled=not has_data)
    months_available = ["Yanvar","Fevral","Mart","Aprel","May","İyun","İyul","Avqust","Sentyabr","Oktyabr","Noyabr","Dekabr"]
    month_select = st.multiselect("Aylar", months_available, default=months_available, disabled=not (has_data and month_mode=="Seçilən aylar"))

    c1, c2 = st.columns(2)
    reset = c1.button("Sıfırla", use_container_width=True, disabled=not has_data)
    apply = c2.button("Tətbiq et", use_container_width=True, disabled=not has_data)

    # Tətbiq/Sıfırla
    if has_data:
        if reset:
            st.session_state["df_clean"] = df_full.copy()
            st.session_state["active_filter_summary"] = "Hamısı"
        elif apply:
            view = df_full.copy()
            if year_mode == "Seçilən illər" and year_select:
                view = view[view.get("il").isin(year_select)]
            if month_mode == "Seçilən aylar" and month_select:
                view = view[view.get("ay_ad").isin(month_select)]
            st.session_state["df_clean"] = view
            parts = []
            parts.append("İl: " + (", ".join(map(str, year_select)) if year_mode=="Seçilən illər" else "Hamısı"))
            parts.append("Ay: " + (", ".join(month_select) if month_mode=="Seçilən aylar" else "Hamısı"))
            st.session_state["active_filter_summary"] = " | ".join(parts)

    st.caption("Filtr **Tətbiq et** ilə aktiv olur. **Sıfırla** → Hamısı.")

# Aktiv filtr bandı
summary_text = st.session_state.get("active_filter_summary", "Hamısı")
st.success(f"Aktiv filtr: {summary_text}")
