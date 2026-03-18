import streamlit as st
import requests
import pandas as pd
from io import StringIO

st.title("Bond yield source test — GB + JP focus")
st.caption("ECB EA aggregate confirmed working. Now finding GB + JP sources.")

if st.button("Run tests"):

    # ── ECB EA aggregate (confirmed working) — parse it ───────────────────────
    st.subheader("ECB EA aggregate — parse test")
    try:
        url = ("https://data-api.ecb.europa.eu/service/data/"
               "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"
               "?format=csvdata&startPeriod=2020-01-01")
        r = requests.get(url, timeout=20)
        df = pd.read_csv(StringIO(r.text))
        st.write(f"Columns: {df.columns.tolist()}")
        st.write(f"Rows: {len(df)}")
        st.write(df.tail(3))
    except Exception as e:
        st.error(f"ECB parse error: {e}")

    st.divider()

    # ── OECD with corrected URL format ────────────────────────────────────────
    st.subheader("OECD — corrected URLs")
    oecd_urls = {
        "GBR v1": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_KEI@DF_KEI,4.0/GBR.M.IRLTLT01.ST.....?format=csvfilewithlabels&startPeriod=2020-01",
        "JPN v1": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_KEI@DF_KEI,4.0/JPN.M.IRLTLT01.ST.....?format=csvfilewithlabels&startPeriod=2020-01",
        "GBR v2": "https://stats.oecd.org/sdmx-json/data/KEI/IRLTLT01.GBR.ST.M/all?startTime=2020-01&endTime=2025-12",
        "JPN v2": "https://stats.oecd.org/sdmx-json/data/KEI/IRLTLT01.JPN.ST.M/all?startTime=2020-01&endTime=2025-12",
    }
    for label, url in oecd_urls.items():
        try:
            r = requests.get(url, timeout=15)
            st.write(f"**{label}** HTTP {r.status_code} — {len(r.text)} chars — `{r.text[:100]}`")
        except Exception as e:
            st.error(f"❌ {label}: {e}")

    st.divider()

    # ── BIS (Bank for International Settlements) ──────────────────────────────
    st.subheader("BIS API")
    for label, url in {
        "GB 10Y": "https://stats.bis.org/api/v2/data/BIS,WS_LONG_CPI,1.0/M.GB.L.L40.A.A.A.A.A?format=csv&startPeriod=2020-01",
        "JP 10Y": "https://stats.bis.org/api/v2/data/BIS,WS_LONG_CPI,1.0/M.JP.L.L40.A.A.A.A.A?format=csv&startPeriod=2020-01",
    }.items():
        try:
            r = requests.get(url, timeout=15)
            st.write(f"**{label}** HTTP {r.status_code} — {len(r.text)} chars — `{r.text[:100]}`")
        except Exception as e:
            st.error(f"❌ BIS {label}: {e}")

    st.divider()

    # ── Bundesbank (DE) + direct central bank APIs ────────────────────────────
    st.subheader("Direct central bank APIs")
    apis = {
        "Bundesbank DE 10Y": "https://api.bundesbank.de/service/data/BBDP/M.DE.EUR.BBK01.WT1010?format=sdmx-json&startPeriod=2020-01",
        "BOJ JP 10Y (simple)": "https://www.stat-search.boj.or.jp/ssi/mtsindex/elabel_search.do?startDate=2023-01-01&endDate=&series=FM08%2FFM08_D_R_10Y&type=default&outputFormat=CSV",
        "Investing GB 10Y": "https://api.investing.com/api/financialdata/2040/historical/chart?period=P1Y&interval=P1M&pointscount=60",
    }
    for label, url in apis.items():
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
            st.write(f"**{label}** HTTP {r.status_code} — {len(r.text)} chars — `{r.text[:100]}`")
        except Exception as e:
            st.error(f"❌ {label}: {e}")

    st.divider()

    # ── Stooq CSV (different from pandas_datareader) ──────────────────────────
    st.subheader("Stooq direct CSV")
    for label, sym in [("GB 10Y", "10gb.b"), ("JP 10Y", "10jp.b")]:
        try:
            url = f"https://stooq.com/q/d/l/?s={sym}&i=m"
            r   = requests.get(url, timeout=15,
                      headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            st.write(f"**{label} ({sym})** HTTP {r.status_code} — {len(r.text)} chars — `{r.text[:100]}`")
        except Exception as e:
            st.error(f"❌ Stooq {label}: {e}")

    st.info("Share screenshot — any HTTP 200 with real data = our source!")
