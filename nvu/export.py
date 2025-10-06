# nvu/export.py — v3 (blank-only filter, no hardcoded codes)
from datetime import datetime
import io
import numpy as np
import pandas as pd
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# ——— “boş” kimi qəbul edilən markerlər
BLANK_MARKERS = {None, "", " ", "-", "—", "–", "NA", "N/A", "None", "\xa0"}

ALIASES = {
    "applicant": ["Ərizəçi", "Erizeci", "Applicant", "Müştəri", "Musteri"],
    "brand":     ["Marka", "Brand"],
    "model":     ["Model"],
    "color":     ["Rəng", "Reng", "Color"],
    "year":      ["Buraxılış ili", "İl", "Il", "İlk qeyd ili", "FirstRegYear"],
}

# ——— Util
def _find_col(df: pd.DataFrame, keys):
    for k in keys:
        if k in df.columns:
            return k
    lower = {c.lower(): c for c in df.columns}
    for k in keys:
        if k.lower() in lower:
            return lower[k.lower()]
    return None

def _is_blank(x) -> bool:
    if pd.isna(x):
        return True
    if isinstance(x, str) and x.strip() in BLANK_MARKERS:
        return True
    return False

def drop_blank_status_rows(df: pd.DataFrame, status_cols: list[str] | None):
    """Status sütun(lar)ında BLANK olan sətrləri çıxarır. SABİT KOD YOXDUR."""
    if not status_cols:
        return df
    out = df.copy()
    for c in status_cols or []:
        if c and c in out.columns:
            out = out.loc[~out[c].apply(_is_blank)]
    return out

def ensure_decade_bins(df: pd.DataFrame) -> pd.Series:
    """Buraxılış ilini 10 illik zolaqlara çevirir: 1970–1979, 1980–1989, …"""
    year_col = _find_col(df, ALIASES["year"])
    years = pd.to_numeric(df.get(year_col, pd.Series(index=df.index)), errors="coerce")
    def lab(y):
        if np.isnan(y):
            return None
        d = int(y // 10 * 10)
        return f"{d}–{d+9}"
    return years.apply(lab)

def top_n_table(series: pd.Series, n: int, colname: str) -> pd.DataFrame:
    vc = (
        series.astype(str)
        .replace({"nan": "(bilinmir)", "None": "(bilinmir)", "": "(bilinmir)"})
        .value_counts()
        .head(n)
        .reset_index()
    )
    vc.columns = [colname, "Say"]
    vc.insert(0, "Sıra №", range(1, len(vc) + 1))
    return vc

# ——— DOCX köməkçilər
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

def add_table(doc: Document, df: pd.DataFrame, title: str | None = None):
    if title:
        p = doc.add_paragraph(title)
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(12)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r, c = df.shape
    t = doc.add_table(rows=r+1, cols=c)
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
    for i in range(r):
        for j in range(c):
            t.cell(i+1, j).text = str(df.iat[i, j])
    _set_borderless(t)
    doc.add_paragraph("")

# ——— Report qurucu
def build_report(
    df: pd.DataFrame,
    session_state,
    *,
    status_cols: list[str] | None = None,
    include_blanks: bool = False,
) -> dict:
    # blank filter (istifadəçi istəyinə görə)
    df2 = df.copy() if include_blanks else drop_blank_status_rows(df, status_cols)

    # sütunlar
    col_app = _find_col(df2, ALIASES["applicant"])
    col_brand = _find_col(df2, ALIASES["brand"])
    col_model = _find_col(df2, ALIASES["model"])
    col_color = _find_col(df2, ALIASES["color"])

    # decade bins
    decade_bins = ensure_decade_bins(df2)
    decade_tbl = (
        decade_bins.dropna()
        .value_counts()
        .sort_index()
        .rename_axis("İllər (10 illik)")
        .reset_index(name="Say")
    )
    decade_tbl.insert(0, "Sıra №", range(1, len(decade_tbl) + 1))

    # Top-N-lər: sessiyadan oxu
    N_app   = int(session_state.get("param_topN_erizeci", 10))
    N_brand = int(session_state.get("param_topN_marka",   10))
    N_model = int(session_state.get("param_topN_model",   10))
    N_color = int(session_state.get("param_topN_reng",    10))

    report = {
        "generated_at": datetime.now(),
        "top_counts_meta": {
            "applicant": N_app, "brand": N_brand, "model": N_model, "color": N_color
        },
        "tables": {"decades": decade_tbl},
    }
    if col_app:   report["tables"]["top_applicant"] = top_n_table(df2[col_app], N_app, col_app)
    if col_brand: report["tables"]["top_brand"]     = top_n_table(df2[col_brand], N_brand, col_brand)
    if col_model: report["tables"]["top_model"]     = top_n_table(df2[col_model], N_model, col_model)
    if col_color: report["tables"]["top_color"]     = top_n_table(df2[col_color], N_color, col_color)
    return report

def export_docx(report: dict) -> bytes:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(10.5)

    h = doc.add_paragraph("ESLİ – Arayış Hesabatı")
    h.runs[0].bold = True
    h.runs[0].font.size = Pt(14)
    doc.add_paragraph(report["generated_at"].strftime("Tarix: %d.%m.%Y"))

    # 10 illik intervallar
    tbl = report["tables"].get("decades")
    if tbl is not None:
        add_table(doc, tbl, title="NV yaşları – 10 illik intervallar")

    meta = report["top_counts_meta"]
    if (t := report["tables"].get("top_applicant")) is not None:
        add_table(doc, t, title=f"Top-Ərizəçi (Top-{meta['applicant']})")
    if (t := report["tables"].get("top_brand")) is not None:
        add_table(doc, t, title=f"Marka Top-{meta['brand']}")
    if (t := report["tables"].get("top_model")) is not None:
        add_table(doc, t, title=f"Modellər Top-{meta['model']}")
    if (t := report["tables"].get("top_color")) is not None:
        add_table(doc, t, title=f"Rəng Top-{meta['color']}")

    bio = io.BytesIO()
    doc.save(bio); bio.seek(0)
    return bio.read()
