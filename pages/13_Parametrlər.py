import streamlit as st

st.title("⚙️ Parametrlər")

# ---- Top-N Parametrləri ----
st.markdown("#### 🔝 Top-N göstəriciləri")

st.session_state.setdefault("param_topN_erizeci", 20)
st.session_state.setdefault("param_topN_marka", 20)
st.session_state.setdefault("param_topN_model", 20)
st.session_state.setdefault("param_topN_reng", 20)

col1, col2 = st.columns(2)
with col1:
    st.session_state["param_topN_erizeci"] = st.number_input("Ərizəçi Top-N", 5, 100, st.session_state["param_topN_erizeci"])
    st.session_state["param_topN_model"] = st.number_input("Model Top-N", 5, 100, st.session_state["param_topN_model"])
with col2:
    st.session_state["param_topN_marka"] = st.number_input("Marka Top-N", 5, 100, st.session_state["param_topN_marka"])
    st.session_state["param_topN_reng"] = st.number_input("Rəng Top-N", 5, 100, st.session_state["param_topN_reng"])

# ---- Digər Parametrlər ----
st.markdown("#### ⚙️ Digər parametrlər")

# Variant 1: default = blanklar göstərilmir
st.session_state.setdefault("param_include_blanks", False)
st.session_state["param_include_blanks"] = st.toggle(
    "Boş sətrləri göstər (tövsiyə olunmur)", st.session_state["param_include_blanks"]
)

st.info("Top-N dəyərləri UI və Word hesabatında eyni tətbiq olunur. Blank sətrlər default olaraq gizlədilir.")
