# nvu/export.py
import re
from io import BytesIO
from typing import Dict, Any, Optional

import pandas as pd
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


# ------------------------------ Köməkçilər ------------------------------
def _fmt_int(x: Optional[int]) -> str:
    if x is None:
        return "—"
    return f"{int(x):,}".replace(",", " ")

def _add_table(doc: Document, df: pd.DataFrame) -> None:
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, col in enumerate(df.columns):
        p = hdr[i].paragraphs[0]
        r = p.add_run(str(col))
        r.bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for j, col in enumerate(df.columns):
            val = row[col]
            cells[j].text = "" if pd.isna(val) else str(val)

def _subset(df: pd.DataFrame, preferred_cols) -> pd.DataFrame:
    cols = [c for c in preferred_cols if c in df.columns]
    return df[cols].copy() if cols else df.copy()

# ------------------------ Təsnifat xəritəsi (fallback) -------------------
_CLASS_INFO_BASE = {
    "M1": ("Oturacaq yerləri (sürücüdən əlavə) ≤ 8 — sərnişin", 1500),
    "M2": ("> 8 yer, icazə verilən kütlə ≤ 5 t — sərnişin", 2000),
    "M3": ("> 5 t — sərnişin", 3000),
    "N1": ("İcazə verilən kütlə ≤ 3.5 t — yük", 1500),
    "N2": ("3.5–12 t — yük", 2000),
    "N3": ("> 12 t — yük", 3000),
    "T":  ("Traktorlar (təkərli)", 2000),
    "TK": ("Traktorlar (tırtıllı)", 2000),
    "TT": ("Traktorlar (digər)", 2000),
    "H":  ("Özügedən maşınlar (mexaniki ötürücülü)", 3000),
    "HT": ("Özügedən maşınlar (hidrostatik ötürücülü)", 3000),
    "HK": ("Meliorasiya/yol-tikinti maşınları, ekskavatorlar", 3000),
    "L":  ("Kvadrisikllər və təkərləri dörddən az olanlar", 200),
}
_GABLE = {"M1","M2","M3","N1","N2","N3"}

def _fallback_tesnifat(df_counts: pd.DataFrame, settings: Dict[str, Any]) -> pd.DataFrame:
    """Təsnifat (string) → Kod çıxar, G-ləri birləşdir (istəyə görə), Say (+ Cəmi)."""
    merge_g = bool(settings.get("merge_g", True))
    calc     = bool(settings.get("calc_amounts", False))

    VALID = set(_CLASS_INFO_BASE.keys()) | {k+"G" for k in _GABLE}

    def _extract_code(val: str) -> str:
        s = str(val).upper().strip()
        for bad in ("TƏSNİFATI","TƏSNIFATI","TESNIFATI","TƏSNİFATİ","TƏSNİFAT"):
            s = s.replace(bad, "")
        s = s.strip()
        token = re.split(r"[\s\-/_,]+", s)[0] if s else ""
        for k in sorted(VALID, key=len, reverse=True):
            if s.startswith(k) or token.startswith(k):
                return k
        return token

    if df_counts.empty:
        return pd.DataFrame(columns=["Təsnifat","Say"])

    df = df_counts.copy()
    if "Təsnifat" not in df.columns:
        df.columns = ["Təsnifat","Say"][:len(df.columns)]
    df["Təsnifat"] = df["Təsnifat"].apply(_extract_code)
    if merge_g:
        df["Təsnifat"] = df["Təsnifat"].str.replace(r"^([MN][123])G$", r"\\1", regex=True)

    out = df.groupby("Təsnifat", as_index=False)["Say"].sum().sort_values("Say", ascending=False)

    if calc:
        map_df = (pd.DataFrame.from_dict(_CLASS_INFO_BASE, orient="index", columns=["Açıqlama","Güzəşt (AZN)"])
                    .reset_index().rename(columns={"index":"Təsnifat"}))
        out = out.merge(map_df[["Təsnifat","Güzəşt (AZN)"]], on="Təsnifat", how="left")
        out["Güzəşt (AZN)"] = out["Güzəşt (AZN)"].fillna(0).astype(int)
        out["Cəmi (AZN)"] = out["Say"] * out["Güzəşt (AZN)"]
        out = out[["Təsnifat","Say","Cəmi (AZN)"]]
    else:
        out = out[["Təsnifat","Say"]]
    return out.reset_index(drop=True)

# ------------------------------- DOCX -----------------------------------
def export_docx(report: Dict[str, Any], source_filename: str = "") -> bytes:
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)

    doc.add_heading("NVU Arayış Paneli — Hesabat", level=1)
    if source_filename:
        doc.add_paragraph(f"Mənbə fayl: {source_filename}")

    # 1) Utilizatorlar
    doc.add_heading("1) Utilizatorlar üzrə qəbul edilən NV sayları", level=2)
    util = report.get("utilizator_counts", pd.DataFrame())
    if isinstance(util, pd.DataFrame) and not util.empty:
        # CƏM sətri
        if util.shape[1] >= 2:
            total = int(util.iloc[:,1].sum())
            util_out = util.copy()
            util_out.loc[len(util_out), util_out.columns[0]] = "CƏM"
            util_out.loc[len(util_out)-1, util_out.columns[1]] = total
        else:
            util_out = util.copy()
        _add_table(doc, util_out)
    else:
        doc.add_paragraph("Məlumat yoxdur.")

    # 2) Təsnifat
    doc.add_heading("2) Təsnifatlar üzrə", level=2)
    calc = bool(report.get("tesnifat_settings", {}).get("calc_amounts", False))
    ready = report.get("tesnifat_table")
    if isinstance(ready, pd.DataFrame) and not ready.empty:
        # yalnız lazımi sütunlar
        pref = ["Təsnifat","Kod","Say"] + (["Cəmi (AZN)"] if calc else [])
        t = _subset(ready, pref)
        if "Kod" in t.columns and "Təsnifat" not in t.columns:
            t = t.rename(columns={"Kod":"Təsnifat"})
        _add_table(doc, t)
        if "Say" in t.columns:
            p = doc.add_paragraph(); p.add_run(f"Cəm say: {_fmt_int(int(t['Say'].sum()))}").bold = True
        if calc and "Cəmi (AZN)" in t.columns:
            p = doc.add_paragraph(); p.add_run(f"Ümumi məbləğ (AZN): {_fmt_int(int(t['Cəmi (AZN)'].sum()))}").bold = True
    else:
        base = report.get("tesnifat_counts", pd.DataFrame())
        t = _fallback_tesnifat(base, report.get("tesnifat_settings", {}))
        _add_table(doc, t)
        if "Say" in t.columns:
            p = doc.add_paragraph(); p.add_run(f"Cəm say: {_fmt_int(int(t['Say'].sum()))}").bold = True
        if "Cəmi (AZN)" in t.columns:
            p = doc.add_paragraph(); p.add_run(f"Ümumi məbləğ (AZN): {_fmt_int(int(t['Cəmi (AZN)'].sum()))}").bold = True

    # 3+) Digər bölmələr – dinamik başlıqlar
    meta = report.get("top_counts_meta", {})
    sections = [
        ("3) Təsdiqedici Statusları", "tesdiq_status_totals", ["Təsdiq edici sənədin statusu","Say"]),
        ("4) TT aktların Statusları", "tehvil_status_totals", ["Təhvil-təslim sənədinin statusu","Say"]),
        (f"5) Top {meta.get('erizeci_N', 50)} Ərizəçi", "top_erizeci", ["Ərizəçinin tam adı","Say"]),
        (f"6) Marka Top {meta.get('marka_N', 20)}", "top_marka", ["Marka","Say"]),
        (f"7) Modellər üzrə Top {meta.get('model_N', 10)}", "top_model", ["Marka","Model","Say"]),
        (f"8) Rəng Top {meta.get('reng_N', 10)}", "top_reng", ["Rəng","Say"]),
        ("9) NV yaşları 10illik intervallarda", "year_bins", ["Buraxılış ili","Say"]),
    ]
    for title, key, pref in sections:
        doc.add_heading(title, level=2)
        d = report.get(key, pd.DataFrame())
        if isinstance(d, pd.DataFrame) and not d.empty:
            _add_table(doc, _subset(d, pref))
        else:
            doc.add_paragraph("Məlumat yoxdur.")

    bio = BytesIO(); doc.save(bio)
    return bio.getvalue()

# ------------------------------- XLSX -----------------------------------
def export_xlsx(report: Dict[str, Any]) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as xw:
        for key, val in report.items():
            if isinstance(val, pd.DataFrame) and not val.empty:
                val.to_excel(xw, sheet_name=key[:31], index=False)

        # Utilizator cədvəlində CƏM sətri ilə ayrıca vərəq (oxunaqlıdır)
        util = report.get("utilizator_counts")
        if isinstance(util, pd.DataFrame) and not util.empty and util.shape[1] >= 2:
            util2 = util.copy()
            util2.loc[len(util2), util2.columns[0]] = "CƏM"
            util2.loc[len(util2)-1, util2.columns[1]] = int(util.iloc[:,1].sum())
            util2.to_excel(xw, sheet_name="utilizator_counts", index=False)

        # Təsnifat: hazır yoxdursa fallback yaz
        tbl = report.get("tesnifat_table")
        if not (isinstance(tbl, pd.DataFrame) and not tbl.empty):
            base = report.get("tesnifat_counts", pd.DataFrame())
            fall = _fallback_tesnifat(base, report.get("tesnifat_settings", {}))
            if not fall.empty:
                fall.to_excel(xw, sheet_name="tesnifatlar", index=False)

    return bio.getvalue()
