
import pandas as pd
from .settings import get_settings

def canon_map(series: pd.Series, dict_key: str) -> pd.Series:
    cfg = get_settings()
    sd = cfg.get("status_dict",{}).get(dict_key,{})
    rev = {}
    for canon, alts in sd.items():
        rev[canon] = canon
        for a in alts:
            rev[str(a).strip().lower()] = canon
    def map_one(x):
        if pd.isna(x): return None
        s = str(x).strip()
        key = s.lower()
        return rev.get(key, s)
    return series.map(map_one)
