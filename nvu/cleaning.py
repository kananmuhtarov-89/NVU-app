import re
from datetime import datetime
import pandas as pd
def coerce_str(x):
    if pd.isna(x): return None
    s = str(x).strip()
    s = re.sub(r"[\u200B-\u200D\uFEFF]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s if s else None
def normalize_code(s):
    s = coerce_str(s)
    if not s: return None
    return re.sub(r"[^A-Z0-9]", "", s.upper())
def load_excel(file):
    return pd.read_excel(file)
def dedup_dataframe(df, tehvil_col, tesdiq_col, nv_col):
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(coerce_str)
    for key in [tesdiq_col, tehvil_col, nv_col]:
        if key in df.columns:
            df[key+"_norm"] = df[key].map(normalize_code)
    deduped = df.copy()
    for key in [tehvil_col+"_norm", tesdiq_col+"_norm"]:
        if key in deduped.columns:
            grp = deduped.groupby(key, dropna=True, as_index=False, sort=False)
            try:
                deduped = grp.apply(lambda g: g.loc[g.notna().sum(axis=1).idxmax()], include_groups=False).reset_index(drop=True)
            except TypeError:
                deduped = grp.apply(lambda g: g.loc[g.notna().sum(axis=1).idxmax()]).reset_index(drop=True)
    return deduped
def dynamic_year_bins(series):
    years = pd.to_numeric(series, errors="coerce").dropna().astype(int)
    if years.empty: return pd.Series(dtype="object")
    current_year = datetime.now().year
    bins=[(1885,1950)]; start=1951
    while start<=current_year:
        end=min(start+9,current_year); bins.append((start,end)); start=end+1
    labels=[f"{a}–{b}" for (a,b) in bins]; cuts=bins
    def map_year(y):
        for (a,b),lab in zip(cuts,labels):
            if a<=y<=b: return lab
        if y<1885: return "≤1884"
        return f"{current_year}–{current_year}"
    return years.map(map_year)
