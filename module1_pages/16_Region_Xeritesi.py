
import streamlit as st, json, os
st.title("Region xəritəsi (NV kodu → Region)")

path = os.path.join(os.path.dirname(__file__), "..", "data", "az_region_codes.json")
if not os.path.exists(path):
    st.error("az_region_codes.json faylı tapılmadı."); st.stop()

with open(path,"r",encoding="utf-8") as f:
    data = json.load(f)

st.caption("Redaktə et və faylı yüklə/saxla (buludda daimi saxlamaq mümkün deyil, JSON qeydini endir).")
rows = [{"Kod": k, "Region": v} for k,v in data.items()]
edited = st.data_editor(rows, num_rows="dynamic", use_container_width=True)
if st.button("JSON olaraq yüklə"):
    new_map = {row["Kod"]: row["Region"] for row in edited if row.get("Kod")}
    st.download_button("az_region_codes.json", data=json.dumps(new_map, ensure_ascii=False, indent=2).encode("utf-8"),
                       file_name="az_region_codes.json", mime="application/json")
