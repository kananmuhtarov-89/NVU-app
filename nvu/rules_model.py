import re
from .cleaning import coerce_str


def clean_text(x):
    s = coerce_str(x) or ""
    s = s.upper()
    s = s.replace("İ", "I")
    s = s.replace("Ə", "E")
    s = s.replace("Ö", "O")
    s = s.replace("Ü", "U")
    s = s.replace("Ğ", "G")
    s = s.replace("Ş", "S")
    s = s.replace("Ç", "C")
    s = re.sub(r"[-_/]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def has_code(md, codes):
    """
    Model içində ayrıca kod axtarır.
    Məsələn: 21063, Niva 2121, 3110 101 və s.
    """
    tokens = re.findall(r"[A-Z]+|\d+", md)
    return any(code in tokens for code in codes)


def normalize_model(marka, model):
    mk = clean_text(marka)
    md = clean_text(model)

    if not md:
        return None

    # ---------------- VAZ / LADA ----------------
    if mk in {"VAZ", "LADA"}:
        if has_code(md, {"2101", "21011", "21013"}):
            return "VAZ-2101 qrup"

        if has_code(md, {"2106", "21061", "21063", "21065"}):
            return "VAZ-2106 qrup"

        if has_code(md, {"2103", "21033", "2105", "21051", "21053", "2107", "21072", "21074"}):
            return "VAZ-2103/2105/2107 qrup"

        if has_code(md, {"2102", "2104", "21043"}):
            return "VAZ-2102/2104 universal qrup"

        if has_code(md, {"2108", "21083", "2109", "21093", "21099"}):
            return "VAZ Samara qrup"

        if has_code(md, {"2121", "21213", "21214", "212140", "2131"}) or "NIVA" in md:
            return "VAZ Niva qrup"

        if has_code(md, {"2110", "21100", "21102", "21104", "2111", "2112", "2115", "21154", "2170", "21705", "21723"}) or "PRIORA" in md:
            return "VAZ-2110/2111/2112/2115 qrup"

    # ---------------- GAZ / VOLQA ----------------
    if mk in {"GAZ", "VOLGA", "VOLQA GAZ 24"}:
        if has_code(md, {"21", "24", "2401", "2402", "2404", "2410", "2411", "2412", "2417", "3102", "31029", "310290", "3110", "31105"}):
            return "GAZ Volqa qrup"

        if has_code(md, {"2705", "3221", "32213", "322132", "3302", "33021", "330210", "3303", "3307", "3308"}):
            return "GAZelle/Sobol qrup"

        if has_code(md, {"51", "51A", "52", "53", "53A", "53B", "66", "69"}):
            return "GAZ yük/UAZ tipli qrup"

    # ---------------- MOSKVICH ----------------
    if mk in {"MOSKVICH", "MOSKVIC", "MOSKVIC"}:
        if has_code(md, {"408", "412", "2140", "21403", "21406", "2141", "21412"}) or "ALEKO" in md:
            return "Moskvich qrup"

    # ---------------- UAZ ----------------
    if mk == "UAZ":
        if has_code(md, {"469", "469B", "452", "31512", "31514"}) or any(x in md for x in ["HUNTER", "PATRIOT", "BUXANKA", "BUKHANKA"]):
            return "UAZ qrup"

    # ---------------- MERCEDES ----------------
    if mk in {"MERCEDES", "MERCEDES BENZ", "DAIMLER", "DAIMLER BENZ"}:
        # yük / avtobus / mikroavtobus
        if any(x in md for x in [
            "ATEGO", "ACTROS", "AXOR", "SPRINTER", "VITO", "VIANO",
            "208D", "308", "318", "410", "TRAVEGO", "BUS", "AVTOBUS",
            "MIKROAVTOBUS", "YUK"
        ]):
            return "Mercedes yük/mikroavtobus qrup"

        # minik Mercedes
        if (
            "BENZ" in md
            or has_code(md, {"190", "200", "200D", "220", "220D", "230", "230E", "240", "250", "260", "300", "300D", "320"})
            or re.search(r"\b(C|E|S|ML|G|A)\s?\d{2,3}\b", md)
            or any(x in md for x in ["C SERIYA", "E SERIYA", "S SERIYA", "ML SERIYA", "G SERIYA"])
        ):
            return "Mercedes minik qrup"

    # ---------------- BMW ----------------
    if mk == "BMW":
        if any(x in md for x in ["3 SERIYA", "3-SERIYA"]) or has_code(md, {"318", "320", "325", "328"}):
            return "BMW 3-seriya"
        if any(x in md for x in ["5 SERIYA", "5-SERIYA"]) or has_code(md, {"520", "524", "525", "530"}):
            return "BMW 5-seriya"
        if any(x in md for x in ["7 SERIYA", "7-SERIYA"]):
            return "BMW 7-seriya"

    # ---------------- ümumi yararsız adlar ----------------
    if md in {"MINIK", "YUK", "YUK MASINI", "MIKROAVTOBUS", "AVTOBUS"}:
        return "Digər/naməlum model"

    # Qalan modellər öz adı ilə qalsın
    return md or None
