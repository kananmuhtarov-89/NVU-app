from .cleaning import coerce_str


BRAND_MAPPING = {
    # VAZ / Lada
    "vaz": "Lada/VAZ",
    "lada": "Lada/VAZ",

    # GAZ
    "gaz": "GAZ",
    "volqa gaz-24": "GAZ",
    "m 21 v": "GAZ",
    "m21v": "GAZ",

    # Mercedes
    "mercedes": "Mercedes-Benz",
    "daimler": "Mercedes-Benz",
    "daimler benz": "Mercedes-Benz",

    # Digər yazılış uyğunlaşdırmaları
    "kamaz": "KAMAZ",
    "zil": "ZIL",
    "zİl": "ZIL",
    "zıl": "ZIL",

    "ij": "İJ",
    "ij": "İJ",
    "ij-": "İJ",
    "ij ": "İJ",
    "i̇j": "İJ",

    "eraz": "YERAZ",
    "yeraz": "YERAZ",

    "kavz": "KAVZ",
    "kavz": "KAVZ",

    # Samand / Khazar ailəsi
    "azsamand": "Iran Khodro/Samand",
    "samand": "Iran Khodro/Samand",
    "khazar": "Iran Khodro/Samand",
    "iran khodro": "Iran Khodro/Samand",

    # Kiçik standartlaşdırmalar
    "dongfeng": "Dongfeng",
    "dongfeng": "Dongfeng",
    "faw": "FAW",
    "howo": "HOWO",
    "daf": "DAF",
    "man": "MAN",
    "maz": "MAZ",
    "uaz": "UAZ",
    "mmz": "MMZ",
    "saz": "SAZ",
    "paz": "PAZ",
    "raf": "RAF",
    "zaz": "ZAZ",
    "byd": "BYD",
    "jac": "JAC",
    "mg": "MG",
}


def clean_brand_key(x):
    s = coerce_str(x).lower()
    s = s.replace("İ", "i").replace("ı", "i")
    s = s.replace("ə", "e").replace("ö", "o").replace("ü", "u")
    s = s.replace("ğ", "g").replace("ş", "s").replace("ç", "c")
    s = " ".join(s.split())
    return s


def normalize_brand(x):
    key = clean_brand_key(x)

    if not key:
        return None

    return BRAND_MAPPING.get(key, coerce_str(x))
