import re
from .cleaning import coerce_str
RUSSIAN_MAKES = {"VAZ","LADA","VOLGA","GAZ","UAZ","MOSKVICH","MOSKVİÇ","MOSKVIC","MOSKVİCH"}
FAMILY_PATTERNS = [
    ("VAZ-2101 qrup", {"VAZ","LADA"}, re.compile(r"\b(2101|21011|21013)\b")),
    ("VAZ-2103/2105/2107 qrup", {"VAZ","LADA"}, re.compile(r"\b(2103|2105|2107|21074)\b")),
    ("VAZ-2106 qrup", {"VAZ","LADA"}, re.compile(r"\b(2106|21061|21063|21065)\b")),
    ("VAZ Niva qrup", {"VAZ","LADA"}, re.compile(r"\b(2121|21213|21214|2131|NIVA)\b")),
    ("GAZ Volqa qrup", {"GAZ","VOLGA"}, re.compile(r"\b(GAZ[\s\-]?(21|24|2410|3102|3110)|VOLGA)\b")),
    ("UAZ qrup", {"UAZ"}, re.compile(r"\b(469|HUNTER|PATRIOT|452|BUKHANKA|BUXANKA)\b", re.IGNORECASE)),
    ("Moskvich qrup", {"MOSKVICH","MOSKVİÇ","MOSKVIC","MOSKVİCH"}, re.compile(r"\b(408|412|2140|ALEKO)\b")),
]
def normalize_model(marka, model):
    mk = (coerce_str(marka) or "").upper()
    md = (coerce_str(model) or "").upper()
    if mk in RUSSIAN_MAKES:
        for label, marka_set, pat in FAMILY_PATTERNS:
            if mk in marka_set and pat.search(md or ""):
                return label
    md = re.sub(r"[-\s_]+"," ", md).strip()
    return md or None
