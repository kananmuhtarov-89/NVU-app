from datetime import datetime
import io
import numpy as np
import pandas as pd
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from nvu.cleaning import _is_blank, to_decade_bins

# -------------------------
# Köməkçilər
# -------------------------

ALIASES = {
    "applicant": ["Ərizəçi", "Ərizəçi adı", "Applicant", "Müştəri", "Musteri"],
    "brand":     ["Marka", "Brand"],
    "model":     ["Model"],
    "color":     ["Rəng", "Reng", "Color"],
    "year":      ["Buraxılış ili", "İl", "Il", "İlk qeyd ili", "FirstRegYear"],
}

def _find_col(df: pd.DataFrame, keys) -> str | None:
    for k in keys:
        if k in df.columns:
            return k
    lower = {str(c).lower(): c for c in df.columns}
    for k in keys:
        lk = str(k).lower()
        if lk in lower:
            return lower[lk]
    return None

def drop_blank_status_rows(df: pd.DataFrame, status_cols: list[str] | None):
    """
    Status sütun(lar)ında BLANK olan sətrləri çıxarır.
    SABİT İSTİSNA KOD YOXDUR (952/938/955 və s. qalır).
    """
    if not status_cols:
        return df
    out = df.copy()
    for c in status_cols or []:
        if c and c in out.columns:
            out = out.loc[~out[c].apply(_is_blank)]
    return out

def top_n_table(series: pd.Series, n: int, label: str) -> pd.DataFrame:
    vc = (
        series.astype(str)
        .replace({"nan": "(bilinmir)", "None": "(bilinmir)", "": "(bilinmir)"})
        .value_counts()
        .head(n)
        .reset_index()
    )
    vc.columns = [label, "Say"]
    vc.insert(0, "Sıra №", range(1, len(vc) + 1))
    return vc

# -------------------------
# DOCX format köməkçilər
# -------------------------

def _set_borderless(table):
    tbl = table._element
    tblPr = tbl.get_or_add_tblPr()
    borders = tblPr.find(qn('w:tblBorders'))
    if borders is None:
        borders = OxmlElement('w:tblBorders')
        tblPr.append(borders)
    def nil(side):
        e = OxmlElement(side); e.set(qn('w:val'), 'nil'); return e
    for side in ['w:top','w:left','w:bottom','w:right','w:insideH','w:insideV']:
        old = borders.find(qn(side))
        if old is not None: borders.remove(old)
        borders.append(nil(side))

def _shade(cell, fill_hex="F2F2F2"):
    tc = cell._tc
    pr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    pr.append(shd)

def add_df_table(doc: Document, df: pd.DataFrame, title: str | None = None):
    if title:
        p = doc.add_paragraph(title)
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    rows, cols = df.shape
    t = doc.add_table(rows=rows + 1, cols=cols)
    # header
    for j, col in enumerate(df.columns):
        cell = t.cell(0, j)
        cell.text = str(col)
        for par in cell.paragraphs:
            for run in par.runs:
                run.font.bold = True
                run.font.size = Pt(10.5)
        _shade(cell)
    # body
    for i in range(rows):
        for j in range(cols):
            t.cell(i + 1, j).text = str(df.iat[i, j])
    _set_borderless(t)
    doc.add_paragraph("")

# -------------------------
# Report & Export
# -------------------------

def build_report(df: pd.DataFrame, session_state, *, status_cols: list[str] | None = None) -> dict:
    df2 = drop_blank_status_rows(df, status_cols=status_cols)

    # Sütun xəritəsi
    col_app   = _find_col(df2, ALIASES["applicant"])
    col_brand = _find_col(df2, ALIASES["brand"])
    col_model = _find_col(df2, ALIASES["model"])
    col_color = _find_col(df2, ALIASES["color"])
    col_year  = _find_col(df2, ALIASES["year"])

    # 10 illik intervallar
    if col_year:
        decade_bins = to_decade_bins(pd.to_numeric(df2[col_year], errors="coerce"))
        decade_tbl = (
            decade_bins[decade_bins != "Naməlum"]
            .value_counts()
            .sort_index()
            .rename_axis("İllər (10 illik)")
            .reset_index(name="Say")
        )
        decade_tbl.insert(0, "Sıra №", range(1, len(decade_tbl) + 1))
    else:
        decade_tbl = pd.DataFrame(columns=["Sıra №", "İllər (10 illik)", "Say"])

    # Parametrlərdən Top-N
    N_app   = int(session_state.get("param_topN_erizeci", 20))
    N_brand = int(session_state.get("param_topN_marka",   20))
    N_model = int(session_state.get("param_topN_model",   20))
    N_color = int(session_state.get("param_topN_reng",    20))

    report = {
        "generated_at": datetime.now(),
        "top_counts_meta": {"applicant": N_app, "brand": N_brand, "model": N_model, "color": N_color},
        "tables": {"decades": decade_tbl}
    }

    if col_app:
        report["tables"]["top_applicant"] = top_n_table(df2[col_app], N_app, col_app)
    if col_brand:
        report["tables"]["top_brand"] = top_n_table(df2[col_brand], N_brand, col_brand)
    if col_model:
        report["tables"]["top_model"] = top_n_table(df2[col_model], N_model, col_model)
    if col_color:
        report["tables"]["top_color"] = top_n_table(df2[col_color], N_color, col_color)

    return report

def export_docx(report: dict) -> bytes:
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(10.5)

    h = doc.add_paragraph("ESLİ – Arayış Hesabatı")
    h.runs[0].bold = True
    h.runs[0].font.size = Pt(14)
    doc.add_paragraph(report['generated_at'].strftime("Tarix: %d.%m.%Y"))

    # 10 illik
    if (tbl := report["tables"].get("decades")) is not None and not tbl.empty:
        add_df_table(doc, tbl, title="NV yaşları – 10 illik intervallar")

    meta = report["top_counts_meta"]
    if (tbl := report["tables"].get("top_applicant")) is not None:
        add_df_table(doc, tbl, title=f"Top-Ərizəçi (Top-{meta['applicant']})")
    if (tbl := report["tables"].get("top_brand")) is not None:
        add_df_table(doc, tbl, title=f"Marka Top-{meta['brand']}")
    if (tbl := report["tables"].get("top_model")) is not None:
        add_df_table(doc, tbl, title=f"Modellər Top-{meta['model']}")
    if (tbl := report["tables"].get("top_color")) is not None:
        add_df_table(doc, tbl, title=f"Rəng Top-{meta['color']}")

    bio = io.BytesIO()
    doc.save(bio); bio.seek(0)
    return bio.read()
