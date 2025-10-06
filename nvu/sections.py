import pandas as pd
from .cleaning import normalize_code, dynamic_year_bins, coerce_str
from .rules_status import ALLOWED_3, ALLOWED_4, status_totals
from .rules_model import normalize_model
from .rules_color import normalize_color
from .regions import extract_region_from_nv
def section1_utilizator(df, col_utilizator, col_nv):
    tmp = df[[col_utilizator, col_nv]].copy()
    tmp[col_nv+"_norm"] = tmp[col_nv].map(normalize_code)
    tbl = (tmp.dropna(subset=[col_utilizator, col_nv+"_norm"])
              .drop_duplicates([col_utilizator, col_nv+"_norm"])
              .groupby(col_utilizator)[col_nv+"_norm"]
              .nunique()
              .reset_index(name="NV sayı"))
    return tbl.sort_values("NV sayı", ascending=False)
def section2_tesnifat(df, col_tesnifat):
    t2 = df[col_tesnifat].dropna().map(coerce_str).value_counts().reset_index()
    t2.columns = [col_tesnifat, "Say"]
    return t2
def section3_status_totals(df, col_status):
    return status_totals(df[col_status], ALLOWED_3)
def section4_status_totals(df, col_status):
    return status_totals(df[col_status], ALLOWED_4)
def section5_top50_erizeci(df, col_erizeci):
    t5 = df[col_erizeci].dropna().map(coerce_str).value_counts().head(50).reset_index()
    t5.columns = [col_erizeci, "Say"]
    t5.insert(0, "Sıra №", range(1, len(t5)+1))
    return t5
def section6_top20_marka(df, col_marka):
    t6 = df[col_marka].dropna().map(coerce_str).value_counts().head(20).reset_index()
    t6.columns = [col_marka, "Say"]
    return t6
def section7_top20_model(df, col_marka, col_model):
    tmp = df[[col_marka, col_model]].copy()
    tmp["Model (uyğunlaşdırılmış)"] = [normalize_model(a, b) for a,b in zip(tmp[col_marka], tmp[col_model])]
    t7 = tmp["Model (uyğunlaşdırılmış)"].dropna().value_counts().head(20).reset_index()
    t7.columns = ["Model (uyğunlaşdırılmış)", "Say"]
    return t7
def section8_top20_reng(df, col_reng):
    tmp = df[col_reng].map(normalize_color)
    t8 = tmp.dropna().value_counts().head(20).reset_index()
    t8.columns = ["Rəng (uyğunlaşdırılmış)", "Say"]
    return t8
def section9_region_counts(df, col_nv, region_map):
    codes = df[col_nv].map(lambda x: extract_region_from_nv(x, region_map)[1])
    t9 = codes.dropna().value_counts().reset_index()
    t9.columns = ["Region", "Say"]
    total = t9["Say"].sum()
    if total > 0:
        t9["Pay (%)"] = (t9["Say"] * 100 / total).round(2)
    return t9
def section10_year_bins(df, col_year):
    years_mapped = dynamic_year_bins(df[col_year])
    if years_mapped.empty:
        return pd.DataFrame(columns=["Yaş dövrü","Say"])
    t10 = years_mapped.value_counts().sort_index().reset_index()
    t10.columns = ["Yaş dövrü", "Say"]
    return t10
