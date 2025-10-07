from io import BytesIO
from typing import Dict, Any, Optional
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# -------------------- util --------------------
def _fmt_int(x: Optional[int]) -> str:
    if x is None: return "—"
    try: return f"{int(x):,}".replace(",", " ")
    except Exception: return str(x)

def _make_table_borderless(table):
    try:
        tbl = table._tbl
        tblPr = getattr(tbl, "tblPr", None) or getattr(tbl, "get_or_add_tblPr", lambda: None)()
        if tblPr is None: return
        NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        for el in tblPr.xpath("./w:tblBorders", namespaces=NS):
            tblPr.remove(el)
    except Exception: pass

def _shade_cell(cell, fill_hex="D9E1F2"):
    try:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), fill_hex)
        tcPr.append(shd)
    except Exception: pass

def _set_table_cell_margins(table, top=80, bottom=80, left=80, right=80):
    try:
        tbl = table._tbl
        tblPr = getattr(tbl, "tblPr", None) or getattr(tbl, "get_or_add_tblPr", lambda: None)()
        if tblPr is None: return
        cellMar = tblPr.find(qn("w:tblCellMar"))
        if cellMar is None:
            cellMar = OxmlElement("w:tblCellMar")
            tblPr.append(cellMar)
        def _set(side, val):
            el = cellMar.find(qn(f"w:{side}"))
            if el is None:
                el = OxmlElement(f"w:{side}")
                cellMar.append(el)
            el.set(qn("w:w"), str(val))
            el.set(qn("w:type"), "dxa")
        for s, v in [("top",top),("bottom",bottom),("left",left),("right",right)]:
            _set(s, v)
    except Exception: pass

def _to_text(val) -> str:
    if pd.isna(val): return "—"
    s = str(val).strip()
    if s.lower() in ("nan","none",""): return "—"
    try:
        if isinstance(val, float) and float(val).is_integer(): return _fmt_int(int(val))
        if isinstance(val, int): return _fmt_int(val)
    except Exception: pass
    return s

def _sanitize_df_for_docx(df: pd.DataFrame) -> pd.DataFrame:
    dfx = df.copy()
    for c in dfx.columns: dfx[c] = dfx[c].map(_to_text)
    return dfx

def _drop_blank_rows(df: pd.DataFrame, key_cols) -> pd.DataFrame:
    dfx = df.copy(); mask = pd.Series(True, index=dfx.index)
    for c in key_cols:
        if c in dfx.columns:
            s = dfx[c].astype(str).str.strip()
            mask &= ~(s.isna() | (s=="") | s.str.lower().isin(["nan","none","—"]))
    return dfx[mask].copy()

def _add_table(doc: Document, df: pd.DataFrame, add_rownum: bool = False) -> None:
    dfx = df.copy()
    if add_rownum and len(dfx)>0: dfx.insert(0, "Sıra №", range(1, len(dfx)+1))
    dfx = _sanitize_df_for_docx(dfx)
    table = doc.add_table(rows=1, cols=len(dfx.columns))
    table.allow_autofit = True
    _set_table_cell_margins(table); _make_table_borderless(table)

    hdr = table.rows[0].cells
    for i, col in enumerate(dfx.columns):
        _shade_cell(hdr[i])
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(str(col)); run.bold = True; run.font.name = "Arial"; run.font.size = Pt(11)

    for _, row in dfx.iterrows():
        cells = table.add_row().cells
        for j, col in enumerate(dfx.columns):
            p = cells[j].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(row[col]); run.font.name = "Arial"; run.font.size = Pt(11)

def _subset(df: pd.DataFrame, preferred_cols) -> pd.DataFrame:
    cols = [c for c in preferred_cols if c in df.columns]
    return df[cols].copy() if cols else df.copy()

# -------------------- DOCX --------------------
def export_docx(report: Dict[str, Any], source_filename: str = "") -> bytes:
    """
    Toggle calc_amounts:
      - True  → “Cəmi (AZN)” sütunu + “Ümumi məbləğ (AZN)” sətiri göstərilir
      - False → hər ikisi gizlədilir
    """
    # ---- GUARD: report mütləq dict olsun ----
    if not isinstance(report, dict):
        if isinstance(report, pd.DataFrame):
            report = {"tesnifat_table": report}
        else:
            report = {}

    # calc_amounts təhlükəsiz oxunur
    ts = report.get("tesnifat_settings")
    if not isinstance(ts, dict): ts = {}
    calc = bool(ts.get("calc_amounts", False))

    doc = Document()

    # Ümumi stil – Arial 12
    base = doc.styles["Normal"]; base.font.name = "Arial"; base.font.size = Pt(12)
    # Heading style-lar
    h1 = doc.styles["Heading 1"]; h1.font.name = "Arial"; h1.font.size = Pt(18); h1.font.color.rgb = RGBColor(0x12,0x3A,0x7A)
    h2 = doc.styles["Heading 2"]; h2.font.name = "Arial"; h2.font.size = Pt(14); h2.font.color.rgb = RGBColor(0x1F,0x5A,0xB6)

    # Başlıq
    doc.add_heading("NVU Arayış Paneli — Hesabat", level=1)
    p = doc.add_paragraph()
    r1 = p.add_run("Hesabat tarixi: "); r1.bold = True; r1.font.color.rgb = RGBColor(0xFF,0x00,0x00)
    p.add_run(pd.Timestamp.now().strftime(" %Y-%m-%d %H:%M"))

    # 2) Təsnifat
    doc.add_heading("2) Təsnifatlar üzrə — yekun", level=2)
    ready = report.get("tesnifat_table")

    AMOUNT_ALIASES = ["Cəmi (AZN)", "Cəmi(AZN)", "Cemi (AZN)", "Cemi(AZN)"]

    if isinstance(ready, pd.DataFrame) and not ready.empty:
        pref = ["Kod", "Təsnifat", "Say"] + (AMOUNT_ALIASES if calc else [])
        t = _subset(ready, pref).copy()

        # alias-ları standarta çevir
        for a in AMOUNT_ALIASES:
            if a in t.columns and a != "Cəmi (AZN)":
                t.rename(columns={a: "Cəmi (AZN)"}, inplace=True)

        # calc ON + hələ də “Cəmi (AZN)” yoxdursa → yerində hesabla
        if calc and "Cəmi (AZN)" not in t.columns and "Say" in t.columns:
            code_col = "Kod" if "Kod" in t.columns else ("Təsnifat" if "Təsnifat" in t.columns else None)
            if code_col is not None:
                _rates = {
                    "M1":1500,"M2":2000,"M3":3000,
                    "N1":1500,"N2":2000,"N3":3000,
                    "T":2000,"TK":2000,"TT":2000,
                    "H":3000,"HT":3000,"HK":3000,"L":200
                }
                def _norm(c: str) -> str:
                    s = str(c).strip().upper()
                    return s[:-1] if s.endswith("G") and s[:-1] in _rates else s
                rates = t[code_col].map(_norm).map(lambda k: _rates.get(k, 0))
                say = pd.to_numeric(t["Say"], errors="coerce").fillna(0).astype(int)
                t["Cəmi (AZN)"] = (rates * say).astype(int)

        # çıxış sütunları
        cols = []
        if "Kod" in t.columns: cols.append("Kod")
        elif "Təsnifat" in t.columns: cols.append("Təsnifat")
        if "Say" in t.columns: cols.append("Say")
        if calc and "Cəmi (AZN)" in t.columns:
            t["Cəmi (AZN)"] = pd.to_numeric(t["Cəmi (AZN)"], errors="coerce").fillna(0).astype(int)
            cols.append("Cəmi (AZN)")

        t_display = t[cols].copy()
        if len(t_display.columns) > 0:
            first_col = t_display.columns[0]
            t_display.rename(columns={first_col: "Təsnifat"}, inplace=True)

        _add_table(doc, t_display, add_rownum=False)

        if "Say" in t.columns:
            p = doc.add_paragraph()
            p.add_run(f"Cəm say: {_fmt_int(int(pd.to_numeric(t['Say'], errors='coerce').fillna(0).sum()))}").bold = True
        if calc and "Cəmi (AZN)" in t.columns:
            p = doc.add_paragraph()
            p.add_run(f"Ümumi məbləğ (AZN): {_fmt_int(int(pd.to_numeric(t['Cəmi (AZN)'], errors='coerce').fillna(0).sum()))}").bold = True
    else:
        base = report.get("tesnifat_counts", pd.DataFrame())
        t = _subset(base, ["Təsnifat", "Say"])
        _add_table(doc, t, add_rownum=False)

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# -------------------- XLSX (dəyişmədən qala bilər) --------------------
try:
    from openpyxl.styles import Font, PatternFill, Alignment
except Exception:
    Font = PatternFill = Alignment = None

def _style_openpyxl_worksheet(ws, df: pd.DataFrame):
    if ws is None or Font is None: return
    header_fill = PatternFill("solid", fgColor="D9E1F2")
    for cell in ws[1]:
        cell.font = Font(bold=True); cell.fill = header_fill; cell.alignment = Alignment(vertical="center")
    for idx, col in enumerate(df.columns, start=1):
        max_len = len(str(col))
        for v in df[col].astype(str).values[:500]:
            max_len = max(max_len, len(v))
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = min(max(10, int(max_len*1.2)+2), 60)

def export_xlsx(report: dict) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for key, sheet_name in [
            ("utilizator_counts","Utilizatorlar"),
            ("tesnifat_table","Təsnifat"),
            ("tesnifat_counts","Təsnifat"),
            ("tesdiq_status_totals","Təsdiq statusu"),
            ("tehvil_status_totals","Təhvil statusu"),
            ("top_erizeci","Top ərizəçi"),
            ("top_marka","Top marka"),
            ("top_model","Top model"),
            ("top_reng","Top rəng"),
            ("year_bins","İllər üzrə"),
        ]:
            df = report.get(key)
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                _style_openpyxl_worksheet(writer.sheets.get(sheet_name), df)
    bio.seek(0)
    return bio.getvalue()
