import streamlit as st

st.set_page_config(page_title="NVU Utilizasiya", page_icon="🧩", layout="wide")
st.title("NVU Utilizasiya — Analitika tətbiqi")
st.markdown("Bu tətbiq Excel faylını yükləyib **təmizləyir** və **bölmələr** üzrə nəticələri göstərir.")
st.info("Başlamaq üçün solda **1) Faylı yüklə** səhifəsinə keçin. Aşağıdakı **İl/Ay filtri** bütün səhifələrə tətbiq olunur.")

# ========= Sidebar: İl / Ay Filtrləri =========
with st.sidebar:
    st.header("Filtr: İl / Ay")

    df_full = st.session_state.get("df_clean_full")
    has_data = df_full is not None and len(df_full) > 0

    # İllər siyahısı və "ən son il"
    years_available = []
    latest_year = None
    if has_data and "il" in df_full.columns:
        try:
            years_available = sorted([int(x) for x in df_full["il"].dropna().unique().tolist()])
            latest_year = max(years_available) if years_available else None
        except Exception:
            years_available = []
            latest_year = None

    # İl rejimi (latest_year varsa default = "Seçilən illər")
    year_mode = st.radio(
        "İl rejimi",
        options=["Hamısı", "Seçilən illər"],
        index=(1 if latest_year else 0),
        horizontal=True,
        disabled=not has_data
    )
    year_select = st.multiselect(
        "İllər",
        years_available,
        default=([latest_year] if latest_year else years_available),
        disabled=not (has_data and year_mode == "Seçilən illər"),
    )

    # Ay rejimi
    months_available = ["Yanvar","Fevral","Mart","Aprel","May","İyun","İyul","Avqust","Sentyabr","Oktyabr","Noyabr","Dekabr"]
    month_mode = st.radio(
        "Ay rejimi",
        options=["Hamısı", "Seçilən aylar"],
        index=0,
        horizontal=True,
        disabled=not has_data
    )
    month_select = st.multiselect(
        "Aylar",
        months_available,
        default=months_available,
        disabled=not (has_data and month_mode == "Seçilən aylar"),
    )

    c1, c2 = st.columns(2)
    reset = c1.button("Sıfırla", use_container_width=True, disabled=not has_data)
    apply = c2.button("Tətbiq et", use_container_width=True, disabled=not has_data)

    # Tətbiq/Sıfırla məntiqi
    if has_data:
        if reset:
            st.session_state["df_clean"] = df_full.copy()
            st.session_state["active_filter_summary"] = "Hamısı"
            st.session_state["filter_initialized"] = False

        elif apply:
            view = df_full.copy()
            if year_mode == "Seçilən illər" and year_select:
                view = view[view.get("il").isin(year_select)]
            if month_mode == "Seçilən aylar" and month_select and "ay_ad" in view.columns:
                view = view[view["ay_ad"].isin(month_select)]
            st.session_state["df_clean"] = view
            parts = []
            parts.append("İl: " + (", ".join(map(str, year_select)) if year_mode == "Seçilən illər" else "Hamısı"))
            parts.append("Ay: " + (", ".join(month_select) if month_mode == "Seçilən aylar" else "Hamısı"))
            st.session_state["active_filter_summary"] = " | ".join(parts)

    st.caption("Filtr **Tətbiq et** ilə aktiv olur. **Sıfırla** → Hamısı.")

# --- İlk açılışda SON ili avtomatik tətbiq et (apply düyməsinə basmadan) ---
df_full = st.session_state.get("df_clean_full")
if df_full is not None and len(df_full) > 0 and not st.session_state.get("filter_initialized"):
    st.session_state["filter_initialized"] = True
    view = df_full.copy()
    if "il" in df_full.columns:
        try:
            yrs = sorted([int(x) for x in df_full["il"].dropna().unique().tolist()])
            if yrs:
                last = max(yrs)
                view = view[view["il"] == last]
                st.session_state["active_filter_summary"] = f"İl: {last} | Ay: Hamısı"
        except Exception:
            st.session_state["active_filter_summary"] = "Hamısı"
    st.session_state["df_clean"] = view

# Aktiv filtr bandı
summary_text = st.session_state.get("active_filter_summary", "Hamısı")
st.success(f"Aktiv filtr: {summary_text}")
