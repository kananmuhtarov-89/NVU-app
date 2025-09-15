from io import BytesIO
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import pandas as pd
ACCENT = RGBColor(0x1F, 0x4E, 0x79)
def _set_para_font(p, size=12, italic=False, bold=False, color=None, align=None, space_before=2, space_after=2):
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    for run in p.runs:
        run.font.name = "Arial"
        run.font.size = Pt(size)
        run.italic = italic
        run.bold = bold
        if color is not None:
            run.font.color.rgb = color
def _set_table_font(table, header_shade=True, compact=False, col_widths=None):
    for i, row in enumerate(table.rows):
        for cell in row.cells:
            for p in cell.paragraphs:
                pf = p.paragraph_format
                pf.space_before = Pt(1 if compact else 2)
                pf.space_after = Pt(2 if compact else 3)
                for run in p.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(12)
                    if i == 0:
                        run.bold = True
                        run.font.color.rgb = ACCENT
        if i == 0 and header_shade:
            for cell in row.cells:
                tcPr = cell._tc.get_or_add_tcPr()
                shd = OxmlElement('w:shd')
                shd.set(qn('w:fill'), "E9EFF7")
                shd.set(qn('w:val'), "clear")
                tcPr.append(shd)
def _add_section_heading(doc, text):
    cap = doc.add_paragraph(text)
    _set_para_font(cap, size=14, bold=True, color=ACCENT, space_after=6)
    try: cap.style = doc.styles['Heading 2']
    except Exception: pass
    return cap
def _add_collapsible_subheading(doc, text):
    sub = doc.add_paragraph(text)
    _set_para_font(sub, size=13, bold=True, color=ACCENT, space_after=4)
    try: sub.style = doc.styles['Heading 3']
    except Exception: pass
    return sub
def _add_table(doc, df: pd.DataFrame, compact=False):
    tbl = doc.add_table(rows=1, cols=len(df.columns))
    hdr = tbl.rows[0].cells
    for j, col in enumerate(df.columns):
        hdr[j].text = str(col)
    for _, row in df.iterrows():
        cells = tbl.add_row().cells
        for j, col in enumerate(df.columns):
            cells[j].text = str(row[col])
    _set_table_font(tbl, header_shade=True, compact=compact)
    doc.add_paragraph("")
    return tbl
def export_docx(report: dict, source_filename: str) -> bytes:
    doc = Document()
    doc.core_properties.title = "NVU Arayış"
    title_p = doc.add_paragraph("NVU Utilizasiya — Arayış")
    _set_para_font(title_p, size=18, bold=True, color=ACCENT, align=WD_ALIGN_PARAGRAPH.CENTER)
    dt = datetime.now().strftime('%Y-%m-%d %H:%M')
    _add = doc.add_paragraph; _set = _set_para_font
    _set(_add(f"Hesabat tarixi: {dt}"), size=12, italic=True)
    _set(_add(f"Mənbə fayl: {source_filename}"), size=12, italic=True)
    doc.add_paragraph("")
    for key, title in [
        ("utilizator_counts","1) Utilizatorlar üzrə qəbul edilən NV sayları"),
        ("tesnifat_counts","2) Təsnifatlar üzrə"),
        ("tesdiq_status_totals","3) Təsdiqedici sənədin statusları — yekun"),
        ("tehvil_status_totals","4) Təhvil-təslim sənədinin statusları — yekun"),
        ("top50_erizeci","5) Top-50 Ərizəçi"),
        ("top20_marka","6) Top-20 Marka"),
        ("top20_model","7) Top-20 Model (uyğunlaşdırılmış)"),
        ("top20_reng","8) Top-20 Rəng (uyğunlaşdırılmış)"),
        ("region_counts","9) Region paylanması (NV nömrəsinə görə)"),
        ("year_bins","10) NV-lərin yaş strukturu (10 illik dövrlərlə)"),
    ]:
        df = report.get(key)
        if df is not None and not df.empty:
            _add_section_heading(doc, title)
            if key=="top50_erizeci":
                top20=df.head(20); _add_table(doc, top20, compact=True)
                rest=df.iloc[20:]
                if not rest.empty:
                    _add_collapsible_subheading(doc,"Daha çox (21–50)")
                    _add_table(doc, rest, compact=True)
            elif key=="region_counts":
                df=df.sort_values("Say", ascending=False)
                top10=df.head(10); _add_table(doc, top10, compact=True)
                rest=df.iloc[10:]
                if not rest.empty:
                    _add_collapsible_subheading(doc,f"Daha çox (11–{len(df)})")
                    _add_table(doc, rest, compact=True)
            else:
                _add_table(doc, df, compact=True)
    doc.add_paragraph("")
    _set(doc.add_paragraph("K.M"), size=12, align=WD_ALIGN_PARAGRAPH.RIGHT)
    bio = BytesIO(); doc.save(bio); return bio.getvalue()
def export_xlsx(report: dict) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as w:
        for k, df in report.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.to_excel(w, sheet_name=str(k)[:31], index=False)
    return bio.getvalue()
