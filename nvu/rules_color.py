import re
import unicodedata


def coerce_str(x):
    if x is None:
        return ""
    return str(x).strip()


def clean_color_key(x):
    """
    Rəng adını müqayisə üçün standart formaya salır.
    Məsələn:
    'Qırmızı metallik' -> 'qirmizi'
    'Gümüşü metal' -> 'gumusu'
    """
    s = coerce_str(x).lower()

    # Azərbaycan hərflərini sadələşdiririk
    replacements = {
        "ə": "e",
        "ı": "i",
        "ö": "o",
        "ü": "u",
        "ğ": "g",
        "ş": "s",
        "ç": "c",
    }

    for a, b in replacements.items():
        s = s.replace(a, b)

    # lazımsız sözləri silirik
    remove_words = [
        "metallik",
        "metallic",
        "metal",
        "sedef",
        "perlam",
        "xett",
        "mat",
    ]

    for word in remove_words:
        s = re.sub(rf"\b{word}\b", " ", s)

    s = re.sub(r"\s+", " ", s).strip()
    return s


COLOR_MAPPING = {
    # Ağ qrupu
    "ag": "Ağ",
    "aciq ag": "Ağ",
    "parlaq ag": "Ağ",
    "ag mirvari": "Ağ",
    "elvan ag": "Ağ",
    "beyaz gece": "Ağ",
    "qar kralicasi": "Ağ",
    "fil sumuyu": "Ağ",
    "sud": "Ağ",
    "kremli": "Ağ",

    # Qara qrupu
    "qara": "Qara",

    # Boz qrupu
    "boz": "Boz",
    "aciq boz": "Boz",
    "tund boz": "Boz",
    "yas asfalt": "Boz",
    "tustu": "Boz",
    "aciq tustu": "Boz",
    "qrafit": "Boz",
    "sero beliy": "Boz",
    "siklon": "Boz",

    # Gümüşü qrupu
    "gumusu": "Gümüşü",
    "silver": "Gümüşü",
    "tund gumusu": "Gümüşü",

    # Göy / mavi qrupu
    "goy": "Göy",
    "mavi": "Göy",
    "aciq goy": "Göy",
    "aciq mavi": "Göy",
    "tund goy": "Göy",
    "tund mavi": "Göy",
    "boz mavi": "Göy",
    "boz goy": "Göy",
    "goy gece yarisi": "Göy",
    "mavi adriatika": "Göy",
    "goy valentin": "Göy",
    "akvamarin": "Göy",
    "medeo": "Göy",
    "baltika": "Göy",
    "atlantika": "Göy",
    "bosfor": "Göy",
    "qolfstrim": "Göy",
    "vasilkoviy": "Göy",
    "deniz dalgasi": "Göy",
    "delfin": "Göy",
    "laguna": "Göy",
    "firuzeyi": "Göy",

    # Yaşıl qrupu
    "yasil": "Yaşıl",
    "aciq yasil": "Yaşıl",
    "tund yasil": "Yaşıl",
    "zeytun": "Yaşıl",
    "zumrud": "Yaşıl",
    "xaki": "Xaki",
    "mudafie": "Xaki",
    "pitsunda": "Yaşıl",
    "polevoy": "Yaşıl",
    "liana yasil": "Yaşıl",
    "lipa yasil": "Yaşıl",
    "yasil bag": "Yaşıl",
    "salatoviy": "Yaşıl",
    "flora": "Yaşıl",
    "avanturin": "Yaşıl",

    # Sarı qrupu
    "sari": "Sarı",
    "aciq sari": "Sarı",
    "solgun sari": "Sarı",
    "parlaq sari": "Sarı",
    "limon": "Sarı",
    "mimoza": "Sarı",
    "primula": "Sarı",
    "sari primula": "Sarı",
    "sari prim": "Sarı",

    # Qırmızı qrupu
    "qirmizi": "Qırmızı",
    "tund qirmizi": "Qırmızı",
    "parlaq qirmizi": "Qırmızı",
    "rubin": "Qırmızı",
    "albali": "Qırmızı",
    "visnoviy": "Qırmızı",
    "gilənar": "Qırmızı",
    "gilenar": "Qırmızı",
    "nar": "Qırmızı",
    "bordo": "Qırmızı",
    "tund bordo": "Qırmızı",
    "tund zogali": "Qırmızı",
    "korrida": "Qırmızı",
    "al": "Qırmızı",
    "qirmizi nar": "Qırmızı",

    # Narıncı qrupu
    "narinci": "Narıncı",
    "qirmizi narinci": "Narıncı",
    "terrokati": "Narıncı",

    # Bej qrupu
    "bej": "Bej",
    "aciq bej": "Bej",
    "tund bej": "Bej",
    "solgun bej": "Bej",
    "qum": "Bej",
    "qumlu": "Bej",
    "pesocni": "Bej",
    "safari": "Bej",
    "seh ra": "Bej",
    "sehra": "Bej",
    "qobi": "Bej",

    # Qızılı qrupu
    "qizili": "Qızılı",
    "qizil runo": "Qızılı",
    "oxra qizili": "Qızılı",
    "qizili oxra": "Qızılı",
    "oxra": "Qızılı",

    # Qəhvəyi qrupu
    "qehveyi": "Qəhvəyi",
    "aciq qehveyi": "Qəhvəyi",
    "tund qehveyi": "Qəhvəyi",
    "t koriç": "Qəhvəyi",
    "t koric": "Qəhvəyi",
    "tund palidi": "Qəhvəyi",

    # Bənövşəyi qrupu
    "benovseyi": "Bənövşəyi",
    "yasemen": "Bənövşəyi",
    "tund yasemen": "Bənövşəyi",
    "badimcan": "Bənövşəyi",
    "murena": "Bənövşəyi",
}


def normalize_color(c):
    """
    Tanınan rəngi standart qrupa salır.
    Tanınmayan bütün rəngləri 'Digər' qaytarır.
    """
    key = clean_color_key(c)

    if not key:
        return "Digər"

    if key in COLOR_MAPPING:
        return COLOR_MAPPING[key]

    return "Digər"
