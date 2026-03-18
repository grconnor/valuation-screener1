import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from io import StringIO

st.title("Bond yield source test")
st.caption("Tests every viable source for DE, FR, GB, JP 10Y yields from Streamlit Cloud")

if st.button("Run all tests"):

    # ── 1. Yahoo Finance tickers ──────────────────────────────────────────────
    st.subheader("1. Yahoo Finance")
    for country, tickers in {
        "DE": ["DE10YT=RR","^TNDE","DEAT10Y=RR"],
        "FR": ["FR10YT=RR","^TNFR","FRAT10Y=RR"],
        "GB": ["GB10YT=RR","^TNGB","GBAT10Y=RR"],
        "JP": ["JP10YT=RR","^TNJP","JPAT10Y=RR"],
    }.items():
        found = False
        for tk in tickers:
            try:
                df = yf.Ticker(tk).history(period="1y", auto_adjust=True)
                if df is not None and not df.empty and "Close" in df.columns:
                    s = df["Close"].dropna()
                    if len(s) > 10:
                        st.success(f"✅ {country} — {tk}: {len(s)} bars, latest={s.iloc[-1]:.4f}")
                        found = True
                        break
            except Exception as e:
                st.error(f"❌ {country} — {tk}: {e}")
        if not found:
            st.error(f"❌ {country} — all Yahoo tickers failed")

    # ── 2. ECB SDW API ────────────────────────────────────────────────────────
    st.subheader("2. ECB SDW API (DE + FR)")
    for label, key in [
        ("DE", "YC/B.DE.EUR.4F.G_N_A.SV_C_YM.SR_10Y"),
        ("FR", "YC/B.FR.EUR.4F.G_N_A.SV_C_YM.SR_10Y"),
        ("EA aggregate", "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"),
    ]:
        try:
            url = f"https://data-api.ecb.europa.eu/service/data/{key}?format=csvdata&startPeriod=2023-01-01"
            r   = requests.get(url, timeout=15)
            st.write(f"**{label}** HTTP {r.status_code} — {len(r.text)} chars — `{r.text[:80]}`")
        except Exception as e:
            st.error(f"❌ ECB {label}: {e}")

    # ── 3. OECD API ───────────────────────────────────────────────────────────
    st.subheader("3. OECD API")
    for country in ["DEU","FRA","GBR","JPN"]:
        try:
            url = (f"https://sdmx.oecd.org/public/rest/data/"
                   f"OECD.SDD.STES,DSD_KEI@DF_KEI,4.0/"
                   f"{country}.M.IRLTLT01.ST?startPeriod=2023-01&format=csvfilewithlabels")
            r   = requests.get(url, timeout=15)
            st.write(f"**{country}** HTTP {r.status_code} — {len(r.text)} chars — `{r.text[:80]}`")
        except Exception as e:
            st.error(f"❌ OECD {country}: {e}")

    # ── 4. World Bank API ─────────────────────────────────────────────────────
    st.subheader("4. World Bank API")
    for code in ["GB","JP","DE","FR"]:
        try:
            url = f"https://api.worldbank.org/v2/country/{code}/indicator/FR.INR.LNGR?format=json&mrv=60"
            r   = requests.get(url, timeout=15)
            st.write(f"**{code}** HTTP {r.status_code} — {len(r.text)} chars — `{r.text[:80]}`")
        except Exception as e:
            st.error(f"❌ WorldBank {code}: {e}")

    # ── 5. Bank of England ────────────────────────────────────────────────────
    st.subheader("5. Bank of England API (GB)")
    try:
        url = ("https://www.bankofengland.co.uk/boeapps/database/_iadb-FromShowColumns.do"
               "?csv.x=yes&Datefrom=01/Jan/2020&Dateto=now&SeriesCodes=IUMSNPY&CSVF=TN&UsingCodes=Y")
        r   = requests.get(url, timeout=15)
        st.write(f"HTTP {r.status_code} — {len(r.text)} chars — `{r.text[:80]}`")
    except Exception as e:
        st.error(f"❌ BOE: {e}")

    # ── 6. ECB old endpoint ───────────────────────────────────────────────────
    st.subheader("6. ECB old endpoint")
    try:
        url = ("https://sdw-wsrest.ecb.europa.eu/service/data/"
               "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"
               "?format=csvdata&startPeriod=2023-01-01")
        r   = requests.get(url, timeout=15)
        st.write(f"HTTP {r.status_code} — {len(r.text)} chars — `{r.text[:80]}`")
    except Exception as e:
        st.error(f"❌ ECB old: {e}")

    st.divider()
    st.info("Share a screenshot of all results — any ✅ green = working source for the screener.")
