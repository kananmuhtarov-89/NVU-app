
import re, pandas as pd
from datetime import datetime
from .settings import CANON_COLS

def qc_report(df: pd.DataFrame, colmap: dict, dedup_keys: list[str]) -> dict:
    issues = {}
    missing = [c for c in CANON_COLS if c not in colmap.values()]
    issues["Çatışmayan sütunlar"] = pd.DataFrame({"Sütun": missing}) if missing else pd.DataFrame(columns=["Sütun"])
    empty_counts = {}
    for canon, real in colmap.items():
        if real in df.columns:
            empty_counts[canon] = int(df[real].isna().sum())
    issues["Boş dəyərlər"] = pd.DataFrame([{"Sütun":k,"Boş say":v} for k,v in empty_counts.items()]).sort_values("Boş say", ascending=False) if empty_counts else pd.DataFrame(columns=["Sütun","Boş say"])
    year_col = colmap.get("Buraxılış ili")
    year_df = pd.DataFrame(columns=["Sətir","Dəyər","Problem"])
    if year_col and year_col in df.columns:
        yrs = pd.to_numeric(df[year_col], errors="coerce")
        bad = df[yrs < 1885].index.tolist()
        bad2 = df[yrs > datetime.now().year].index.tolist()
        rows = []
        for i in bad: rows.append({"Sətir": i, "Dəyər": df.loc[i, year_col], "Problem": "<1885"})
        for i in bad2: rows.append({"Sətir": i, "Dəyər": df.loc[i, year_col], "Problem": ">cari il"})
        year_df = pd.DataFrame(rows)
    issues["Şübhəli illər"] = year_df
    nv_col = colmap.get("NV qeydiyyat nömrəsi")
    nv_df = pd.DataFrame(columns=["Sətir","Dəyər","Problem"])
    if nv_col and nv_col in df.columns:
        bad_nv_idx = df[~df[nv_col].astype(str).str.contains(r"\d", na=True)].index.tolist()
        nv_df = pd.DataFrame([{"Sətir": i, "Dəyər": df.loc[i, nv_col], "Problem": "format / rəqəm yoxdur"} for i in bad_nv_idx])
    issues["NV formatı"] = nv_df
    dup_rows = pd.DataFrame(columns=["Açar kombinasiya","Sətir sayı"])
    keys = [colmap.get(k) for k in dedup_keys if colmap.get(k) in df.columns]
    if keys:
        dup = df[keys].astype(str).fillna("").duplicated(keep=False)
        if dup.any():
            g = df[dup].groupby(keys).size().reset_index(name="Sətir sayı").sort_values("Sətir sayı", ascending=False)
            g["Açar kombinasiya"] = g[keys].agg(" | ".join, axis=1)
            dup_rows = g[["Açar kombinasiya","Sətir sayı"]]
    issues["Təkrarlanan açarlar"] = dup_rows
    return issues
