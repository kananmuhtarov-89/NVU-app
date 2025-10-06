# pages/2_Tesnifatlar_uzre.py
import streamlit as st
import pandas as pd
from nvu.sections import section2_tesnifat  # sənin sayım funksiyanı istifadə edirik

df = st.session_state.get("df_clean")
if df is None:
    st.warning("İlk öncə **1) Yüklə / Təmizlə** səhifəsində Excel yükləyin.")
    st.stop()

st.title("2) Təsnifatlar üzrə")

COL = "Təsnifat"
if COL not in df.columns:
    st.error(f"'{COL}' sütunu tapılmadı.")
    st.stop()

# NK №61 (31.01.2024), 2 №-li əlavəyə uyğun qısa izah + güzəşt məbləği (AZN)
CLASS_INFO_BASE = {
    # Sərnişindaşıma
    "M1": ("Oturacaq yerləri (sürücüdən əlavə) ≤ 8 — sərnişin", 1500),
    "M2": ("> 8 yer, icazə verilən kütlə ≤ 5 t — sərnişin", 2000),
    "M3": ("> 5 t — sərnişin", 3000),
    # Yükdaşıma
    "N1": ("İcazə verilən kütlə ≤ 3.5 t — yük", 1500),
    "N2": ("3.5–12 t — yük", 2000),
    "N3": ("> 12 t — yük", 3000),
    # Traktor / xüsusi texnika
    "T":  ("Traktorlar (təkərli)", 2000),
    "TK": ("Traktorlar (tırtıllı)", 2000),
    "TT": ("Traktorlar (digər)", 2000),
    "H":  ("Özügedən maşınlar (mexaniki ötürücülü)", 3000),
    "HT": ("Özügedən maşınlar (hidrostatik ötürücülü)", 3000),
    "HK": ("Meliorasiya/yol-tikinti maşınları, ekskavatorlar", 3000),
    # Digər
    "L":  ("Kvadrisikllər və təkərləri dörddən az olanlar", 200),
}

# G-variantları olan siniflər
_GABLE = {"M1", "M2", "M3", "N1", "N2", "N3"}

# FULL xəritə: BASE + G variantları (eyni məbləğ, açıqlamada "(yolsuzluq)")
CLASS_INFO_FULL = CLASS_INFO_BASE.copy()
for base in _GABLE:
    desc, amt = CLASS_INFO_BASE[base]
    CLASS_INFO_FULL[base + "G"] = (desc + " (yolsuzluq)", amt)

def normalize_g(code: str) -> str:
    s = str(code).strip().upper()
    if s.endswith("G") and s[:-1] in _GABLE:
        return s[:-1]
    return s

# ---- UI idarələri ----
merge_g = st.toggle("**G variantlarını birləşdir** (M1+M1G, N1+N1G, ...)", value=True)
calc_amounts = st.toggle("**Məbləğləri hesabla** (Cəmi AZN sütunu)", value=False)

# ---- Sayım (sənin funksiyanla) ----
if merge_g:
    tmp = df.copy()
    norm_col = "_Kod_norm"
    tmp[norm_col] = tmp[COL].astype(str).apply(normalize_g)
    tbl = section2_tesnifat(tmp, norm_col).copy()   # sütunlar: _Kod_norm, Say
    src_col = norm_col
    class_map = CLASS_INFO_BASE
else:
    tbl = section2_tesnifat(df, COL).copy()         # sütunlar: Təsnifat, Say
    src_col = COL
    class_map = CLASS_INFO_FULL

tbl.rename(columns={src_col: "Kod"}, inplace=True)
tbl["Kod"] = tbl["Kod"].astype(str).str.strip().str.upper()

# ---- Açıqlama və Güzəşt sütunları əlavə et ----
map_df = pd.DataFrame.from_dict(class_map, orient="index", columns=["Açıqlama", "Güzəşt (AZN)"]).reset_index().rename(columns={"index": "Kod"})
tbl = tbl.merge(map_df, on="Kod", how="left")
tbl["Açıqlama"] = tbl["Açıqlama"].fillna("Rəsmi siyahıda yoxdur")
tbl["Güzəşt (AZN)"] = tbl["Güzəşt (AZN)"].fillna(0).astype(int)

# ---- Məbləğ hesablanması (opsional) ----
if calc_amounts:
    tbl["Cəmi (AZN)"] = tbl["Say"] * tbl["Güzəşt (AZN)"]
    show_cols = ["Kod", "Açıqlama", "Güzəşt (AZN)", "Say", "Cəmi (AZN)"]
else:
    show_cols = ["Kod", "Açıqlama", "Say"]

# Sıralama: Say azalan
tbl = tbl.sort_values(by="Say", ascending=False)[show_cols].reset_index(drop=True)

# ---- KPI-lar ----
c1, c2, c3 = st.columns(3)
c1.metric("Sətir sayı", f"{len(tbl):,}".replace(",", " "))
total_nv = int(section2_tesnifat(df, COL)["Say"].sum())
c2.metric("Ümumi NV (filtrdən sonra)", f"{total_nv:,}".replace(",", " "))
if calc_amounts and "Cəmi (AZN)" in tbl:
    c3.metric("Ümumi məbləğ (AZN)", f"{int(tbl['Cəmi (AZN)'].sum()):,}".replace(",", " "))

# ---- Cədvəl və endirmə ----
st.dataframe(tbl, use_container_width=True)
st.download_button("CSV kimi endir", data=tbl.to_csv(index=False).encode("utf-8-sig"),
                   file_name="tesnifatlar.csv", mime="text/csv")
