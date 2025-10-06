import re
from io import BytesIO
from typing import Dict, Any, Optional

import pandas as pd
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ------------------------------------------------------------
# Köməkçilər
# ------------------------------------------------------------
def _add_table(doc: Document, df: pd.DataFrame, header_bold: bool = True) -> None:
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, col in enumerate(df.columns):
        p = hdr[i].paragraphs[0]
        run = p.add_run(str(col))
        if header_bold:
            run.bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for j, col in enumerate(df.columns):
            cells[j].text = str(row[col] if pd.notna(row[col]) else "")

def _fmt_int(x: Optional[int]) -> str:
    if x is None:
        return "—"
    return f"{int(x):,}".replace(",", " ")

# ------------------------------------------------------------
# Təsnifat xəritəsi (fallback üçün)
# ------------------------------------------------------------
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
    """
    tesnifat_counts (Təsnifat, Say) əsasında Word/XLSX üçün minimal cədvəl.
    Çıxış yalnız: Təsnifat (kod), Say [+ Cəmi (AZN) əgər calc=True].
    """
    merge_g = bool(settings.get("merge_g", True))
    calc = bool(settings.get("calc_amounts", False))

    VALID = set(_CLASS_INFO_BASE.keys()) | {k + "G" for k in _GABLE}

    def _extract_code(val: str) -> str:
        s = str(val).upper().strip()
        for bad in ("TƏSNİFATI", "TƏSNIFATI", "TESNIFATI", "TƏSNİFATİ", "TƏSNİFAT"):
            s = s.replace(bad, "")
        s = s.strip()
        token = re.split(r"[\s\-/_,]+", s)[0] if s else ""
        for k in sorted(VALID, key=len, reverse=True):
            if s.startswith(k) or token.startswith(k):
                return k
        return token

    df = df_counts.copy()
    df["Təsnifat"] = df["Təsnifat"].apply(_extract_code)

    if merge_g:
        df["Təsnifat"] = df["Təsnifat"].str.replace(r"^([MN][123])G$", r"\1", regex=True)

    out = df.groupby("Təsnifat", as_index=False)["Say"].sum()

    if calc:
        map_df = pd.DataFrame.from_dict(_CLASS_INFO_BASE, orient="index",
                                        columns=["Açıqlama", "Güzəşt (AZN)"]).reset_index().rename(columns={"index":"Təsnifat"})
        out = out.merge(map_df[["Təsnifat", "Güzəşt (AZN)"]], on="Təsnifat", how="left")
        out["Güzəşt (AZN)"] = out["Güzəşt (AZN)"].fillna(0).astype(int)
        out["Cəmi (AZN)"] = out["Say"] * out["Güzəşt (AZN)"]
        out = out[["Təsnifat", "Say", "Cəmi (AZN)"]]
    else:
        out = out[["Təsnifat", "Say"]]

    return out.sort_values("Say", ascending=False).reset_index(drop=True)

# ------------------------------------------------------------
# DOCX
# ------------------------------------------------------------
def export_docx(report: Dict[str, Any], source_filename: str = "") -> bytes:
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)

    title = doc.add_heading("NVU Arayış Paneli — Hesabat", level=1)
    if source_filename:
        doc.add_paragraph(f"Mənbə fayl: {source_filename}")

    # 1) Utilizatorlar üzrə
    doc.add_heading("1) Utilizatorlar üzrə qəbul edilən NV sayları", level=2)
    util = report.get("utilizator_counts", pd.DataFrame())
    if isinstance(util, pd.DataFrame) and not util.empty:
        total_nv = int(util.iloc[:,1].sum()) if util.shape[1] >= 2 else int(util.sum(numeric_only=True))
        util_out = util.copy()
        util_out.loc[len(util_out), util_out.columns[0]] = "CƏM"
        util_out.loc[len(util_out)-1, util_out.columns[1]] = total_nv
        _add_table(doc, util_out)
    else:
        doc.add_paragraph("Məlumat yoxdur.")

    # 2) Təsnifatlar üzrə
    doc.add_heading("2) Təsnifatlar üzrə", level=2)
    calc = bool(report.get("tesnifat_settings", {}).get("calc_amounts", False))
    tbl_ready = report.get("tesnifat_table")
    if isinstance(tbl_ready, pd.DataFrame) and not tbl_ready.empty:
        # yalnız lazımi sütunlar
        cols = ["Təsnifat", "Say"] + (["Cəmi (AZN)"] if calc and "Cəmi (AZN)" in tbl_ready.columns else [])
        tesn_out = tbl_ready[cols].copy()
        _add_table(doc, tesn_out)
        # cəmlər
        total_cnt = int(tesn_out["Say"].sum())
        p = doc.add_paragraph(); p.add_run(f"Cəm say: {_fmt_int(total_cnt)}").bold = True
        if calc and "Cəmi (AZN)" in tesn_out.columns:
            total_amt = int(tesn_out["Cəmi (AZN)"].sum())
            p = doc.add_paragraph(); p.add_run(f"Ümumi məbləğ (AZN): {_fmt_int(total_amt)}").bold = True
    else:
        # fallback
        tesn_counts = report.get("tesnifat_counts", pd.DataFrame())
        if isinstance(tesn_counts, pd.DataFrame) and not tesn_counts.empty:
            tesn_out = _fallback_tesnifat(tesn_counts, report.get("tesnifat_settings", {}))
            _add_table(doc, tesn_out)
            total_cnt = int(tesn_out["Say"].sum())
            p = doc.add_paragraph(); p.add_run(f"Cəm say: {_fmt_int(total_cnt)}").bold = True
            if "Cəmi (AZN)" in tesn_out.columns:
                total_amt = int(tesn_out["Cəmi (AZN)"].sum())
                p = doc.add_paragraph(); p.add_run(f"Ümumi məbləğ (AZN): {_fmt_int(total_amt)}").bold = True
        else:
            doc.add_paragraph("Məlumat yoxdur.")

    # 3+) Digər bölmələr
    order = [
        ("3) Təsdiqedici Statusları", "tesdiq_status_totals"),
        ("4) TT aktların Statusları", "tehvil_status_totals"),
        ("5) Top 50 Ərizəçi", "top50_erizeci"),
        ("6) Marka Top 20", "top20_marka"),
        ("7) Modellar üzrə Top 20", "top20_model"),
        ("8) Rəng Top 20", "top20_reng"),
        ("9) Region", "region_counts"),
        ("10) NV yaşları 10illik intervallarda", "year_bins"),
    ]
    for heading, key in order:
        doc.add_heading(heading, level=2)
        df = report.get(key, pd.DataFrame())
        if isinstance(df, pd.DataFrame) and not df.empty:
            _add_table(doc, df)
        else:
            doc.add_paragraph("Məlumat yoxdur.")

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ------------------------------------------------------------
# XLSX
# ------------------------------------------------------------
def export_xlsx(report: Dict[str, Any]) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as xw:
        # Bütün DataFrame-ləri vərəqlərə yaz
        for key, value in report.items():
            if isinstance(value, pd.DataFrame) and not value.empty:
                sheet = key[:31]
                value.to_excel(xw, sheet_name=sheet, index=False)

        # Utilizatorlar üçün CƏM sətiri
        util = report.get("utilizator_counts")
        if isinstance(util, pd.DataFrame) and not util.empty:
            sh = "utilizator_counts"
            util_out = util.copy()
            util_out.loc[len(util_out), util_out.columns[0]] = "CƏM"
            util_out.loc[len(util_out)-1, util_out.columns[1]] = int(util.iloc[:,1].sum())
            util_out.to_excel(xw, sheet_name=sh, index=False)

        # Təsnifatlar: hazır cədvəl yoxdursa fallback
        tbl_ready = report.get("tesnifat_table")
        if isinstance(tbl_ready, pd.DataFrame) and not tbl_ready.empty:
            tbl_ready.to_excel(xw, sheet_name="tesnifatlar", index=False)
        else:
            tesn_counts = report.get("tesnifat_counts")
            if isinstance(tesn_counts, pd.DataFrame) and not tesn_counts.empty:
                fallback = _fallback_tesnifat(tesn_counts, report.get("tesnifat_settings", {}))
                fallback.to_excel(xw, sheet_name="tesnifatlar", index=False)

    return bio.getvalue()
