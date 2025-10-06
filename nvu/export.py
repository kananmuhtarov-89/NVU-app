# nvu/export.py
from io import BytesIO
from typing import Dict, Any, Optional
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# -------------------- Köməkçilər --------------------
def _fmt_int(x: Optional[int]) -> str:
    if x is None:
        return "—"
    try:
        return f"{int(x):,}".replace(",", " ")
    except Exception:
        return str(x)

def _make_table_borderless(table):
    """
    Word cədvəlində sərhədləri (grid) söndürmək üçün stabil metod.
    Bəzi mühitlərdə python-docx tblPr və ya nsmap qaytarmadığından,
    həm None hallarını, həm də namespace-i manuel idarə edirik.
    Uğursuz olarsa, export dayanmasın deyə səssiz ötürürük.
    """
    try:
        tbl = table._tbl
        # tblPr None ola bilər — bu halda yaradıb geri qaytarır
        tblPr = getattr(tbl, "tblPr", None)
        if tblPr is None and hasattr(tbl, "get_or_add_tblPr"):
            tblPr = tbl.get_or_add_tblPr()

        if tblPr is None:
            return

        # Namespace-i əl ilə veririk (w:)
        NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

        # Mövcud sərhəd elementlərini sil
        for el in tblPr.xpath("./w:tblBorders", namespaces=NS):
            tblPr.remove(el)
    except Exception:
        pass

def _to_text(val) -> str:
    """NaN/boş/“nan” dəyərləri '—' kimi yaz, ədəd varsa '.0' at."""
    if pd.isna(val):
        return "—"
    s = str(val).strip()
    if s.lower() in ("nan", "none", ""):
        return "—"
    # ədədlərdə .0 at
    try:
        if isinstance(val, float) and float(val).is_integer():
            return _fmt_int(int(val))
        if isinstance(val, (int,)):
            return _fmt_int(val)
    except Exception:
        pass
    return s

def _sanitize_df_for_docx(df: pd.DataFrame) -> pd.DataFrame:
    dfx = df.copy()
    for c in dfx.columns:
        dfx[c] = dfx[c].map(_to_text)
    return dfx

def _add_table(doc: Document, df: pd.DataFrame, add_rownum: bool = False) -> None:
    dfx = df.copy()
    if add_rownum and len(dfx) > 0:
        dfx.insert(0, "Sıra №", range(1, len(dfx) + 1))
    dfx = _sanitize_df_for_docx(dfx)

    table = doc.add_table(rows=1, cols=len(dfx.columns))
    _make_table_borderless(table)

    # Header sətri
    hdr = table.rows[0].cells
    for i, col in enumerate(dfx.columns):
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(str(col))
        run.bold = True
        run.font.name = "Arial"
        run.font.size = Pt(11)
        # Açıq tünd boz (opsional): run.font.color.rgb = RGBColor(55, 55, 55)

    # Sətirlər
    for _, row in dfx.iterrows():
        cells = table.add_row().cells
        for j, col in enumerate(dfx.columns):
            p = cells[j].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(row[col])
            run.font.name = "Arial"
            run.font.size = Pt(11)

def _subset(df: pd.DataFrame, preferred_cols) -> pd.DataFrame:
    cols = [c for c in preferred_cols if c in df.columns]
    return df[cols].copy() if cols else df.copy()

# -------------------- DOCX --------------------
def export_docx(report: Dict[str, Any], source_filename: str = "") -> bytes:
    doc = Document()

    # Ümumi stil – Arial 12
    base = doc.styles["Normal"]
    base.font.name = "Arial"
    base.font.size = Pt(12)

    # Heading 1 – Arial 18, tünd mavi
    h1 = doc.styles["Heading 1"]
    h1.font.name = "Arial"
    h1.font.size = Pt(18)
    h1.font.color.rgb = RGBColor(0x12, 0x3A, 0x7A)  # #123A7A

    # Heading 2 – Arial 14, mavi
    h2 = doc.styles["Heading 2"]
    h2.font.name = "Arial"
    h2.font.size = Pt(14)
    h2.font.color.rgb = RGBColor(0x1F, 0x5A, 0xB6)  # #1F5AB6

    doc.add_heading("NVU Arayış Paneli — Hesabat", level=1)
    if source_filename:
        p = doc.add_paragraph("Mənbə fayl: ")
        run = p.add_run(source_filename)
        run.bold = True

    # 1) Utilizatorlar
    doc.add_heading("1) Utilizatorlar üzrə qəbul edilən NV sayları", level=2)
    util = report.get("utilizator_counts", pd.DataFrame())
    if isinstance(util, pd.DataFrame) and not util.empty:
        util_out = util.copy()
        if util_out.shape[1] >= 2:
            total = pd.to_numeric(util_out.iloc[:, 1], errors="coerce").fillna(0).astype(int).sum()
            util_out = util_out.copy()
            util_out.iloc[:, 1] = pd.to_numeric(util_out.iloc[:, 1], errors="coerce").fillna(0).astype(int)
            util_out.loc[len(util_out), util_out.columns[0]] = "CƏM"
            util_out.loc[len(util_out) - 1, util_out.columns[1]] = total
        _add_table(doc, util_out, add_rownum=False)
    else:
        doc.add_paragraph("Məlumat yoxdur.")

    # 2) Təsnifat
    doc.add_heading("2) Təsnifatlar üzrə", level=2)
    calc = bool(report.get("tesnifat_settings", {}).get("calc_amounts", False))
    ready = report.get("tesnifat_table")
    if isinstance(ready, pd.DataFrame) and not ready.empty:
        pref = ["Kod", "Təsnifat", "Say"] + (["Cəmi (AZN)"] if calc else [])
        t = _subset(ready, pref)
        if "Kod" not in t.columns and "Təsnifat" in t.columns:
            t = t.rename(columns={"Təsnifat": "Kod"})
        cols = ["Kod", "Say"]
        if calc and "Cəmi (AZN)" in t.columns:
            # rəqəmləri int kimi göstər
            t["Cəmi (AZN)"] = pd.to_numeric(t["Cəmi (AZN)"], errors="coerce").fillna(0).astype(int)
            cols += ["Cəmi (AZN)"]
        _add_table(doc, t[cols], add_rownum=False)

        # CƏM göstəriciləri
        if "Say" in t.columns:
            p = doc.add_paragraph()
            p.add_run(f"Cəm say: {_fmt_int(int(pd.to_numeric(t['Say'], errors='coerce').fillna(0).sum()))}").bold = True
        if calc and "Cəmi (AZN)" in t.columns:
            p = doc.add_paragraph()
            p.add_run(
                f"Ümumi məbləğ (AZN): {_fmt_int(int(pd.to_numeric(t['Cəmi (AZN)'], errors='coerce').fillna(0).sum()))}"
            ).bold = True
    else:
        base = report.get("tesnifat_counts", pd.DataFrame())
        t = _subset(base, ["Təsnifat", "Say"])
        _add_table(doc, t, add_rownum=False)

    # 3+) Digər bölmələr – dinamik başlıqlar + Sıra №
    meta = report.get("top_counts_meta", {})
    sections = [
        ("3) Təsdiqedici Statusları", "tesdiq_status_totals",
         ["Təsdiq edici sənədin statusu", "Say"], False),
        ("4) TT aktların Statusları", "tehvil_status_totals",
         ["Təhvil-təslim sənədinin statusu", "Say"], False),
        (f"5) Top {meta.get('erizeci_N', 50)} Ərizəçi", "top_erizeci",
         ["Ərizəçinin tam adı", "Say"], True),
        (f"6) Marka Top {meta.get('marka_N', 20)}", "top_marka",
         ["Marka", "Say"], True),
        (f"7) Modellər üzrə Top {meta.get('model_N', 10)}", "top_model",
         ["Marka", "Model", "Say"], True),
        (f"8) Rəng Top {meta.get('reng_N', 10)}", "top_reng",
         ["Rəng", "Say"], True),
        ("9) NV yaşları 10illik intervallarda", "year_bins",
         ["Buraxılış ili", "Say"], False),
    ]
    for title, key, pref, add_no in sections:
        doc.add_heading(title, level=2)
        d = report.get(key, pd.DataFrame())
        if isinstance(d, pd.DataFrame) and not d.empty:
            # rəqəm sütunlarını int kimi göstərək
            dx = d.copy()
            for col in dx.columns:
                if pd.api.types.is_numeric_dtype(dx[col]):
                    dx[col] = pd.to_numeric(dx[col], errors="coerce").fillna(0).astype(int)
            _add_table(doc, _subset(dx, pref), add_rownum=add_no)
        else:
            doc.add_paragraph("Məlumat yoxdur.")

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# -------------------- XLSX --------------------
def export_xlsx(report: Dict[str, Any]) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as xw:
        for key, val in report.items():
            if isinstance(val, pd.DataFrame) and not val.empty:
                val.to_excel(xw, sheet_name=key[:31], index=False)

        # Utilizator cədvəlini CƏM sətiri ilə də ayrıca yaz (oxunaqlı olur)
        util = report.get("utilizator_counts")
        if isinstance(util, pd.DataFrame) and not util.empty and util.shape[1] >= 2:
            util2 = util.copy()
            util2.iloc[:, 1] = pd.to_numeric(util2.iloc[:, 1], errors="coerce").fillna(0).astype(int)
            util2.loc[len(util2), util2.columns[0]] = "CƏM"
            util2.loc[len(util2) - 1, util2.columns[1]] = int(util2.iloc[:-1, 1].sum())
            util2.to_excel(xw, sheet_name="utilizator_counts", index=False)

        # Təsnifat: hazır cədvəl yoxdursa baza yaz
        tbl = report.get("tesnifat_table")
        if not (isinstance(tbl, pd.DataFrame) and not tbl.empty):
            base = report.get("tesnifat_counts", pd.DataFrame())
            if isinstance(base, pd.DataFrame) and not base.empty:
                _subset(base, ["Təsnifat", "Say"]).to_excel(
                    xw, sheet_name="tesnifatlar", index=False
                )

    return bio.getvalue()
