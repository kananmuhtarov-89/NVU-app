# nvu/export.py
from io import BytesIO
from datetime import datetime
import pandas as pd
import numpy as np

# =====================================================
# ---------------------- DOCX -------------------------
# =====================================================
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn

# Ümumi stil konstansları
H1_COLOR = RGBColor(31, 78, 121)    # tünd mavi
H2_COLOR = RGBColor(0, 112, 192)    # mavi
HDR_FILL = "D9E1F2"                 # açıq mavi (xlsx/dəmək üçün)
FONT_NAME = "Arial"

def _set_doc_defaults(doc: Document):
    # Default font = Arial
    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = Pt(10)

def _set_header_footer(doc: Document, source_filename: str = ""):
    sect = doc.sections[0]
    # Header
    header_p = sect.header.paragraphs[0] if sect.header.paragraphs else sect.header.add_paragraph()
    header_p.text = "NVU — Utilizasiya Proqramı üzrə Yekun Hesabat"
    header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in header_p.runs:
        r.font.bold = True
        r.font.name = FONT_NAME
        r.font.size = Pt(11)
        r.font.color.rgb = H1_COLOR

    # Footer (yalnız tarix)
    footer_p = sect.footer.paragraphs[0] if sect.footer.paragraphs else sect.footer.add_paragraph()
    footer_p.text = f"Təmiz Şəhər ASC — NV Utilizasiya şöbəsi · Tarix: {datetime.now():%Y-%m-%d}"
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in footer_p.runs:
        r.font.name = FONT_NAME
        r.font.size = Pt(9)

def _add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.bold = True
    if level == 1:
        run.font.size = Pt(16)
        run.font.color.rgb = H1_COLOR
        p.space_after = Pt(6)
    else:
        run.font.size = Pt(13)
        run.font.color.rgb = H2_COLOR
        p.space_after = Pt(4)

def _add_note_date(doc: Document):
    p = doc.add_paragraph()
    r1 = p.add_run("Hesabat tarixi: ")
    r1.font.name = FONT_NAME
    r1.bold = True
    r1.font.size = Pt(10)
    r2 = p.add_run(datetime.now().strftime("%Y-%m-%d"))
    r2.font.name = FONT_NAME
    r2.font.size = Pt(10)
    r2.font.color.rgb = RGBColor(192, 0, 0)  # qırmızı

def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    out = df.copy()
    # NaN/boş/“—” sətirləri tam sil
    if isinstance(out, pd.DataFrame):
        # string kimi “—” olanları NaN et
        out = out.replace({r"^\s*—\s*$": np.nan}, regex=True)
        out = out.dropna(how="all")
    return out

def _table_borderless(tbl):
    # Bütün sərhədləri sıfırla
    tblPr = tbl._element.get_or_add_tblPr()
    tblBorders = OxmlElement('w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        elem = OxmlElement(f'w:{edge}')
        elem.set(qn('w:val'), 'nil')
        tblBorders.append(elem)
    tblPr.append(tblBorders)

def _add_df_table(doc: Document, df: pd.DataFrame):
    df = _clean_df(df)
    if df.empty:
        return

    # Başlıqları “Təsnifat” kimi vahidləşdirmək istəyi: 1-ci sütunu varsa rename
    if df.columns.size >= 1:
        c0 = str(df.columns[0]).strip()
        # artıq "Təsnifat" deyilsə uyğunlaşdır
        if c0.lower() in ["kod", "kod/təsnifat", "kod / təsnifat", "tesnifat", "kod tesnifat"]:
            df = df.rename(columns={df.columns[0]: "Təsnifat"})

    # DOCX cədvəli
    rows, cols = len(df.index), len(df.columns)
    if rows <= 0 or cols <= 0:
        return

    table = doc.add_table(rows=rows+1, cols=cols)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.allow_autofit = True
    # Borderless
    _table_borderless(table)

    # Header – açıq mavi fon effekti üçün sadəcə bold + text rəngi
    for j, col in enumerate(df.columns):
        cell = table.cell(0, j)
        cell.text = str(col)
        for r in cell.paragraphs[0].runs:
            r.font.bold = True
            r.font.name = FONT_NAME
            r.font.size = Pt(10)

    # Rows
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        for j, col in enumerate(df.columns):
            val = row[col]
            cell = table.cell(i, j)
            cell.text = "" if pd.isna(val) else str(val)
            for r in cell.paragraphs[0].runs:
                r.font.name = FONT_NAME
                r.font.size = Pt(10)

    doc.add_paragraph()  # araya boşluq

def export_docx(report: dict, source_filename: str = "") -> bytes:
    """
    NVU DOCX report — sabit, təhlükəsiz versiya.
    - Header/Footer qurulur
    - “Hesabat tarixi” göstərilir
    - Boş cədvəllər atlanaq
    - Borderless table + Arial
    """
    doc = Document()
    _set_doc_defaults(doc)
    _set_header_footer(doc, source_filename=source_filename)

    # Başlıq + tarix
    _add_heading(doc, "Yekun Hesabat", level=1)
    _add_note_date(doc)

    # Bölmə: Utilizatorlar
    df = _clean_df(report.get("utilizator_counts"))
    if not df.empty:
        _add_heading(doc, "Utilizatorlar", level=2)
        # CƏM sətiri varsa saxla (DataFrame tərəfindən formalaşdırılıbsa)
        _add_df_table(doc, df)

    # Bölmə: Təsnifat
    df = report.get("tesnifat_table") or report.get("tesnifat_counts")
    df = _clean_df(df)
    if not df.empty:
        _add_heading(doc, "Təsnifatlar üzrə", level=2)
        _add_df_table(doc, df)

    # Bölmə: Statuslar
    for key, title in [
        ("tesdiq_status_totals", "Təsdiq statusu"),
        ("tehvil_status_totals","Təhvil statusu"),
    ]:
        df = _clean_df(report.get(key))
        if not df.empty:
            _add_heading(doc, title, level=2)
            _add_df_table(doc, df)

    # Bölmə: Top-N
    for key, title in [
        ("top_erizeci","Ərizəçi Top"),
        ("top_marka", "Marka Top"),
        ("top_model", "Model Top"),
        ("top_reng",  "Rəng Top"),
    ]:
        df = _clean_df(report.get(key))
        if not df.empty:
            _add_heading(doc, title, level=2)
            _add_df_table(doc, df)

    # Bölmə: İllər üzrə
    df = _clean_df(report.get("year_bins"))
    if not df.empty:
        _add_heading(doc, "NV yaşları 10 illik intervallarda — yekun", level=2)
        _add_df_table(doc, df)

    # Saxla
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()


# =====================================================
# ---------------------- XLSX -------------------------
# =====================================================

# ---- openpyxl stilləri (opsional; yoxdursa no-op) ----
try:
    from openpyxl.styles import Font as XLFont, PatternFill, Alignment as XLAlignment
except Exception:
    XLFont = PatternFill = XLAlignment = None

def _style_openpyxl_worksheet(ws, df: pd.DataFrame):
    """
    Power BI üçün oxunaqlılıq:
    - Header-lar bold + açıq mavi fon (#D9E1F2)
    - Sütun genişliklərini kontentə görə təxmini autosize
    """
    if ws is None or XLFont is None:
        return
    header_fill = PatternFill("solid", fgColor="D9E1F2")
    for cell in ws[1]:
        cell.font = XLFont(bold=True)
        cell.fill = header_fill
        cell.alignment = XLAlignment(vertical="center")
    for idx, col in enumerate(df.columns, start=1):
        max_len = len(str(col))
        for v in df[col].astype(str).values[:500]:
            max_len = max(max_len, len(v))
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = min(max(10, int(max_len * 1.2) + 2), 60)

def export_xlsx(report: dict) -> bytes:
    """
    report-dakı DataFrame-ləri ayrıca vərəqlərə yazır (openpyxl).
    'powerbi_feed' varsa, onu ayrıca 'PowerBI_Feed' vərəqində çıxarır.
    """
    from pandas import ExcelWriter  # gec import təhlükəsizlik üçün
    bio = BytesIO()
    with ExcelWriter(bio, engine="openpyxl") as writer:
        # 1) Utilizatorlar
        df = report.get("utilizator_counts")
        if isinstance(df, pd.DataFrame) and not df.empty:
            name = "Utilizatorlar"
            df.to_excel(writer, sheet_name=name, index=False)
            _style_openpyxl_worksheet(writer.sheets.get(name), df)

        # 2) Təsnifat
        df = report.get("tesnifat_table") or report.get("tesnifat_counts")
        if isinstance(df, pd.DataFrame) and not df.empty:
            name = "Təsnifat"
            df.to_excel(writer, sheet_name=name, index=False)
            _style_openpyxl_worksheet(writer.sheets.get(name), df)

        # 3) Status cədvəlləri və TOP-lar
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

        # 4) Parametrlər (Top-N metadata)
        meta = report.get("top_counts_meta")
        if isinstance(meta, dict) and meta:
            df_meta = pd.DataFrame([meta])
            name = "Parametrlər"
            df_meta.to_excel(writer, sheet_name=name, index=False)
            _style_openpyxl_worksheet(writer.sheets.get(name), df_meta)

        # 5) Power BI üçün tek-sheet feed
        feed = report.get("powerbi_feed")
        if isinstance(feed, pd.DataFrame) and not feed.empty:
            name = "PowerBI_Feed"
            feed.to_excel(writer, sheet_name=name, index=False)
            _style_openpyxl_worksheet(writer.sheets.get(name), feed)

    bio.seek(0)
    return bio.getvalue()
