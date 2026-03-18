import streamlit as st
import requests
import pandas as pd
from io import StringIO

st.title("FRED connectivity test")

if st.button("Test FRED now"):
    for sid in ["IRLTLT01GBM156N", "IRLTLT01JPM156N",
                "IRLTLT01DEM156N", "IRLTLT01FRM156N"]:
        try:
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
            r   = requests.get(url, timeout=15,
                      headers={"User-Agent": "Mozilla/5.0"})
            st.write(f"**{sid}** — HTTP {r.status_code} — "
                     f"{len(r.text)} chars — "
                     f"preview: `{r.text[:60]}`")
        except Exception as e:
            st.error(f"**{sid}** — EXCEPTION: {e}")
