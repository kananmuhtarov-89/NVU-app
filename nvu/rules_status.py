import re, pandas as pd
from .cleaning import coerce_str
ALLOWED_3 = ["Ləğv edilmiş","Təsdiqedici sənəd yükləndi"]
ALLOWED_4 = ["Qüvvədən düşmüş","Ləğv edilmiş","Sənəd yükləndi"]
def _fold_az_lower(s):
    if s is None: return None
    s = coerce_str(s); 
    if s is None: return None
    s = s.lower()
    for k,v in {"ə":"e","ö":"o","ü":"u","ş":"s","ç":"c","ğ":"g","ı":"i","i̇":"i","ï":"i"}.items():
        s = s.replace(k,v)
    return re.sub(r"\s+"," ",s).strip()
_STATUS_CANON_MAP = {
    "legv edilmis":"Ləğv edilmiş","tesdiqedici sened yuklendi":"Təsdiqedici sənəd yükləndi",
    "quvveden dusmus":"Qüvvədən düşmüş","sened yuklendi":"Sənəd yükləndi",
}
for _lab in set(ALLOWED_3+ALLOWED_4):
    _STATUS_CANON_MAP.setdefault(_fold_az_lower(_lab), _lab)
def normalize_status(s):
    if s is None: return None
    folded = _fold_az_lower(s)
    return _STATUS_CANON_MAP.get(folded, coerce_str(s))
def status_totals(series, allowed):
    s = series.map(normalize_status); vc = s.value_counts()
    return pd.DataFrame([{"Status":lab,"Say":int(vc.get(lab,0))} for lab in allowed])
