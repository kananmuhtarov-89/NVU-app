# nvu/export.py
from datetime import datetime
from io import BytesIO
import pandas as pd

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# =========================
# VİZUAL PARAMETRLƏR (BURADA DƏYİŞ)
# =========================
# Rəng palitrası
COLOR_H1 = RGBColor(0x1F, 0x4E, 0x79)       # #1F4E79 (tünd mavi)
COLOR_H2 = RGBColor(0x2E, 0x75, 0xB6)       # #2E75B6 (mavi)
COLOR_HEADER_BG = "D9E1F2"                  # cədvəl başlığı fonu
COLOR_TOTAL_BG  = "FCE4D6"                  # yekun sətir fonu
COLOR_ZEBRA_BG  = "F7F9FC"                  # zolaqlama
COLOR_DIVIDER   = RGBColor(0xD0, 0xD0, 0xD0)

# Top bölmələr üçün başlıq rəngləri (bonus)
COLOR_TOP_ERIZECI = RGBColor(0x23, 0x8E, 0x6E)  # yaşıl ton
COLOR_TOP_MARKA   = RGBColor(0x2E, 0x75, 0xB6)  # mavi ton
COLOR_TOP_MODEL   = RGBColor(0x7F, 0x60, 0xA8)  # bənövşəyi ton
COLOR_TOP_RENG    = RGBColor(0xC0, 0x58, 0x50)  # narıncı-qırmızı ton

# Şrift ölçüləri
FONT_NAME       = "Arial"
FONT_SIZE_BODY  = Pt(10.5)
FONT_SIZE_H1    = Pt(14)
FONT_SIZE_H2    = Pt(12)

# Sətirarası məsafə və boşluqlar
PARAGRAPH_SPACING_BEFORE = Pt(12)
PARAGRAPH_SPACING_AFTER  = Pt(6)
LINE_SPACING             = 1.15

# Üst/altbilgi
HEADER_TITLE     = "NVU — Utilizasiya Proqramı üzrə Yekun Hesabat"
FOOTER_LEFT_TEXT = "Təmiz Şəhər ASC — NV Utilizasiya şöbəsi"
# Altbilgidə sağda avtomatik: Tarix: YYYY-MM-DD (sənəd № YOX)

# =========================
# KÖMƏKÇİ FUNKSİYALAR
# =========================
def _set_document_defaults(doc: Document):
    style = doc.styles['Normal']
    style.font.name = FONT_NAME
    style.font.size = FONT_SIZE_BODY

def _set_paragraph_format(p):
    p.paragraph_format.space_before = PARAGRAPH_SPACING_BEFORE
    p.paragraph_format.space_after  = PARAGRAPH_SPACING_AFTER
    p.paragraph_format.line_spacing = LINE_SPACING

def _add_header_footer(doc: Document, report_date: str):
    section = doc.sections[0]

    # Header
    header = section.header
    header_p = header.paragraphs[0]
    header_p.text = HEADER_TITLE
    header_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in header_p.runs:
        run.font.name = FONT_NAME
        run.font.size = Pt(9.5)
        run.bold = True

    # Footer (sol)
    footer = section.footer
    left_p = footer.add_paragraph()
    left_p.text = FOOTER_LEFT_TEXT
    left_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in left_p.runs:
        run.font.name = FONT_NAME
        run.font.size = Pt(9)

    # Footer (sağ — yalnız tarix)
    right_p = footer.add_paragraph()
    right_p.text = f"Tarix: {report_date}"
    right_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for run in right_p.runs:
        run.font.name = FONT_NAME
        run.font.size = Pt(9)

def _add_divider_line(doc: Document):
    p = doc.add_paragraph()
    _set_paragraph_format(p)
    run = p.add_run("────────────────────────────────────────────────────────")
    run.font.color.rgb = COLOR_DIVIDER
    run.font.size = Pt(8)
    return p

def _add_heading(doc: Document, text: str, level: int = 1, color: RGBColor | None = None):
    """Rəngli heading (H1/H2). `color` verilərsə, onu istifadə edir."""
    p = doc.add_paragraph()
    _set_paragraph_format(p)
    run = p.add_run(text)
    run.bold = True
    run.font.name = FONT_NAME
    if level == 1:
        run.font.size = FONT_SIZE_H1
        run.font.color.rgb = color if color else COLOR_H1
    else:
        run.font.size = FONT_SIZE_H2
        run.font.color.rgb = color if color else COLOR_H2
    return p

def _add_report_date_line(doc: Document, report_date: str):
    p = doc.add_paragraph()
    _set_paragraph_format(p)
    p.paragraph_format.space_before = Pt(0)
    run_label = p.add_run("Hesabat tarixi: ")
    run_label.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    run_label.font.bold = True
    run_label.font.name = FONT_NAME
    run_value = p.add_run(report_date)
    run_value.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    run_value.font.bold = True
    run_value.font.name = FONT_NAME

def _format_cell_text(cell, bold=False, italic=False, align_right=False):
    if not cell.paragraphs:
        return
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if align_right else WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.name = FONT_NAME
        run.font.size = FONT_SIZE_BODY
        run.bold = bold
        run.italic = italic

def _set_cell_shading(cell, fill_hex: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def _set_table_borderless(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = tblPr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement('w:tblBorders')
        tblPr.append(borders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        tag = 'w:{}'.format(edge)
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn('w:val'), 'nil')  # borderless

def _is_numeric_series(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s)

def _thousands(n):
    try:
        return f"{int(n):,}".replace(",", " ")
    except Exception:
        return str(n)

def _drop_blank_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    mask = pd.Series([True] * len(df))
    for col in df.columns:
        col_vals = df[col]
        mask = mask & ~(col_vals.isna() | (col_vals.astype(str).str.strip().isin(["", "—", "-", "None", "nan"])))
    return df[mask]

def _iconize_headers(headers: list[str]) -> list[str]:
    """
    BONUS: cədvəl başlıqlarına uyğun ikonlar əlavə edir.
    """
    out = []
    for h in headers:
        h_low = h.lower()
        if "statusu" in h_low or "status" in h_low:
            out.append(f"📄 {h}")
        elif h.strip().lower() in {"marka"}:
            out.append(f"🚗 {h}")
        elif h.strip().lower() in {"rəng", "reng"}:
            out.append(f"🎨 {h}")
        else:
            out.append(h)
    return out

def _add_table_from_df(doc: Document, df: pd.DataFrame, highlight_total_rows=True, zebra=True, iconize=True):
    """
    DF-dən borderless cədvəl:
     - başlıq sətri açıq mavi fon + bold
     - ədədi sütunlar sağa hizalı, minlik ayırıcı
     - zebra (alternating row)
     - 'CƏM' tipli sətirlər vurğulanır
     - BONUS: başlıqlara ikon (istəyə görə)
    """
    if df is None or df.empty:
        p = doc.add_paragraph("(Məlumat yoxdur)")
        _set_paragraph_format(p)
        return

    df = df.copy()
    numeric_cols = [c for c in df.columns if _is_numeric_series(df[c])]
    for c in numeric_cols:
        df[c] = df[c].apply(_thousands)

    rows, cols = df.shape
    table = doc.add_table(rows=rows + 1, cols=cols)
    _set_table_borderless(table)

    # Başlıq sətri
    headers = list(df.columns)
    if iconize:
        headers = _iconize_headers(headers)
    for j, col in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = str(col)
        _set_cell_shading(cell, COLOR_HEADER_BG)
        _format_cell_text(cell, bold=True, align_right=False)

    # Data sətirləri
    for i in range(rows):
        for j in range(cols):
            cell = table.cell(i + 1, j)
            val = "" if pd.isna(df.iat[i, j]) else str(df.iat[i, j])
            cell.text = val
            if zebra and (i % 2 == 1):
                _set_cell_shading(cell, COLOR_ZEBRA_BG)
            align_right = (df.columns[j] in numeric_cols)
            _format_cell_text(cell, bold=False, align_right=align_right)

    # Yekun sətirlərinin vurğulanması
    if highlight_total_rows:
        total_keywords = {"CƏM", "Cem", "Cəm", "Cəm say", "Cem say", "Cəm Say"}
        first_col = df.columns[0]
        for i in range(rows):
            label = str(df.iloc[i][first_col]).strip().upper()
            if any(k.upper() in label for k in total_keywords):
                for j in range(cols):
                    cell = table.cell(i + 1, j)
                    _set_cell_shading(cell, COLOR_TOTAL_BG)
                    _format_cell_text(cell, bold=True,
                                      align_right=(df.columns[j] in numeric_cols))

def _add_small_caption(doc: Document, text: str, italic=True):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after  = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(9.5)
    run.italic = italic

# =========================
# DOCX EXPORT
# =========================
def export_docx(report: dict, source_filename: str = "") -> bytes:
    """
    Word export:
    - Rəngli heading-lər (H1/H2), bölmələrarası nazik xətt
    - 'Hesabat tarixi' qırmızı
    - Borderless cədvəllər, başlıq fonu, zebra, yekun vurğusu
    - Üst/altbilgi (alt: yalnız tarix)
    - BONUS: ikonlu cədvəl başlıqları, Top bölmələr üçün fərqli başlıq rəngi
    """
    doc = Document()
    _set_document_defaults(doc)

    report_date = report.get("report_date") or datetime.now().strftime("%Y-%m-%d")
    _add_header_footer(doc, report_date)

    # Başlıq və Hesabat tarixi
    _add_heading(doc, "NVU Arayış Paneli — Hesabat", level=1)
    _add_report_date_line(doc, report_date)

    # 1) Utilizatorlar
    _add_heading(doc, "1) Utilizatorlar üzrə qəbul edilən NV sayları — yekun", level=1)
    _add_divider_line(doc)
    utilizator_df = report.get("utilizator_counts")
    if utilizator_df is not None:
        _add_table_from_df(doc, _drop_blank_rows(utilizator_df))
        _add_small_caption(doc, "Mənbə: NV qeydiyyat nömrəsi üzrə deduplikasiya (ən yeni R tarixi).")
    else:
        _add_small_caption(doc, "(Məlumat yoxdur)")

    # 2) Təsnifatlar
    _add_heading(doc, "2) Təsnifatlar üzrə — yekun", level=1)
    _add_divider_line(doc)
    tesnifat_df = report.get("tesnifat_table")
    if tesnifat_df is None:
        tesnifat_df = report.get("tesnifat_counts")
    if tesnifat_df is not None and hasattr(tesnifat_df, "empty") and not tesnifat_df.empty:
        cols = list(tesnifat_df.columns)
        if cols:
            cols[0] = "Təsnifat"
            tesnifat_df = tesnifat_df.copy()
            tesnifat_df.columns = cols
        _add_table_from_df(doc, _drop_blank_rows(tesnifat_df))
    else:
        _add_small_caption(doc, "(Məlumat yoxdur)")

    # 3) Təsdiqedici sənəd statusları
    _add_heading(doc, "3) Təsdiqedici sənədin statusları — yekun", level=1)
    _add_divider_line(doc)
    tesdiq_df = report.get("tesdiq_status_totals")
    if tesdiq_df is not None and hasattr(tesdiq_df, "empty") and not tesdiq_df.empty:
        _add_table_from_df(doc, _drop_blank_rows(tesdiq_df))
    else:
        _add_small_caption(doc, "(Məlumat yoxdur)")

    # 4) Təhvil-təslim statusları
    _add_heading(doc, "4) Təhvil-təslim sənədinin statusları — yekun", level=1)
    _add_divider_line(doc)
    tehvil_df = report.get("tehvil_status_totals")
    if tehvil_df is not None and hasattr(tehvil_df, "empty") and not tehvil_df.empty:
        _add_table_from_df(doc, _drop_blank_rows(tehvil_df))
    else:
        _add_small_caption(doc, "(Məlumat yoxdur)")

    # 5) Top 15 Ərizəçi (başlıq rəngi: yaşıl)
    _add_heading(doc, "5) Top 15 Ərizəçi", level=1, color=COLOR_TOP_ERIZECI)
    _add_divider_line(doc)
    top_erizeci_df = report.get("top_erizeci")
    if top_erizeci_df is not None and hasattr(top_erizeci_df, "empty") and not top_erizeci_df.empty:
        _add_table_from_df(doc, _drop_blank_rows(top_erizeci_df))
    else:
        _add_small_caption(doc, "(Məlumat yoxdur)")

    # 6) Marka Top 10 (başlıq rəngi: mavi)
    _add_heading(doc, "6) Marka Top 10", level=1, color=COLOR_TOP_MARKA)
    _add_divider_line(doc)
    top_marka_df = report.get("top_marka")
    if top_marka_df is not None and hasattr(top_marka_df, "empty") and not top_marka_df.empty:
        _add_table_from_df(doc, _drop_blank_rows(top_marka_df))
    else:
        _add_small_caption(doc, "(Məlumat yoxdur)")

    # 7) Modellər üzrə Top 10 (başlıq rəngi: bənövşəyi)
    _add_heading(doc, "7) Modellər üzrə Top 10", level=1, color=COLOR_TOP_MODEL)
    _add_divider_line(doc)
    top_model_df = report.get("top_model")
    if top_model_df is not None and hasattr(top_model_df, "empty") and not top_model_df.empty:
        _add_table_from_df(doc, _drop_blank_rows(top_model_df))
    else:
        _add_small_caption(doc, "(Məlumat yoxdur)")

    # 8) Rəng Top 10 (başlıq rəngi: narıncı-qırmızı)
    _add_heading(doc, "8) Rəng Top 10", level=1, color=COLOR_TOP_RENG)
    _add_divider_line(doc)
    top_reng_df = report.get("top_reng")
    if top_reng_df is not None and hasattr(top_reng_df, "empty") and not top_reng_df.empty:
        _add_table_from_df(doc, _drop_blank_rows(top_reng_df))
    else:
        _add_small_caption(doc, "(Məlumat yoxdur)")

    # 9) NV yaşları (10 illik)
    _add_heading(doc, "9) NV yaşları 10 illik intervallarda — yekun", level=1)
    _add_divider_line(doc)
    year_bins_df = report.get("year_bins")
    if year_bins_df is not None and hasattr(year_bins_df, "empty") and not year_bins_df.empty:
        _add_table_from_df(doc, _drop_blank_rows(year_bins_df))
        _add_small_caption(doc, 'Qeyd: “1110–1119” intervalı anomaliyadır (mənbə yazılışı).')
    else:
        _add_small_caption(doc, "(Məlumat yoxdur)")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

# =========================
# XLSX EXPORT
# =========================
def export_xlsx(report: dict) -> bytes:
    """
    XLSX export:
    - Hər bölmə ayrı vərəqdə
    - Utilizatorlar üçün CƏM sətiri yoxdursa, avtomatik əlavə olunur
    """
    from pandas import ExcelWriter

    def _with_total_row(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        tmp = df.copy()
        num_cols = [c for c in tmp.columns if pd.api.types.is_numeric_dtype(tmp[c])]
        if not num_cols:
            return tmp
        first_col = tmp.columns[0]
        # Artıq CƏM varsa, keç
        if str(tmp.iloc[-1][first_col]).strip().upper().startswith("CƏM"):
            return tmp
        total_col = num_cols[-1]
        total = tmp[total_col].sum()
        new_row = {col: "" for col in tmp.columns}
        new_row[first_col] = "CƏM"
        new_row[total_col] = total
        return pd.concat([tmp, pd.DataFrame([new_row])], ignore_index=True)

    output = BytesIO()
    with ExcelWriter(output, engine="openpyxl") as writer:
        df = report.get("utilizator_counts")
        if df is not None:
            _with_total_row(df).to_excel(writer, index=False, sheet_name="1_Utilizatorlar")

        df = report.get("tesnifat_table")
        if df is None:
            df = report.get("tesnifat_counts")
        if df is not None:
            cols = list(df.columns)
            if cols:
                cols[0] = "Təsnifat"
                df = df.copy()
                df.columns = cols
            df.to_excel(writer, index=False, sheet_name="2_Tesnifat")

        df = report.get("tesdiq_status_totals")
        if df is not None:
            df.to_excel(writer, index=False, sheet_name="3_Tesdiq_Status")

        df = report.get("tehvil_status_totals")
        if df is not None:
            df.to_excel(writer, index=False, sheet_name="4_Tehvil_Status")

        df = report.get("top_erizeci")
        if df is not None:
            df.to_excel(writer, index=False, sheet_name="5_Top_Erizeci")

        df = report.get("top_marka")
        if df is not None:
            df.to_excel(writer, index=False, sheet_name="6_Top_Marka")

        df = report.get("top_model")
        if df is not None:
            df.to_excel(writer, index=False, sheet_name="7_Top_Model")

        df = report.get("top_reng")
        if df is not None:
            df.to_excel(writer, index=False, sheet_name="8_Top_Reng")

        df = report.get("year_bins")
        if df is not None:
            df.to_excel(writer, index=False, sheet_name="9_Yas_Intervallar")

        meta = report.get("top_counts_meta")
        if meta:
            pd.DataFrame([meta]).to_excel(writer, index=False, sheet_name="10_Param_TopN")

        dt = report.get("report_date") or datetime.now().strftime("%Y-%m-%d")
        pd.DataFrame([{"Hesabat tarixi": dt}]).to_excel(writer, index=False, sheet_name="11_Info")

    output.seek(0)
    return output.getvalue()
