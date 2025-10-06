import math
import pandas as pd

# -------------------------
# NVU – Cleaning & Utils
# -------------------------

# Boş (blank) sayılan markerlər
BLANK_MARKERS = {None, "", " ", "-", "—", "–", "NA", "N/A", "None", "\xa0"}

def _is_blank(value) -> bool:
    """Hüceyrənin boş olub-olmadığını yoxlayır."""
    if pd.isna(value):
        return True
    v = str(value).replace("\u00A0", " ").strip()  # NBSP -> space
    return v in BLANK_MARKERS

# Geri uyğunluq: bəzi modullar bu funksiyanı import edir (məs., regions.py)
def coerce_str(value) -> str:
    """
    Dəyəri təmiz string-ə çevirir. Blank markerlər üçün "" qaytarır.
    """
    if pd.isna(value):
        return ""
    s = str(value).replace("\u00A0", " ").strip()
    return "" if s in BLANK_MARKERS else s

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

# -------------------------
# 10 illik intervallar (vahid mənbə)
# -------------------------

def decade_label(year: int) -> str:
    """İli klassik dekad aralığına çevirir (1970–1979 və s.)."""
    try:
        year = int(year)
    except (ValueError, TypeError):
        return "Naməlum"
    start = int(year // 10 * 10)
    end = start + 9
    return f"{start}-{end}"

def to_decade_bins(series: pd.Series) -> pd.Series:
    """Series üzərində decade_label tətbiqi (NaN -> Naməlum)."""
    return series.apply(lambda y: decade_label(y) if pd.notna(y) else "Naməlum")
