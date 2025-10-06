import math
import pandas as pd

# -------------------------
# NVU Utility Functions
# -------------------------

BLANK_MARKERS = {None, "", " ", "-", "—", "–", "NA", "N/A", "None", "\xa0"}

def _is_blank(value):
    """Hüceyrənin boş olub-olmadığını yoxlayır."""
    if pd.isna(value):
        return True
    v = str(value).strip()
    return v in BLANK_MARKERS

def clean_column_names(df):
    df.columns = [c.strip() for c in df.columns]
    return df

# -------------------------
# NVU 10 illik interval funksiyası (vahid mənbə)
# -------------------------

def decade_label(year: int) -> str:
    """Verilən ili 10 illik intervala çevirir (1970–1979 və s.)"""
    try:
        year = int(year)
    except (ValueError, TypeError):
        return "Naməlum"
    start = int(year // 10 * 10)
    end = start + 9
    return f"{start}-{end}"

def to_decade_bins(series):
    """Series üzərində decade_label tətbiqi"""
    return series.apply(lambda y: decade_label(y) if pd.notna(y) else "Naməlum")
