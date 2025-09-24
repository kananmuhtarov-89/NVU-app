import streamlit as st
import pandas as pd

st.set_page_config(page_title="NVU Analitika", page_icon="🧩", layout="wide")
st.title("NVU Analitika — ümumi panel")
st.markdown("Sol menudan **1) Faylı yüklə** səhifəsində faylı yükləyin. Buradakı filtr bütün səhifələrə tətbiq olunur.")

AZ_MONTHS = ["Yanvar","Fevral","Mart","Aprel","May","İyun","İyul","Avqust","Sentyabr","Oktyabr","Noyabr","Dekabr"]

SOURCE_LABELS = {
    "R":  "R — Müraciət",
    "AB": "AB — Təhvil-təslim",
    "AF": "AF — Təsdiqedici sənəd",
    "KOMPOZIT": "KOMPOZİT — ən son əməliyyat (max R/AB/AF)",
}

def _get_years_from_source(df_full: pd.DataFrame, src_key: str):
    if df_full is None or len(df_full) == 0:
        return []
    if src_key == "KOMPOZIT":
        if "dt_KOMPOZIT" in df_full:
            yrs = df_full["dt_KOMPOZIT"].dropna().dt.year.unique().tolist()
            return sorted(int(x) for x in yrs)
        return []
    col = f"il_{src_key}"
    if col in df_full:
        yrs = df_full[col].dropna().unique().tolist()
        return sorted(int(x) for x in yrs)
    return []

def _apply_filter(df_full: pd.DataFrame, src_key: str, years_sel, months_sel):
    view = df_full.copy()
    if src_key == "KOMPOZIT":
        if years_sel:
            view = view[view["dt_KOMPOZIT"].dt.year.isin(years_sel)]
        if months_sel:
            view = view[view["dt_KOMPOZIT"].dt.month.isin([AZ_MONTHS.index(m)+1 for m in months_sel])]
    else:
        il_col = f"il_{src_key}"
        ay_col = f"ay_no_{src_key}"
        if years_sel and il_col in view:
            view = view[view[il_col].isin(years_sel)]
        if months_sel and ay_col in view:
            view = view[view[ay_col].isin([AZ_MONTHS.index(m)+1 for m in months_sel])]
    return view

with st.sidebar:
    st.header("Filtr: Tarix mənbəyi / İl / Ay")

    df_full = st.session_state.get("df_clean_full")
    has_data = df_full is not None and len(df_full) > 0

    src_options = list(SOURCE_LABELS.keys())
    default_key = st.session_state.get("active_source_key", "R")
    default_idx = src_options.index(default_key)
    option_labels = [SOURCE_LABELS[k] for k in src_options]
    selected_label = st.selectbox("Tarix mənbəyi", options=option_labels,
                                  index=default_idx, disabled=not has_data)
    src_key = src_options[option_labels.index(selected_label)]

    years_available = _get_years_from_source(df_full, src_key) if has_data else []
    latest_year = max(years_available) if years_available else None

    year_mode = st.radio("İl rejimi", ["Hamısı", "Seçilən illər"],
                         index=(1 if latest_year else 0), horizontal=True, disabled=not has_data)
    year_select = st.multiselect("İllər", years_available,
                                 default=([latest_year] if latest_year else years_available),
                                 disabled=not (has_data and year_mode=="Seçilən illər"))

    month_mode = st.radio("Ay rejimi", ["Hamısı", "Seçilən aylar"],
                          index=0, horizontal=True, disabled=not has_data)
    month_select = st.multiselect("Aylar", AZ_MONTHS,
                                  default=AZ_MONTHS,
                                  disabled=not (has_data and month_mode=="Seçilən aylar"))

    if has_data:
        cov = st.session_state.get("coverage_by_source", {}).get(src_key)
        mm  = st.session_state.get("minmax_by_source", {}).get(src_key)
        if cov is not None and mm is not None:
            st.caption(f"Seçilmiş mənbə: **{SOURCE_LABELS[src_key]}** — əhatə: **{cov:.1f}%**; "
                       f"Min: **{mm['min']}**, Max: **{mm['max']}**")

    c1, c2 = st.columns(2)
    reset = c1.button("Sıfırla", use_container_width=True, disabled=not has_data)
    apply = c2.button("Tətbiq et", use_container_width=True, disabled=not has_data)

    if has_data:
        if reset:
            st.session_state["df_clean"] = df_full.copy()
            st.session_state["active_filter_summary"] = "Hamısı"
            st.session_state["filter_initialized"] = False
            st.session_state["active_source_key"] = "R"
        elif apply:
            yrs = year_select if (year_mode=="Seçilən illər") else years_available
            mns = month_select if (month_mode=="Seçilən aylar") else AZ_MONTHS
            view = _apply_filter(df_full, src_key, yrs, mns)
            st.session_state["df_clean"] = view
            st.session_state["active_source_key"] = src_key
            parts = []
            parts.append("Mənbə: " + SOURCE_LABELS[src_key])
            parts.append("İl: " + (", ".join(map(str, yrs)) if yrs else "—"))
            parts.append("Ay: " + (", ".join(mns) if mns else "—"))
            st.session_state["active_filter_summary"] = " | ".join(parts)

    st.caption("Filtr **Tətbiq et** ilə aktiv olur. **Sıfırla** → Hamısı.")

df_full = st.session_state.get("df_clean_full")
if df_full is not None and len(df_full) > 0 and not st.session_state.get("filter_initialized"):
    st.session_state["filter_initialized"] = True
    src_key = st.session_state.get("active_source_key", "R")
    years_available = _get_years_from_source(df_full, src_key)
    latest_year = max(years_available) if years_available else None
    if latest_year:
        st.session_state["df_clean"] = _apply_filter(df_full, src_key, [latest_year], AZ_MONTHS)
        st.session_state["active_filter_summary"] = f"Mənbə: {SOURCE_LABELS[src_key]} | İl: {latest_year} | Ay: Hamısı"
    else:
        st.session_state["df_clean"] = df_full.copy()
        st.session_state["active_filter_summary"] = "Hamısı"

summary_text = st.session_state.get("active_filter_summary", "Hamısı")
st.success(f"Aktiv filtr: {summary_text}")
