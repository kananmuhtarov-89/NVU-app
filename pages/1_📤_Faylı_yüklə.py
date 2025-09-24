import streamlit as st, os
import pandas as pd
from nvu.cleaning import load_excel, dedup_dataframe

st.title("1) Yüklə / Təmizlə")

def _norm(s: str) -> str:
    return (s or "").lower().replace("ı","i").replace("ə","e").replace("ö","o").replace("ü","u").replace("ş","s").replace("ç","c")

def _guess_date_column(df: pd.DataFrame):
    # Adında tarix sinonimləri olan sütunu öncəliklə seç
    candidates = []
    for c in df.columns:
        lc = _norm(str(c))
        if "tarix" in lc or "date" in lc or "daxil ol" in lc or "qebul" in lc or "teslim" in lc:
            candidates.append(c)
    if candidates:
        return candidates[0]
    # Fallback: tipcə datetime olan 1-ci sütun
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            return c
    return None

uploaded = st.file_uploader("Excel (.xlsx/.xls) yüklə", type=["xlsx","xls"])

if uploaded:
    df = load_excel(uploaded)
    st.write("Sətir sayı (xam):", len(df))

    df_clean = dedup_dataframe(df, "Təhvil aktının seriya nömrəsi", "Təsdiqedici sənədin seriyası", "NV qeydiyyat nömrəsi")

    # ---- DATE → il/ay sütunları ----
    month_map = {1:"Yanvar",2:"Fevral",3:"Mart",4:"Aprel",5:"May",6:"İyun",7:"İyul",8:"Avqust",9:"Sentyabr",10:"Oktyabr",11:"Noyabr",12:"Dekabr"}
    date_col = _guess_date_column(df_clean)
    if date_col:
        dt = pd.to_datetime(df_clean[date_col], errors="coerce", dayfirst=True)
        df_clean["il"] = dt.dt.year
        df_clean["ay_no"] = dt.dt.month
        df_clean["ay_ad"] = df_clean["ay_no"].map(month_map)
        df_clean["il_ay"] = dt.dt.strftime("%Y-%m")
        st.caption(f"Tarix sütunu aşkarlandı: **{date_col}** → il/ay sütunları əlavə olundu.")
        st.session_state["date_column_used"] = date_col
    else:
        st.warning("Tarix sütunu tapılmadı. İl/Ay filtri tarixsiz sətirlərdə işləməyəcək.")

    # Full və görünüş kopyaları
    st.session_state["df_clean_full"] = df_clean.copy()
    st.session_state["df_clean"] = df_clean

    st.success(f"Təmizləndi. Sətirlər (təmiz): {len(df_clean)}")
    st.session_state["source_filename"] = uploaded.name
    st.dataframe(df_clean.head(50), use_container_width=True)

    # Tez yoxlama: illərə görə paylanma
    if "il" in df_clean.columns:
        counts = df_clean["il"].value_counts(dropna=True).sort_index()
        if not counts.empty:
            st.write("**İllərə görə sətir sayı:**")
            st.bar_chart(counts)
else:
    st.info("Fayl yükləyin.")

