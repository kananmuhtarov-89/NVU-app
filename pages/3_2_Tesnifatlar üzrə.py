import re
import pandas as pd
import streamlit as st

# -----------------------------------------------
# Data
# -----------------------------------------------
df = st.session_state.get("df_clean")
if df is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()

st.title("2) Təsnifatlar üzrə")

COL = "Təsnifat"
if COL not in df.columns:
    st.error(f"'{COL}' sütunu tapılmadı.")
    st.stop()

# NK №61 – qısa izah + güzəşt (AZN)
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
_GABLE = {"M1","M2","M3","N1","N2","N3"}

# FULL xəritə (G variantları)
CLASS_INFO_FULL = CLASS_INFO_BASE.copy()
for b in _GABLE:
    d, a = CLASS_INFO_BASE[b]
    CLASS_INFO_FULL[b+"G"] = (d+" (yolsuzluq)", a)

VALID_CODES = sorted(CLASS_INFO_FULL.keys(), key=len, reverse=True)

def extract_code(val: str) -> str:
    """'M1 TƏSNİFATI' → 'M1', 'M1G TƏSNİFATI' → 'M1G', 'TK TƏSNİFATI' → 'TK'."""
    s = str(val).upper().strip()
    s = (s
         .replace("TƏSNİFATI","")
         .replace("TƏSNIFATI","")
         .replace("TESNIFATI","")
         .replace("TƏSNİFATİ","")
         .replace("TƏSNİFAT","")).strip()
    token = re.split(r"[\s\-/_,]+", s)[0] if s else ""
    for c in VALID_CODES:                 # ən uzun kodu öncə yoxla (TK, HT, HK …)
        if s.startswith(c) or token.startswith(c):
            return c
    return token

def normalize_g(code: str) -> str:
    x = str(code).upper()
    return x[:-1] if x.endswith("G") and x[:-1] in _GABLE else x

# ---- UI toggles ----
merge_g = st.toggle("**Təsnifatlar üzrə birləşdir** (M1+M1G, N1+N1G, ...)", value=True)
calc_amounts = st.toggle("**Məbləğləri hesabla** (Cəmi AZN sütunu)", value=False)

# Kodları çıxar
tmp = df.copy()
tmp["_Kod"] = tmp[COL].apply(extract_code)
if merge_g:
    tmp["_Kod"] = tmp["_Kod"].apply(normalize_g)

# Sayım
tbl = (tmp["_Kod"]
       .dropna()
       .astype(str)
       .str.strip()
       .str.upper()
       .value_counts()
       .rename_axis("Kod")
       .reset_index(name="Say"))

# Xəritə seçimi
class_map = CLASS_INFO_BASE if merge_g else CLASS_INFO_FULL
map_df = pd.DataFrame.from_dict(class_map, orient="index",
                                columns=["Açıqlama", "Güzəşt (AZN)"]).reset_index().rename(columns={"index":"Kod"})
tbl = tbl.merge(map_df, on="Kod", how="left")
tbl["Açıqlama"] = tbl["Açıqlama"].fillna("Rəsmi siyahıda yoxdur")
tbl["Güzəşt (AZN)"] = tbl["Güzəşt (AZN)"].fillna(0).astype(int)

if calc_amounts:
    tbl["Cəmi (AZN)"] = tbl["Say"] * tbl["Güzəşt (AZN)"]
    show_cols = ["Kod", "Açıqlama", "Güzəşt (AZN)", "Say", "Cəmi (AZN)"]
else:
    show_cols = ["Kod", "Açıqlama", "Say"]

tbl = tbl.sort_values("Say", ascending=False)[show_cols].reset_index(drop=True)

# KPI
c1, c2, c3 = st.columns(3)
c1.metric("Sətir sayı", f"{len(tbl):,}".replace(","," "))
total_nv = len(tmp)                                  # filtrdən sonra sətirlər
c2.metric("Ümumi NV (filtrdən sonra)", f"{total_nv:,}".replace(","," "))
if calc_amounts and "Cəmi (AZN)" in tbl:
    c3.metric("Ümumi məbləğ (AZN)", f"{int(tbl['Cəmi (AZN)'].sum()):,}".replace(","," "))

st.dataframe(tbl, use_container_width=True)

# ---- Export üçün session-a yaz ----
tbl_export = tbl.rename(columns={"Kod": "Təsnifat"}).copy()
st.session_state["tesnifat_merge"] = merge_g
st.session_state["tesnifat_calc"] = calc_amounts
# Word/XLSX üçün lazımsız "Açıqlama" sütununu saxlamırıq
if "Açıqlama" in tbl_export.columns and calc_amounts:
    tbl_export = tbl_export[["Təsnifat","Say","Cəmi (AZN)"]]
elif "Açıqlama" in tbl_export.columns:
    tbl_export = tbl_export[["Təsnifat","Say"]]
st.session_state["tesnifat_table"] = tbl_export
st.session_state["tesnifat_total_count"] = int(tbl_export["Say"].sum())
st.session_state["tesnifat_total_amount"] = (int(tbl_export["Cəmi (AZN)"].sum())
                                             if calc_amounts and "Cəmi (AZN)" in tbl_export else None)

# CSV endirmə (opsional)
st.download_button("CSV kimi endir",
                   data=tbl_export.to_csv(index=False).encode("utf-8-sig"),
                   file_name="tesnifatlar.csv", mime="text/csv")
