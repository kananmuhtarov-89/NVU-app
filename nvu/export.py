# nvu/export.py
from io import BytesIO
from typing import Dict, Any, Optional
import pandas as pd
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# -------------------- Köməkçilər --------------------
def _fmt_int(x: Optional[int]) -> str:
    if x is None: return "—"
    return f"{int(x):,}".replace(",", " ")

def _make_table_borderless(table):
    # python-docx ilə borderləri söndürmək üçün minimal yol
    tbl = table._tbl
    tblPr = tbl.tblPr
    for el in tblPr.xpath("./w:tblBorders", namespaces=tblPr.nsmap):
        tblPr.remove(el)

def _add_table(doc: Document, df: pd.DataFrame, add_rownum: bool = False) -> None:
    dfx = df.copy()
    if add_rownum and len(dfx) > 0:
        dfx.insert(0, "Sıra №", range(1, len(dfx) + 1))

    table = doc.add_table(rows=1, cols=len(dfx.columns))
    _make_table_borderless(table)

    hdr = table.rows[0].cells
    for i, col in enumerate(dfx.columns):
        p = hdr[i].paragraphs[0]
        run = p.add_run(str(col))
        run.bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    for _, row in dfx.iterrows():
        cells = table.add_row().cells
        for j, col in enumerate(dfx.columns):
            val = row[col]
            cells[j].text = "" if pd.isna(val) else str(val)

def _subset(df: pd.DataFrame, preferred_cols) -> pd.DataFrame:
    cols = [c for c in preferred_cols if c in df.columns]
    return df[cols].copy() if cols else df.copy()

# -------------------- DOCX --------------------
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
        if util.shape[1] >= 2:
            total = int(util.iloc[:,1].sum())
            util_out = util.copy()
            util_out.loc[len(util_out), util_out.columns[0]] = "CƏM"
            util_out.loc[len(util_out)-1, util_out.columns[1]] = total
        else:
            util_out = util.copy()
        _add_table(doc, util_out, add_rownum=False)
    else:
        doc.add_paragraph("Məlumat yoxdur.")

    # 2) Təsnifat
    doc.add_heading("2) Təsnifatlar üzrə", level=2)
    calc = bool(report.get("tesnifat_settings", {}).get("calc_amounts", False))
    ready = report.get("tesnifat_table")
    if isinstance(ready, pd.DataFrame) and not ready.empty:
        # yalnız lazım olan sütunlar; Açıqlama yoxdur
        pref = ["Kod","Təsnifat","Say"] + (["Cəmi (AZN)"] if calc else [])
        t = _subset(ready, pref)
        # ehtiyat: əgər sadəcə "Kod" yoxdursa "Təsnifat"dan istifadə
        if "Kod" not in t.columns and "Təsnifat" in t.columns:
            t = t.rename(columns={"Təsnifat":"Kod"})
        t = t[["Kod","Say"] + (["Cəmi (AZN)"] if calc and "Cəmi (AZN)" in t.columns else [])]
        _add_table(doc, t, add_rownum=False)
        if "Say" in t.columns:
            p = doc.add_paragraph(); p.add_run(f"Cəm say: {_fmt_int(int(t['Say'].sum()))}").bold = True
        if calc and "Cəmi (AZN)" in t.columns:
            p = doc.add_paragraph(); p.add_run(f"Ümumi məbləğ (AZN): {_fmt_int(int(t['Cəmi (AZN)'].sum()))}").bold = True
    else:
        base = report.get("tesnifat_counts", pd.DataFrame())
        t = _subset(base, ["Təsnifat","Say"])
        _add_table(doc, t, add_rownum=False)

    # 3+) Digər bölmələr – dinamik başlıqlar + Sıra №
    meta = report.get("top_counts_meta", {})
    sections = [
        ("3) Təsdiqedici Statusları", "tesdiq_status_totals",
         ["Təsdiq edici sənədin statusu","Say"], False),
        ("4) TT aktların Statusları", "tehvil_status_totals",
         ["Təhvil-təslim sənədinin statusu","Say"], False),
        (f"5) Top {meta.get('erizeci_N', 50)} Ərizəçi", "top_erizeci",
         ["Ərizəçinin tam adı","Say"], True),
        (f"6) Marka Top {meta.get('marka_N', 20)}", "top_marka",
         ["Marka","Say"], True),
        (f"7) Modellər üzrə Top {meta.get('model_N', 10)}", "top_model",
         ["Marka","Model","Say"], True),
        (f"8) Rəng Top {meta.get('reng_N', 10)}", "top_reng",
         ["Rəng","Say"], True),
        ("9) NV yaşları 10illik intervallarda", "year_bins",
         ["Buraxılış ili","Say"], False),
    ]
    for title, key, pref, add_no in sections:
        doc.add_heading(title, level=2)
        d = report.get(key, pd.DataFrame())
        if isinstance(d, pd.DataFrame) and not d.empty:
            _add_table(doc, _subset(d, pref), add_rownum=add_no)
        else:
            doc.add_paragraph("Məlumat yoxdur.")

    bio = BytesIO(); doc.save(bio)
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
            util2.loc[len(util2), util2.columns[0]] = "CƏM"
            util2.loc[len(util2)-1, util2.columns[1]] = int(util.iloc[:,1].sum())
            util2.to_excel(xw, sheet_name="utilizator_counts", index=False)

        # Təsnifat: hazır cədvəl yoxdursa baza yaz
        tbl = report.get("tesnifat_table")
        if not (isinstance(tbl, pd.DataFrame) and not tbl.empty):
            base = report.get("tesnifat_counts", pd.DataFrame())
            if isinstance(base, pd.DataFrame) and not base.empty:
                _subset(base, ["Təsnifat","Say"]).to_excel(xw, sheet_name="tesnifatlar", index=False)

    return bio.getvalue()
