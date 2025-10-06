# pages/2_Tesnifatlar_uzre.py
import re
import pandas as pd
import streamlit as st

df = st.session_state.get("df_clean")
if df is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()

st.title("2) Təsnifatlar üzrə")

# ---- NK №61 xəritəsi ----
CLASS_INFO_BASE = {
    "M1": ("Oturacaq yerləri (sürücüdən əlavə) ≤ 8 — sərnişin", 1500),
    "M2": ("> 8 yer, icazə verilən kütlə ≤ 5 t — sərnişin", 2000),
    "M3": ("> 5 t — sərnişin", 3000),
    "N1": ("İcazə verilən kütlə ≤ 3.5 t — yük", 1500),
    "N2": ("3.5–12 t — yük", 2000),
    "N3": ("> 12 t — yük", 3000),
    "T":  ("Traktorlar (təkərli)", 2000),
    "TK": ("Traktorlar (tırtıllı)", 2000),
    "TT": ("Traktorlar (digər)", 2000),
    "H":  ("Özügedən maşınlar (mexaniki ötürücülü)", 3000),
    "HT": ("Özügedən maşınlar (hidrostatik ötürücülü)", 3000),
    "HK": ("Meliorasiya/yol-tikinti maşınları, ekskavatorlar", 3000),
    "L":  ("Kvadrisikllər və təkərləri dörddən az olanlar", 200),
}
GABLE = {"M1","M2","M3","N1","N2","N3"}

CLASS_INFO_FULL = CLASS_INFO_BASE.copy()
for b in GABLE:
    desc, amt = CLASS_INFO_BASE[b]
    CLASS_INFO_FULL[b+"G"] = (desc+" (yolsuzluq)", amt)

VALID_CODES = sorted(CLASS_INFO_FULL.keys(), key=len, reverse=True)

def extract_code(val: str) -> str:
    s = str(val).upper().strip()
    for bad in ("TƏSNİFATI","TƏSNIFATI","TESNIFATI","TƏSNİFATİ","TƏSNİFAT"):
        s = s.replace(bad, "")
    s = s.strip()
    token = re.split(r"[\s\-/_,]+", s)[0] if s else ""
    for c in VALID_CODES:
        if s.startswith(c) or token.startswith(c):
            return c
    return token

def normalize_g(code: str) -> str:
    x = str(code).upper()
    return x[:-1] if x.endswith("G") and x[:-1] in GABLE else x

# ---- Defaults: toggle-lar ilk dəfə ON gəlsin ----
if "tesnifat_merge" not in st.session_state:
    st.session_state["tesnifat_merge"] = True
if "tesnifat_calc" not in st.session_state:
    st.session_state["tesnifat_calc"] = True

merge_g = st.toggle("**Təsnifatları birləşdir** (M1+M1G, N1+N1G, ...)",
                    key="tesnifat_merge", value=st.session_state["tesnifat_merge"])
calc_amounts = st.toggle("**Məbləğləri hesabla** (Cəmi AZN sütunu)",
                         key="tesnifat_calc", value=st.session_state["tesnifat_calc"])

# ---- Hesablama ----
COL = "Təsnifat"
if COL not in df.columns:
    st.error(f"'{COL}' sütunu tapılmadı.")
    st.stop()

tmp = df.copy()
tmp["Kod"] = tmp[COL].apply(extract_code)
if merge_g:
    tmp["Kod"] = tmp["Kod"].apply(normalize_g)

# sayım
tbl = (tmp["Kod"]
       .dropna().astype(str).str.strip().str.upper()
       .value_counts()
       .rename_axis("Kod")
       .reset_index(name="Say"))

class_map = CLASS_INFO_BASE if merge_g else CLASS_INFO_FULL
map_df = (pd.DataFrame.from_dict(class_map, orient="index",
                                 columns=["Açıqlama","Güzəşt (AZN)"])
          .reset_index().rename(columns={"index":"Kod"}))
tbl = tbl.merge(map_df, on="Kod", how="left")
tbl["Açıqlama"] = tbl["Açıqlama"].fillna("Rəsmi siyahıda yoxdur")
tbl["Güzəşt (AZN)"] = tbl["Güzəşt (AZN)"].fillna(0).astype(int)

if calc_amounts:
    tbl["Cəmi (AZN)"] = tbl["Say"] * tbl["Güzəşt (AZN)"]
    show_cols = ["Kod","Açıqlama","Güzəşt (AZN)","Say","Cəmi (AZN)"]
else:
    show_cols = ["Kod","Açıqlama","Güzəşt (AZN)","Say"]

tbl = tbl.sort_values("Say", ascending=False)[show_cols].reset_index(drop=True)

# KPI-lar
c1, c2, c3 = st.columns(3)
c1.metric("Sətir sayı", f"{len(tbl):,}".replace(","," "))
c2.metric("Ümumi NV", f"{len(tmp):,}".replace(","," "))
if calc_amounts and "Cəmi (AZN)" in tbl.columns:
    c3.metric("Ümumi məbləğ (AZN)", f"{int(tbl['Cəmi (AZN)'].sum()):,}".replace(","," "))

st.dataframe(tbl, use_container_width=True)

# ---- Export üçün minimal cədvəl (Açıqlama çıxarılır) ----
tbl_export = tbl.copy()
if "Cəmi (AZN)" in tbl_export.columns:
    tbl_export = tbl_export[["Kod","Say","Cəmi (AZN)"]]
else:
    tbl_export = tbl_export[["Kod","Say"]]

st.session_state["tesnifat_table"] = tbl_export
st.session_state["tesnifat_merge"] = merge_g
st.session_state["tesnifat_calc"] = calc_amounts

# CSV endirmə (opsional)
st.download_button("CSV kimi endir",
                   data=tbl_export.to_csv(index=False).encode("utf-8-sig"),
                   file_name="tesnifatlar.csv", mime="text/csv")
