import json, re
from .cleaning import coerce_str
def load_region_map(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
def extract_region_from_nv(nv: str, region_map: dict):
    s = coerce_str(nv)
    if not s: return None, None
    if re.match(r"^\s*077", s): code="077"
    elif re.match(r"^\s*099", s): code="099"
    else:
        m2 = re.match(r"^\s*(\d{2})", s) or re.search(r"(\d{2})", s)
        code = m2.group(1) if m2 else None
    if not code: return None, None
    region = region_map.get(code)
    if region is None and len(code)==2 and re.match(r"^\s*0(\d{2})", s or ""):
        code3="0"+code; region=region_map.get(code3); 
        if region: code=code3
    if region is None: region=f"Bilinmir (kod {code})"
    return code, region
