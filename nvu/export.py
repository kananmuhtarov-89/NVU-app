# nvu/export.py
from io import BytesIO
import pandas as pd

# DOCX üçün səndə olan mövcud funksiyalar qalır (toxunmuruq).
# Burada yalnız XLSX export-u openpyxl-ə keçiririk və PowerBI_Feed əlavə edirik.

# ---- openpyxl stilləri (opsional; yoxdursa no-op) ----
try:
    from openpyxl.styles import Font, PatternFill, Alignment
except Exception:
    Font = PatternFill = Alignment = None

def _style_openpyxl_worksheet(ws, df: pd.DataFrame):
    """
    Power BI üçün oxunaqlılıq:
    - Header-lar bold + açıq mavi fon (#D9E1F2)
    - Sütun genişliklərini kontentə görə təxmini autosize
    """
    if ws is None or Font is None:
        return
    header_fill = PatternFill("solid", fgColor="D9E1F2")
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center")
    for idx, col in enumerate(df.columns, start=1):
        max_len = len(str(col))
        # böyük fayllarda sürət üçün 500 sətirə qədər ölçək
        for v in df[col].astype(str).values[:500]:
            max_len = max(max_len, len(v))
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = min(max(10, int(max_len * 1.2) + 2), 60)

# ---- XLSX export ----
def export_xlsx(report: dict) -> bytes:
    """
    report-dakı DataFrame-ləri ayrıca vərəqlərə yazır.
    openpyxl mühərrikindən istifadə edir (xlsxwriter tələb olunmur).
    'powerbi_feed' varsa, onu ayrıca 'PowerBI_Feed' vərəqində çıxarır.
    """
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        # 1) Utilizatorlar
        df = report.get("utilizator_counts")
        if isinstance(df, pd.DataFrame):
            name = "Utilizatorlar"
            df.to_excel(writer, sheet_name=name, index=False)
            _style_openpyxl_worksheet(writer.sheets.get(name), df)

        # 2) Təsnifat (calc_amounts True olduqda Cəmi (AZN) ola bilər)
        df = report.get("tesnifat_table") or report.get("tesnifat_counts")
        if isinstance(df, pd.DataFrame):
            name = "Təsnifat"
            df.to_excel(writer, sheet_name=name, index=False)
            _style_openpyxl_worksheet(writer.sheets.get(name), df)

        # 3) Status cədvəlləri və TOP-lar
        for key, name in [
            ("tesdiq_status_totals", "Təsdiq statusu"),
            ("tehvil_status_totals", "Təhvil statusu"),
            ("top_erizeci",          "Top ərizəçi"),
            ("top_marka",            "Top marka"),
            ("top_model",            "Top model"),
            ("top_reng",             "Top rəng"),
            ("year_bins",            "İllər üzrə"),
        ]:
            df = report.get(key)
            if isinstance(df, pd.DataFrame):
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
