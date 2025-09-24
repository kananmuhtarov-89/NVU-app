import streamlit as st

st.set_page_config(page_title="NVU Utilizasiya", page_icon="🧩", layout="wide")
st.title("NVU Utilizasiya — Analitika tətbiqi")
st.markdown("Bu tətbiq Excel faylını yükləyib **təmizləyir** və **bölmələr** üzrə nəticələri göstərir.")
st.info("Başlamaq üçün solda **1) Faylı yüklə / Təmizlə** səhifəsinə keçin. Aşağıdakı **İl/Ay filtri** bütün səhifələrə tətbiq olunur.")

# ========= Sidebar: İl / Ay Filtrləri =========
with st.sidebar:
    st.header("Filtr: İl / Ay")

    df_full = st.session_state.get("df_clean_full")
    has_data = df_full is not None and len(df_full) > 0

    # ----- İllər -----
    # Mövcud illəri tap və EN SON ili çıxart
    years_available = (
        sorted([int(x) for x in df_full["il"].dropna().unique().tolist()])
        if has_data and "il" in df_full.columns else []
    )
    latest_year = max(years_available) if years_available else None

    # Radio: default = "Seçilən illər" əgər son il mövcuddursa, yoxdursa "Hamısı"
    year_mode = st.radio(
        "İl rejimi",
        options=["Hamısı", "Seçilən illər"],
        index=(1 if latest_year else 0),
        horizontal=True,
        disabled=not has_data
    )

    # Multi-select: default = [son il] (əgər var), əks halda bütün illər
    year_select = st.multiselect(
        "İllər",
        years_available,
        default=([latest_year] if latest_year else years_available),
        disabled=not (has_data and year_mode == "Seçilən illər")
    )

    # ----- Aylar -----
    months_available = ["Yanvar","Fevral","Mart","Aprel","May","İyun","İyul","Avqust","Sentyabr","Oktyabr","Noyabr","Dekabr"]

    month_mode = st.radio(
        "Ay rejimi",
        options=["Hamısı", "Seçilən aylar"],
        index=0,  # default Hamısı
        horizontal=True,
        disabled=not has_data
    )

    month_select = st.multiselect(
        "Aylar",
        months_available,
        default=months_available,   # Hamısı
        disabled=not (has_data and month_mode == "Seçilən aylar")
    )

    c1, c2 = st.columns(2)
    reset = c1.button("Sıfırla", use_container_width=True, disabled=not has_data)
    apply = c2.button("Tətbiq et",
