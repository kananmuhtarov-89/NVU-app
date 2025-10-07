from io import BytesIO
from datetime import datetime
import pandas as pd
import numpy as np

# ============== DOCX ==============
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

H1_COLOR = RGBColor(31, 78, 121)     # tünd mavi
H2_COLOR = RGBColor(0, 112, 192)     # mavi
FONT_NAME = "Arial"

def _set_doc_defaults(doc: Document):
    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = Pt(10)

def _set_header_footer(doc: Document):
    sect = doc.sections[0]
    # Header
    hp = sect.header.paragraphs[0] if sect.header.paragraphs else sect.header.add_paragraph()
    hp.text = "NVU — Utilizasiya Proqramı üzrə Yekun Hesabat"
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in hp.runs:
        r.font.bold = True
        r.font.name = FONT_NAME
        r.font.size = Pt(11)
        r.font.color.rgb = H1_COLOR
    # Footer (yalnız tarix)
    fp = sect.footer.paragraphs[0] if sect.footer.paragraphs else sect.footer.add_paragraph()
    fp.text = f"Təmiz Şəhər ASC — NV Utilizasiya şöbəsi · Tarix: {datetime.now():%Y-%m-%d}"
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in fp.runs:
        r.font.name = FONT_NAME
        r.font.size = Pt(9)

def _add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_paragraph()
    rn = p.add_run(text)
    rn.font.name = FONT_NAME
    rn.bold = True
    if level == 1:
        rn.font.size = Pt(16); rn.font.color.rgb = H1_COLOR; p.space_after = Pt(6)
    else:
        rn.font.size = Pt(13); rn.font.color.rgb = H2_COLOR; p.space_after = Pt(4)

def _add_note_date(doc: Document):
    p = doc.add_paragraph()
    r1 = p.add_run("Hesabat tarixi: ")
    r1.font.name = FONT_NAME; r1.font.size = Pt(10); r1.bold = True
    r2 = p.add_run(datetime.now().strftime("%Y-%m-%d"))
    r2.font.name = FONT_NAME; r2.font.size = Pt(10); r2.font.color.rgb = RGBColor(192, 0, 0)

def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    out = df.copy()
    out = out.replace({r"^\s*—\s*$": np.nan}, regex=True)
    out = out.dropna(how="all")
    return out

def _table_borderless(table):
    """Sərhədləri 'nil' edən təhlükəsiz, minimal versiya."""
    tbl = table._element  # CT_Tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        if len(tbl) > 0:
            tbl.insert(0, tblPr)
        else:
            tbl.append(tblPr)
    tblBorders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        e = OxmlElement(f'w:{edge}')
        e.set(qn('w:val'), 'nil')
        tblBorders.append(e)
    tblPr.append(tblBorders)

def _add_df_table(doc: Document, df: pd.DataFrame):
    df = _clean_df(df)
    if df.empty:
        return
    # 1-ci sütunun adı
    if df.columns.size >= 1:
        c0 = str(df.columns[0]).strip().lower()
        if c0 in ["kod", "kod/təsnifat", "kod / təsnifat", "tesnifat", "kod tesnifat"]:
            df = df.rename(columns={df.columns[0]: "Təsnifat"})
    rows, cols = len(df.index), len(df.columns)
    if rows == 0 or cols == 0:
        return

    table = doc.add_table(rows=rows+1, cols=cols)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.allow_autofit = True
    _table_borderless(table)

    # Header
    for j, col in enumerate(df.columns):
        cell = table.cell(0, j)
        cell.text = str(col)
        for r in cell.paragraphs[0].runs:
            r.font.bold = True; r.font.name = FONT_NAME; r.font.size = Pt(10)

    # Rows
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        for j, col in enumerate(df.columns):
            v = row[col]
            cell = table.cell(i, j)
            cell.text = "" if pd.isna(v) else str(v)
            for r in cell.paragraphs[0].runs:
                r.font.name = FONT_NAME; r.font.size = Pt(10)

    doc.add_paragraph()  # boş sətir

def export_docx(report: dict, source_filename: str = "") -> bytes:
    """NVU DOCX: sabit və təhlükəsiz. Arial, rəngli heading, borderless cədvəl."""
    doc = Document()
    _set_doc_defaults(doc)
    _set_header_footer(doc)

    _add_heading(doc, "Yekun Hesabat", level=1)
    _add_note_date(doc)

    wrote_any = False

    # Utilizatorlar
    sec = _clean_df(report.get("utilizator_counts"))
    if not sec.empty:
        wrote_any = True; _add_heading(doc, "Utilizatorlar", level=2); _add_df_table(doc, sec)

    # Təsnifat (DataFrame-lərdə 'or' YOXDUR)
    t1 = report.get("tesnifat_table"); t2 = report.get("tesnifat_counts")
    sec = _clean_df(t1 if t1 is not None else t2)
    if not sec.empty:
        wrote_any = True; _add_heading(doc, "Təsnifatlar üzrə", level=2); _add_df_table(doc, sec)

    # Statuslar
    for key, title in [("tesdiq_status_totals","Təsdiq statusu"),
                       ("tehvil_status_totals","Təhvil statusu")]:
        sec = _clean_df(report.get(key))
        if not sec.empty:
            wrote_any = True; _add_heading(doc, title, level=2); _add_df_table(doc, sec)

    # TOP-lar
    for key, title in [("top_erizeci","Ərizəçi Top"),
                       ("top_marka","Marka Top"),
                       ("top_model","Model Top"),
                       ("top_reng","Rəng Top")]:
        sec = _clean_df(report.get(key))
        if not sec.empty:
            wrote_any = True; _add_heading(doc, title, level=2); _add_df_table(doc, sec)

    # İllər üzrə
    sec = _clean_df(report.get("year_bins"))
    if not sec.empty:
        wrote_any = True; _add_heading(doc, "NV yaşları 10 illik intervallarda — yekun", level=2); _add_df_table(doc, sec)

    if not wrote_any:
        _add_heading(doc, "Məlumat yoxdur", level=2)
        msg = report.get("summary") or "Seçilmiş filtr üçün uyğun sətir tapılmadı."
        p = doc.add_paragraph(str(msg))
        for r in p.runs:
            r.font.name = FONT_NAME; r.font.size = Pt(10)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()


# ============== XLSX ==============
try:
    from openpyxl.styles import Font as XLFont, PatternFill, Alignment as XLAlignment
except Exception:
    XLFont = PatternFill = XLAlignment = None

def _style_openpyxl_worksheet(ws, df: pd.DataFrame):
    if ws is None or XLFont is None:
        return
    header_fill = PatternFill("solid", fgColor="D9E1F2")
    for cell in ws[1]:
        cell.font = XLFont(bold=True); cell.fill = header_fill; cell.alignment = XLAlignment(vertical="center")
    for idx, col in enumerate(df.columns, start=1):
        max_len = len(str(col))
        for v in df[col].astype(str).values[:500]:
            max_len = max(max_len, len(v))
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = min(max(10, int(max_len * 1.2) + 2), 60)

def export_xlsx(report: dict) -> bytes:
    """openpyxl ilə XLSX; PowerBI_Feed və README ehtiyatı."""
    from pandas import ExcelWriter
    bio = BytesIO()
    wrote_any = False

    with ExcelWriter(bio, engine="openpyxl") as writer:
        # Utilizatorlar
        df = report.get("utilizator_counts")
        if isinstance(df, pd.DataFrame) and not df.empty:
            name = "Utilizatorlar"; df.to_excel(writer, sheet_name=name, index=False); _style_openpyxl_worksheet(writer.sheets.get(name), df); wrote_any = True

        # Təsnifat
        t1 = report.get("tesnifat_table"); t2 = report.get("tesnifat_counts")
        df = t1 if (isinstance(t1, pd.DataFrame) and not t1.empty) else (t2 if isinstance(t2, pd.DataFrame) else None)
        if isinstance(df, pd.DataFrame) and not df.empty:
            name = "Təsnifat"; df.to_excel(writer, sheet_name=name, index=False); _style_openpyxl_worksheet(writer.sheets.get(name), df); wrote_any = True

        # Status + TOP + İllər
        for key, name in [
            ("tesdiq_status_totals", "Təsdiq statusu"),
            ("tehvil_status_totals","Təhvil statusu"),
            ("top_erizeci",         "Top ərizəçi"),
            ("top_marka",           "Top marka"),
            ("top_model",           "Top model"),
            ("top_reng",            "Top rəng"),
            ("year_bins",           "İllər üzrə"),
        ]:
            df = report.get(key)
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.to_excel(writer, sheet_name=name, index=False)
                _style_openpyxl_worksheet(writer.sheets.get(name), df)
                wrote_any = True

        # Parametrlər
        meta = report.get("top_counts_meta")
        if isinstance(meta, dict) and meta:
            df_meta = pd.DataFrame([meta])
            name = "Parametrlər"; df_meta.to_excel(writer, sheet_name=name, index=False); _style_openpyxl_worksheet(writer.sheets.get(name), df_meta); wrote_any = True

        # Power BI feed
        feed = report.get("powerbi_feed")
        if isinstance(feed, pd.DataFrame) and not feed.empty:
            name = "PowerBI_Feed"; feed.to_excel(writer, sheet_name=name, index=False); _style_openpyxl_worksheet(writer.sheets.get(name), feed); wrote_any = True

        if not wrote_any:
            readme = pd.DataFrame({
                "Info": ["No data tables were available to export."],
                "GeneratedAt": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "Hint": ["Check filters and input file, then retry."],
            })
            name = "README"
            readme.to_excel(writer, sheet_name=name, index=False)
            _style_openpyxl_worksheet(writer.sheets.get(name), readme)

    bio.seek(0)
    return bio.getvalue()
