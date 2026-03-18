import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json

st.title("OECD parser test")
st.caption("OECD v2 returned HTTP 200 for GBR and JPN. Now parsing it.")

if st.button("Run parser test"):

    # Test OECD for all 4 countries
    for country_code, label in [("GBR","GB"), ("JPN","JP"), ("DEU","DE"), ("FRA","FR")]:
        st.subheader(f"{label} — {country_code}")
        try:
            url = (f"https://stats.oecd.org/sdmx-json/data/KEI/"
                   f"IRLTLT01.{country_code}.ST.M/all"
                   f"?startTime=2000-01&endTime=2025-12")
            r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
            st.write(f"HTTP {r.status_code} — {len(r.text)} chars")

            if r.status_code == 200:
                data = r.json()

                # Extract time periods
                obs_dims = data["structure"]["dimensions"]["observation"]
                time_vals = obs_dims[0]["values"]
                periods = [v["id"] for v in time_vals]

                # Extract series values
                series_data = data["dataSets"][0]["series"]
                first_key = list(series_data.keys())[0]
                obs = series_data[first_key]["observations"]

                # Build series
                rows = []
                for idx_str, vals in obs.items():
                    idx = int(idx_str)
                    if idx < len(periods) and vals[0] is not None:
                        rows.append({"date": periods[idx], "value": vals[0]})

                df = pd.DataFrame(rows)
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date").sort_index()

                st.success(f"✅ Parsed {len(df)} monthly rows — latest: {df['value'].iloc[-1]:.4f} on {df.index[-1].date()}")
                st.write(df.tail(5))

        except Exception as e:
            st.error(f"❌ {country_code}: {e}")

    st.divider()
    st.info("If all 4 show ✅ — OECD solves all pairs. Share screenshot!")
