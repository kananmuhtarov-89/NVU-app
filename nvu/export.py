import pandas as pd
from nvu.cleaning import _is_blank, to_decade_bins

BLANK_MARKERS = {None, "", " ", "-", "—", "–", "NA", "N/A", "None", "\xa0"}

def drop_excluded_status_rows(df, status_cols=None):
    """
    Status sütunlarındakı blank sətrləri silir.
    Sabit istisna kod YOXDUR (952 və s. qalır).
    """
    if not status_cols:
        return df
    out = df.copy()
    for c in status_cols or []:
        if c and c in out.columns:
            out = out.loc[~out[c].apply(_is_blank)]
    return out


def build_report(df, session_state, *, status_cols=None):
    """
    NVU hesabat obyektini yaradır — boş sətrləri çıxarır, 10 illik intervallar formalaşdırır.
    """
    df = drop_excluded_status_rows(df, status_cols=status_cols)
    report = {}

    # NV yaşları (10 illik)
    if "Buraxılış ili" in df.columns:
        report["year_bins"] = to_decade_bins(df["Buraxılış ili"])
    else:
        report["year_bins"] = pd.Series([], dtype=str)

    # Top-N parametrləri sessiyadan oxu
    report["top_counts_meta"] = {
        "erizeci": session_state.get("param_topN_erizeci", 20),
        "marka": session_state.get("param_topN_marka", 20),
        "model": session_state.get("param_topN_model", 20),
        "reng": session_state.get("param_topN_reng", 20),
    }

    # Burada digər hissələr (Word export və s.) eynilə qalır
    return report
