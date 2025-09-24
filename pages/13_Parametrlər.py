
import streamlit as st, pandas as pd
from nvu.settings import get_settings, set_settings, CANON_COLS, upload_settings, download_settings_button

st.title("Parametrlər")

cfg = get_settings()

st.subheader("1) Sütun xəritəsi")
st.caption("Soldakı (kanonik) → sağdakı (sənin fayldakı konkret başlıq). Xəritəni yadda saxla və export et.")
colmap = cfg.get("column_map",{}).copy()
for canon in CANON_COLS:
    colmap[canon] = st.text_input(canon, value=colmap.get(canon, ""), key=f"colmap_{canon}")
cfg["column_map"] = colmap

st.subheader("2) Top-N dəyərləri")
c1,c2,c3,c4 = st.columns(4)
cfg["topN"]["applicant"] = c1.number_input("Top-N Ərizəçi", 10, 100, cfg["topN"]["applicant"], 5)
cfg["topN"]["brand"]     = c2.number_input("Top-N Marka", 10, 100, cfg["topN"]["brand"], 5)
cfg["topN"]["model"]     = c3.number_input("Top-N Model", 10, 100, cfg["topN"]["model"], 5)
cfg["topN"]["color"]     = c4.number_input("Top-N Rəng", 10, 100, cfg["topN"]["color"], 5)

st.subheader("3) Dedup qaydaları")
keys = cfg.get("dedup_keys", [])
opts = ["Təhvil aktının seriya nömrəsi","Təsdiqedici sənədin seriyası","NV qeydiyyat nömrəsi"]
sel = st.multiselect("Təkrarı silmək üçün istifadə ediləcək açarlar", options=opts, default=keys)
cfg["dedup_keys"] = sel

st.subheader("4) Status sözlükləri")
with st.expander("Təsdiq edici sənədin statusu — sinonimlər"):
    d = cfg["status_dict"]["tesdiq"]
    for canon, alts in d.items():
        cfg["status_dict"]["tesdiq"][canon] = st.text_area(canon, value=", ".join(alts)).split(",")
with st.expander("Təhvil-təslim sənədinin statusu — sinonimlər"):
    d2 = cfg["status_dict"]["tehvil"]
    for canon, alts in d2.items():
        cfg["status_dict"]["tehvil"][canon] = st.text_area(canon, value=", ".join(alts)).split(",")

st.divider()
if st.button("Parametrləri yadda saxla (sessiya daxilində)"):
    set_settings(cfg); st.success("Parametrlər yadda saxlandı (sessiya).")

c5,c6 = st.columns(2)
with c5: download_settings_button()
with c6: upload_settings()
