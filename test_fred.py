import streamlit as st
import requests
import pandas as pd

st.title("OECD final parser fix")

if st.button("Run"):
    for country_code, label in [("GBR","GB"),("JPN","JP"),("DEU","DE"),("FRA","FR")]:
        try:
            url = (f"https://stats.oecd.org/sdmx-json/data/KEI/"
                   f"IRLTLT01.{country_code}.ST.M/all"
                   f"?startTime=2000-01&endTime=2025-12")
            r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
            raw = r.json()

            # raw is a DICT with keys 'meta', 'data', 'errors'
            data_block = raw["data"]
            structure  = data_block["structure"]
            datasets   = data_block["dataSets"]

            # Time periods from dimensions
            obs_dims = structure["dimensions"]["observation"]
            time_dim = next(d for d in obs_dims if d.get("id") == "TIME_PERIOD"
                            or d.get("role","").upper() == "TIME"
                            or d == obs_dims[-1])
            periods = [v["id"] for v in time_dim["values"]]

            # Extract observations
            series = datasets[0]["series"]
            first_key = list(series.keys())[0]
            obs = series[first_key]["observations"]

            rows = []
            for idx_str, vals in obs.items():
                idx = int(idx_str)
                if idx < len(periods) and vals[0] is not None:
                    rows.append({"date": periods[idx], "value": float(vals[0])})

            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()

            st.success(f"✅ **{label}**: {len(df)} monthly rows — "
                       f"latest {df['value'].iloc[-1]:.4f} on {df.index[-1].date()}")

        except Exception as e:
            # Show raw keys to debug further
            try:
                st.error(f"❌ **{label}**: {e}")
                st.code(f"raw type: {type(raw)}, keys: {list(raw.keys()) if isinstance(raw,dict) else raw[:2]}")
            except:
                st.error(f"❌ **{label}**: {e}")

    st.info("✅ on all 4 = ready to fix the screener!")
