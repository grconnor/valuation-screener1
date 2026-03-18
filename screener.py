"""
Caberg Asset Management — Valuation Screener
=============================================
Pine v5 logic: front futures % change vs back futures % change,
rescaled to -100 → +100.

Data sources
  • yfinance  — CME futures, crypto, US/global equity indices
  • Multi-source bond yields — DE/FR/GB/JP 10Y government bond yields fetched
    from multiple providers with automatic fallback:
      1. yfinance Ticker().history()  (Reuters =RR tickers)
      2. ECB SDW REST API            (DE + FR)
      3. Bank of England API         (GB)
      4. Bank of Japan CSV           (JP)
      5. Stooq CSV                   (all four)
      6. FRED monthly → ffill        (last resort)

Timeframes: Daily · Weekly · Monthly
Install:  pip install -r requirements.txt
Run:      streamlit run screener.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from io import StringIO
from typing import Optional


# ─── LOGO (base64 embedded) ───────────────────────────────────────────────────
LOGO_B64 = "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"

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Caberg Valuation Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── STYLING ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&display=swap');
html,body,[class*="css"]          { font-family:'IBM Plex Mono',monospace; }
.stApp                            { background-color:#06060a; }
section[data-testid="stSidebar"] { background-color:#0b0b12; border-right:1px solid #1c1c2e; }
div[data-testid="stMetric"]      { background:#0f0f1a; border:1px solid #1c1c2e; border-radius:6px; padding:12px 16px; }
div[data-testid="stMetricLabel"] p { font-size:9px; letter-spacing:.12em; text-transform:uppercase; color:#555; }
div[data-testid="stMetricValue"] { font-size:1.3rem; font-weight:600; }
[data-testid="stDataFrame"] table   { font-family:'IBM Plex Mono',monospace !important; font-size:12px !important; }
[data-testid="stDataFrame"] thead th{ font-size:10px !important; letter-spacing:.1em; text-transform:uppercase; background-color:#0b0b12 !important; }
hr                               { border-color:#1c1c2e; margin:.6rem 0; }
h1,h2,h3                         { font-family:'IBM Plex Mono',monospace; font-weight:500; }
.stTabs [data-baseweb="tab"]     { font-family:'IBM Plex Mono',monospace; font-size:11px; }
</style>
""", unsafe_allow_html=True)


# ─── PAIR DEFINITIONS ─────────────────────────────────────────────────────────
# bond:{CC}  →  10Y gov bond yield fetched from multiple providers
PAIRS = [
    # FX
    ("AUDCAD",            "6A=F",     "6C=F",        "FX"),
    ("AUDCHF",            "6A=F",     "6S=F",        "FX"),
    ("AUDJPY",            "6A=F",     "6J=F",        "FX"),
    ("AUDNZD",            "6A=F",     "6N=F",        "FX"),
    ("AUDUSD",            "6A=F",     "DX=F",        "FX"),
    ("CADCHF",            "6C=F",     "6S=F",        "FX"),
    ("CADJPY",            "6C=F",     "6J=F",        "FX"),
    ("CHFJPY",            "6S=F",     "6J=F",        "FX"),
    ("EURAUD",            "6E=F",     "6A=F",        "FX"),
    ("EURCAD",            "6E=F",     "6C=F",        "FX"),
    ("EURCHF",            "6E=F",     "6S=F",        "FX"),
    ("EURGBP",            "6E=F",     "6B=F",        "FX"),
    ("EURJPY",            "6E=F",     "6J=F",        "FX"),
    ("EURNZD",            "6E=F",     "6N=F",        "FX"),
    ("EURUSD",            "6E=F",     "DX=F",        "FX"),
    ("GBPAUD",            "6B=F",     "6A=F",        "FX"),
    ("GBPCAD",            "6B=F",     "6C=F",        "FX"),
    ("GBPCHF",            "6B=F",     "6S=F",        "FX"),
    ("GBPJPY",            "6B=F",     "6J=F",        "FX"),
    ("GBPNZD",            "6B=F",     "6N=F",        "FX"),
    ("GBPUSD",            "6B=F",     "DX=F",        "FX"),
    ("NZDCAD",            "6N=F",     "6C=F",        "FX"),
    ("NZDCHF",            "6N=F",     "6S=F",        "FX"),
    ("NZDJPY",            "6N=F",     "6J=F",        "FX"),
    ("NZDUSD",            "6N=F",     "DX=F",        "FX"),
    ("USDCAD",            "DX=F",     "6C=F",        "FX"),
    ("USDCHF",            "DX=F",     "6S=F",        "FX"),
    ("USDJPY",            "DX=F",     "6J=F",        "FX"),
    ("USDMXN",            "DX=F",     "6M=F",        "FX"),
    ("USDZAR",            "DX=F",     "6Z=F",        "FX"),
    # Commodities vs Gold
    ("GOLD / DX",         "GC=F",     "DX=F",        "Commodities"),
    ("OIL / GOLD",        "CL=F",     "GC=F",        "Commodities"),
    ("NATGAS / GOLD",     "NG=F",     "GC=F",        "Commodities"),
    ("COPPER / GOLD",     "HG=F",     "GC=F",        "Commodities"),
    ("PALLADIUM / GOLD",  "PA=F",     "GC=F",        "Commodities"),
    ("PLATINUM / GOLD",   "PL=F",     "GC=F",        "Commodities"),
    ("SILVER / GOLD",     "SI=F",     "GC=F",        "Commodities"),
    ("COCOA / GOLD",      "CC=F",     "GC=F",        "Commodities"),
    ("COFFEE / GOLD",     "KC=F",     "GC=F",        "Commodities"),
    ("CATTLE / GOLD",     "LE=F",     "GC=F",        "Commodities"),
    ("SUGAR / GOLD",      "SB=F",     "GC=F",        "Commodities"),
    ("COTTON / GOLD",     "CT=F",     "GC=F",        "Commodities"),
    ("CORN / GOLD",       "ZC=F",     "GC=F",        "Commodities"),
    ("SOYBEAN / GOLD",    "ZS=F",     "GC=F",        "Commodities"),
    ("WHEAT / GOLD",      "ZW=F",     "GC=F",        "Commodities"),
    # Crypto
    ("BTC / DX",          "BTC=F",    "DX=F",        "Crypto"),
    ("ETH / DX",          "ETH=F",    "DX=F",        "Crypto"),
    # US Indices vs US Bonds
    ("SP500 / BONDS",     "ES=F",     "ZB=F",        "Indices vs Bonds"),
    ("NQ / BONDS",        "NQ=F",     "ZB=F",        "Indices vs Bonds"),
    ("RUSSELL / BONDS",   "RTY=F",    "ZB=F",        "Indices vs Bonds"),
    ("DOW / BONDS",       "YM=F",     "ZB=F",        "Indices vs Bonds"),
    # EU + Japan: index from Yahoo Finance, yield from bond: prefix
    ("CAC40 / FR10Y",     "^FCHI",    "bond:FR",     "Indices vs Bonds"),
    ("DAX / DE10Y",       "^GDAXI",   "bond:DE",     "Indices vs Bonds"),
    ("FTSE / UK10Y",      "^FTSE",    "bond:GB",     "Indices vs Bonds"),
    ("NIKKEI / JP10Y",    "^N225",    "bond:JP",     "Indices vs Bonds"),
]

GROUPS    = ["All"] + sorted(set(p[3] for p in PAIRS))
TIMEFRAMES = {
    "Daily":   "D",
    "Weekly":  "W",
    "Monthly": "ME",
}


# ─── SHARED HTTP SESSION ──────────────────────────────────────────────────────
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9"})

# Fetch log — accumulates messages during a run, displayed in the debug panel
_FETCH_LOG: list[tuple[str, str]] = []   # (level, message)

def _log(level: str, msg: str) -> None:
    _FETCH_LOG.append((level, msg))

def _http_get(url: str, timeout: int = 25, **kw) -> Optional[requests.Response]:
    try:
        r = _SESSION.get(url, timeout=timeout, **kw)
        if r.ok:
            return r
        _log("warn", f"  HTTP {r.status_code} ← {url[:80]}")
        return None
    except Exception as e:
        _log("warn", f"  Error: {e} ← {url[:80]}")
        return None


def _clean(s: Optional[pd.Series]) -> Optional[pd.Series]:
    """
    Normalise any price/yield series before use:
      - Ensure DatetimeIndex
      - Strip timezone (tz-aware → tz-naive) so tz-aware yfinance series
        and tz-naive Stooq/FRED series can be safely joined.
      - Normalise to date-only (removes time-of-day mismatches).
      - Sort, deduplicate, drop NaN.
    """
    if s is None or s.empty:
        return None
    try:
        if not isinstance(s.index, pd.DatetimeIndex):
            s.index = pd.to_datetime(s.index, errors="coerce")
        if s.index.tz is not None:
            s = s.tz_convert("UTC").tz_localize(None)
        s.index = s.index.normalize()
        s = s[~s.index.duplicated(keep="last")]
        s = s.sort_index().dropna()
        return s if len(s) >= 5 else None
    except Exception:
        return s


# ─── YAHOO FINANCE ────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def _yf_fetch(ticker: str) -> Optional[pd.Series]:
    """
    Fetch max daily history from Yahoo Finance.
    Tries yf.Ticker().history() first (handles =RR yield tickers better),
    then falls back to yf.download().
    """
    # Method 1: Ticker.history — better for non-standard tickers
    try:
        tk  = yf.Ticker(ticker)
        df  = tk.history(period="max", auto_adjust=True)
        if df is not None and not df.empty and "Close" in df.columns:
            s = _clean(df["Close"].dropna())
            if s is not None and len(s) >= 20:
                _log("ok", f"  yf.Ticker OK  {ticker}  ({len(s)} bars)")
                return s
    except Exception as e:
        _log("warn", f"  yf.Ticker fail {ticker}: {e}")

    # Method 2: yf.download — standard bulk fetch
    try:
        df = yf.download(
            ticker, period="max", interval="1d",
            auto_adjust=True, progress=False, repair=False,
        )
        if df is not None and not df.empty:
            c = df["Close"].iloc[:, 0] if isinstance(df.columns, pd.MultiIndex) else df["Close"]
            s = _clean(c.dropna())
            if s is not None and len(s) >= 20:
                _log("ok", f"  yf.download OK {ticker}  ({len(s)} bars)")
                return s
    except Exception as e:
        _log("warn", f"  yf.download fail {ticker}: {e}")

    _log("fail", f"  yf FAILED for {ticker}")
    return None


# ─── BOND YIELD SOURCES ───────────────────────────────────────────────────────
# Each returns a daily pd.Series of the 10Y government bond yield, or None.

def _parse_date_value(df: pd.DataFrame) -> Optional[pd.Series]:
    """Find date + numeric value columns, return clean sorted series."""
    try:
        # Identify date column (first col that parses as dates)
        date_col, val_col = None, None
        for col in df.columns:
            try:
                pd.to_datetime(df[col].dropna().iloc[:3])
                date_col = col
                break
            except Exception:
                pass
        if date_col is None:
            date_col = df.columns[0]
        # Value column: first numeric col that isn't the date col
        for col in df.columns:
            if col == date_col:
                continue
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) > 10:
                val_col = col
                break
        if val_col is None:
            return None
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df[val_col]  = pd.to_numeric(df[val_col],   errors="coerce")
        s = (df.dropna(subset=[date_col, val_col])
               .set_index(date_col)[val_col]
               .sort_index()
               .dropna())
        return s if len(s) >= 20 else None
    except Exception:
        return None


# ── 0. pandas_datareader → Stooq (most reliable Stooq client) ───────────────

def _pdr_stooq(sym: str) -> Optional[pd.Series]:
    """
    Fetch bond yield series from Stooq via pandas_datareader.
    pandas_datareader handles Stooq's session/cookie requirements automatically.
    Symbols: 10gb.b  10jp.b  10de.b  10fr.b
    """
    try:
        import pandas_datareader.data as pdr
        start = datetime(2000, 1, 1)
        end   = datetime.now()
        _log("info", f"  pdr.stooq → {sym}")
        df = pdr.DataReader(sym, "stooq", start=start, end=end)
        if df is None or df.empty:
            _log("fail", f"  pdr.stooq empty for {sym}")
            return None
        s = df["Close"].sort_index().dropna()
        if len(s) >= 20:
            _log("ok", f"  pdr.stooq OK {sym}: {len(s)} bars")
            return _clean(s)
        _log("fail", f"  pdr.stooq too few bars: {len(s)}")
    except ImportError:
        _log("warn", "  pandas_datareader not installed — run: pip install pandas-datareader")
    except Exception as e:
        _log("warn", f"  pdr.stooq error {sym}: {e}")
    return None


# ── 1. Yahoo Finance yield tickers ──────────────────────────────────────────

def _yf_yield(country: str) -> Optional[pd.Series]:
    """
    Try Yahoo Finance yield tickers. ^TNGB / ^TNJP are Yahoo's native
    10Y index yield series — most reliable. =RR Reuters tickers are tried next.
    """
    tickers = {
        "DE": ["DE10YT=RR", "DEAT10Y=RR", "^TNDE"],
        "FR": ["FR10YT=RR", "FRAT10Y=RR", "^TNFR"],
        "GB": ["^TNGB",     "GB10YT=RR",  "GBGV10YT=RR", "GBAT10Y=RR"],
        "JP": ["^TNJP",     "JP10YT=RR",  "JPGV10YT=RR", "JPAT10Y=RR"],
    }.get(country, [])

    for tk in tickers:
        s = _yf_fetch(tk)
        if s is not None:
            _log("ok", f"  YF yield OK: {tk} for {country}")
            return s
        _log("warn", f"  YF yield miss: {tk}")
    return None


# ── 2. ECB SDW REST API (Germany + France) ───────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def _ecb_yield(country: str) -> Optional[pd.Series]:
    """ECB Statistics Data Warehouse — DE/FR 10Y par yield curve."""
    if country not in ("DE", "FR"):
        return None

    base = "https://data-api.ecb.europa.eu/service/data"
    keys = [
        f"YC/B.{country}.EUR.4F.G_N_A.SV_C_YM.SR_10Y",
        "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y",
    ]
    for key in keys:
        url = f"{base}/{key}?format=csvdata&startPeriod=2000-01-01"
        _log("info", f"  ECB → {url[:90]}")
        r = _http_get(url)
        if r is None:
            continue
        text = r.text.strip()
        if not text or len(text) < 100:
            continue
        try:
            df = pd.read_csv(StringIO(text))
            tc = next((c for c in df.columns if "TIME" in c.upper()), df.columns[0])
            vc = next((c for c in df.columns if "OBS_VALUE" in c.upper()), None)
            if vc is None:
                for col in reversed(df.columns):
                    if pd.to_numeric(df[col], errors="coerce").notna().sum() > 10:
                        vc = col
                        break
            if vc is None:
                continue
            df[tc] = pd.to_datetime(df[tc], errors="coerce")
            df[vc] = pd.to_numeric(df[vc], errors="coerce")
            s = df.dropna(subset=[tc, vc]).set_index(tc)[vc].sort_index().dropna()
            if len(s) >= 20:
                _log("ok", f"  ECB OK for {country}: {len(s)} bars")
                return _clean(s)
        except Exception as e:
            _log("warn", f"  ECB parse error: {e}")

    _log("fail", f"  ECB FAILED for {country}")
    return None


# ── 3. Bank of England (UK) ──────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def _boe_yield() -> Optional[pd.Series]:
    """UK 10Y nominal par gilt yield from Bank of England. Series: IUMSNPY."""
    today = datetime.now().strftime("%d/%b/%Y")
    urls = [
        (
            "https://www.bankofengland.co.uk/boeapps/database/_iadb-FromShowColumns.do"
            f"?csv.x=yes&Datefrom=02/Jan/2000&Dateto={today}"
            "&SeriesCodes=IUMSNPY&CSVF=TN&UsingCodes=Y"
        ),
        (
            "https://www.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp"
            "?Travel=NIxRSxSUx&FromSeries=1&ToSeries=50&DAT=ALL"
            "&CSVF=TN&html.x=66&html.y=26&SeriesCodes=IUMSNPY&Filter=N"
        ),
    ]
    for i, url in enumerate(urls):
        _log("info", f"  BOE url{i+1} → {url[:80]}")
        r = _http_get(url, timeout=35)
        if r is None:
            _log("fail", f"  BOE url{i+1} no response"); continue
        text = r.text.strip()
        _log("info", f"  BOE url{i+1}: {len(text)} chars  {repr(text[:60])}")
        if len(text) < 100 or "<html" in text.lower():
            _log("fail", f"  BOE url{i+1} returned HTML/empty"); continue
        try:
            df = pd.read_csv(StringIO(text))
            df.columns = [str(c).strip().strip('"') for c in df.columns]
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], dayfirst=True, errors="coerce")
            df.iloc[:, 1] = pd.to_numeric(df.iloc[:, 1], errors="coerce")
            s = (df.dropna(subset=[df.columns[0], df.columns[1]])
                   .set_index(df.columns[0])[df.columns[1]].sort_index())
            if len(s) >= 20:
                _log("ok", f"  BOE url{i+1} OK: {len(s)} bars")
                return _clean(s)
            _log("warn", f"  BOE url{i+1} only {len(s)} rows")
        except Exception as e:
            _log("warn", f"  BOE url{i+1} parse error: {e}")
    _log("fail", "  BOE ALL URLS FAILED")
    return None


# ── 4. Bank of Japan / Ministry of Finance Japan (JP) ───────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def _boj_yield() -> Optional[pd.Series]:
    """Japan 10Y JGB yield from Ministry of Finance Japan CSV."""
    urls = [
        "https://www.mof.go.jp/jgbs/reference/interest_rate/historical/jgbcm_all.csv",
        "https://www.mof.go.jp/jgbs/reference/interest_rate/jgbcm.csv",
    ]
    for mof_url in urls:
        _log("info", f"  MOF → {mof_url}")
        r = _http_get(mof_url, timeout=35)
        if r is None:
            _log("fail", "  MOF no response"); continue
        for enc in ("shift_jis", "utf-8", "cp932", "latin-1"):
            try:
                text = r.content.decode(enc)
                lines = [l for l in text.splitlines()
                         if l.strip() and not l.startswith("#") and not l.startswith('"#')]
                if len(lines) < 5: continue
                df = pd.read_csv(StringIO("\n".join(lines)), header=0)
                df.columns = [str(c).strip() for c in df.columns]
                date_col = df.columns[0]
                ten_yr = next(
                    (c for c in df.columns[1:]
                     if str(c).strip() in ("10年", "10Y", "10", "10年物", "10-Year")),
                    df.columns[10] if len(df.columns) > 10 else None
                )
                if ten_yr is None:
                    _log("warn", f"  MOF no 10Y col. Cols: {df.columns.tolist()[:15]}"); continue
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                df[ten_yr]   = pd.to_numeric(df[ten_yr], errors="coerce")
                s = (df.dropna(subset=[date_col, ten_yr])
                       .set_index(date_col)[ten_yr].sort_index().dropna())
                if len(s) >= 20:
                    _log("ok", f"  MOF OK ({enc}): {len(s)} bars, col='{ten_yr}'")
                    return _clean(s)
                _log("warn", f"  MOF only {len(s)} rows (enc={enc})")
            except Exception as e:
                _log("warn", f"  MOF enc={enc}: {e}"); continue
    _log("fail", "  MOF Japan ALL FAILED")
    return None


# ── 5. Stooq CSV (all four countries) ────────────────────────────────────────

def _stooq_yield(sym: str) -> Optional[pd.Series]:
    """
    Stooq.com free CSV API for bond yields.
    Warms up the session cookie first to avoid 403/empty responses.
    Symbols: 10de.b  10fr.b  10gb.b  10jp.b
    """
    # Cookie warm-up — Stooq requires the quote page to set cookies before CSV download
    try:
        _SESSION.get("https://stooq.com/", timeout=8)
        _SESSION.get(f"https://stooq.com/q/?s={sym}", timeout=8)
    except Exception:
        pass

    end   = datetime.now()
    start = end - timedelta(days=365 * 20)
    url   = (
        f"https://stooq.com/q/d/l/?s={sym}&i=d"
        f"&d1={start.strftime('%Y%m%d')}&d2={end.strftime('%Y%m%d')}"
    )
    _log("info", f"  Stooq → {url[:90]}")
    r = _http_get(url, timeout=25)
    if r is None:
        _log("fail", f"  Stooq HTTP failed for {sym}")
        return None

    text = r.text.strip()
    if not text or "No data" in text or "<html" in text.lower() or len(text) < 50:
        _log("fail", f"  Stooq bad response for {sym}: {repr(text[:80])}")
        return None

    try:
        df = pd.read_csv(StringIO(text), parse_dates=["Date"])
        if "Close" not in df.columns or df.empty:
            _log("fail", f"  Stooq bad cols for {sym}: {df.columns.tolist()}")
            return None
        s = df.sort_values("Date").set_index("Date")["Close"].dropna()
        if len(s) >= 20:
            _log("ok", f"  Stooq OK {sym}: {len(s)} bars")
            return _clean(s)
    except Exception as e:
        _log("warn", f"  Stooq parse error {sym}: {e}")

    _log("fail", f"  Stooq FAILED for {sym}")
    return None


# ── 6. FRED monthly → forward-filled (last resort) ───────────────────────────

def _fred_monthly_ffill(series_id: str) -> Optional[pd.Series]:
    """
    FRED monthly series, forward-filled to daily.
    FRED uses '.' for missing values — we coerce to NaN then drop.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    _log("info", f"  FRED → {url}")
    r = _http_get(url, timeout=25)
    if r is None:
        _log("fail", f"  FRED no response for {series_id}")
        return None
    text = r.text.strip()
    if not text or len(text) < 30:
        _log("fail", f"  FRED empty for {series_id}")
        return None
    _log("info", f"  FRED response ({len(text)} chars): {text[:60]}")
    try:
        df = pd.read_csv(StringIO(text))
        if df.shape[1] < 2:
            _log("fail", f"  FRED bad columns: {df.columns.tolist()}")
            return None
        df.columns = ["Date", "Value"]
        df["Date"]  = pd.to_datetime(df["Date"],  errors="coerce")
        df["Value"] = pd.to_numeric(df["Value"],  errors="coerce")   # '.' → NaN
        df = df.dropna().set_index("Date").sort_index()
        if df.empty:
            _log("fail", f"  FRED no valid rows after cleaning for {series_id}")
            return None
        # Forward-fill monthly data to daily
        idx = pd.date_range(df.index[0], pd.Timestamp.now(), freq="D")
        s   = df["Value"].reindex(idx).ffill().dropna()
        if len(s) >= 20:
            _log("ok", f"  FRED OK {series_id}: {len(s)} days (monthly ffilled)")
            return _clean(s)
        _log("fail", f"  FRED too few rows after ffill: {len(s)}")
    except Exception as e:
        _log("warn", f"  FRED parse error {series_id}: {e}")
    return None


# ── STANDALONE FRED FETCH — fresh connection, no shared session ───────────────
# This is deliberately separate from _SESSION and all other fetch functions.
# Used as the guaranteed first source for GB and JP on Streamlit Cloud.

def _fred_fresh(series_id: str) -> Optional[pd.Series]:
    """
    Fetch a FRED monthly series using a completely fresh requests.get call.
    No shared session, no cookies from other requests, no side effects.
    Forward-fills monthly data to daily.
    Always works from any IP including cloud providers.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    _log("info", f"  FRED-fresh → {series_id}")
    try:
        r = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/csv,text/plain,*/*",
            }
        )
        if not r.ok:
            _log("fail", f"  FRED-fresh HTTP {r.status_code} for {series_id}")
            return None

        text = r.text.strip()
        _log("info", f"  FRED-fresh got {len(text)} chars: {text[:60]}")

        if not text or len(text) < 30:
            _log("fail", f"  FRED-fresh empty response")
            return None

        df = pd.read_csv(StringIO(text))
        if df.shape[1] < 2:
            _log("fail", f"  FRED-fresh bad shape: {df.shape}")
            return None

        df.columns    = ["Date", "Value"]
        df["Date"]    = pd.to_datetime(df["Date"],  errors="coerce")
        df["Value"]   = pd.to_numeric(df["Value"],  errors="coerce")
        df = df.dropna().set_index("Date").sort_index()

        if df.empty:
            _log("fail", f"  FRED-fresh no valid rows for {series_id}")
            return None

        # Forward-fill monthly → daily
        idx = pd.date_range(df.index[0], pd.Timestamp.now(), freq="D")
        s   = df["Value"].reindex(idx).ffill().dropna()

        if len(s) >= 20:
            _log("ok", f"  FRED-fresh OK {series_id}: {len(s)} daily rows")
            return _clean(s)

        _log("fail", f"  FRED-fresh too few rows: {len(s)}")
        return None

    except Exception as e:
        _log("fail", f"  FRED-fresh exception for {series_id}: {e}")
        return None


# ── 6a. FRED via pandas_datareader (daily-interpolated monthly) ──────────────

def _pdr_fred(series_id: str) -> Optional[pd.Series]:
    """
    Fetch a FRED series via pandas_datareader and forward-fill to daily.
    More reliable than direct HTTP to FRED (handles retries, parsing).
    GB: IRLTLT01GBM156N   JP: IRLTLT01JPM156N
    """
    try:
        import pandas_datareader.data as pdr
        _log("info", f"  pdr.fred → {series_id}")
        start = datetime(2000, 1, 1)
        df = pdr.DataReader(series_id, "fred", start=start)
        if df is None or df.empty:
            _log("fail", f"  pdr.fred empty for {series_id}")
            return None
        s = df.iloc[:, 0].dropna()
        if s.empty:
            return None
        # Forward-fill monthly to daily
        idx = pd.date_range(s.index[0], pd.Timestamp.now(), freq="D")
        s   = s.reindex(idx).ffill().dropna()
        if len(s) >= 20:
            _log("ok", f"  pdr.fred OK {series_id}: {len(s)} daily rows (monthly ffilled)")
            return _clean(s)
    except ImportError:
        _log("warn", "  pandas_datareader not installed")
    except Exception as e:
        _log("warn", f"  pdr.fred error {series_id}: {e}")
    return None


# ── Dedicated cached fetchers for GB and JP — bypass all shared state ─────────
# These are the only functions used for bond:GB and bond:JP.
# Completely isolated — own requests.get, own cache, no shared session.

@st.cache_data(ttl=3600, show_spinner=False)
def _uk10y_daily() -> Optional[pd.Series]:
    """UK 10Y gilt yield — FRED IRLTLT01GBM156N — fresh isolated fetch."""
    return _fred_fresh("IRLTLT01GBM156N")


@st.cache_data(ttl=3600, show_spinner=False)
def _jp10y_daily() -> Optional[pd.Series]:
    """Japan 10Y JGB yield — FRED IRLTLT01JPM156N — fresh isolated fetch."""
    return _fred_fresh("IRLTLT01JPM156N")


# ── Master bond yield dispatcher ──────────────────────────────────────────────

# Country → (stooq_sym, fred_series)
_BOND_CONFIG = {
    "DE": ("10de.b", "IRLTLT01DEM156N"),
    "FR": ("10fr.b", "IRLTLT01FRM156N"),
    "GB": ("10gb.b", "IRLTLT01GBM156N"),
    "JP": ("10jp.b", "IRLTLT01JPM156N"),
}

@st.cache_data(ttl=3600, show_spinner=False)
def _bond_yield_daily(country: str) -> Optional[pd.Series]:
    """
    Fetch 10Y government bond yield.

    Source order is optimised for Streamlit Cloud where many APIs
    block cloud-provider IPs:
      - FRED (via pdr) always works from any IP — used first for GB + JP
      - Yahoo Finance ^TN tickers work reliably from cloud
      - ECB API works from cloud for DE + FR
      - BOE / MOF Japan sometimes block cloud IPs — tried but not relied on
    """
    stooq_sym, fred_id = _BOND_CONFIG.get(country, (None, None))
    _log("info", f"─── bond:{country} ───")

    # ── GB and JP: fresh FRED call first — guaranteed from any IP ────────────
    if country in ("GB", "JP"):

        # 1. FRED fresh HTTP (standalone, no shared session — always works)
        if fred_id:
            s = _fred_fresh(fred_id)
            if s is not None:
                return s

        # 2. FRED via pandas_datareader
        if fred_id:
            s = _pdr_fred(fred_id)
            if s is not None:
                return s

        # 3. Yahoo Finance ^TNGB / ^TNJP
        s = _yf_yield(country)
        if s is not None:
            return s

        # 4. FRED via _http_get (shared session — last HTTP attempt)
        if fred_id:
            s = _fred_monthly_ffill(fred_id)
            if s is not None:
                return s

        # 5. pandas_datareader → Stooq
        if stooq_sym:
            s = _pdr_stooq(stooq_sym)
            if s is not None:
                return s

        # 6. Bank of England / MOF Japan
        if country == "GB":
            s = _boe_yield()
            if s is not None:
                return s
        if country == "JP":
            s = _boj_yield()
            if s is not None:
                return s

        # 7. Stooq manual HTTP
        if stooq_sym:
            s = _stooq_yield(stooq_sym)
            if s is not None:
                return s

        _log("fail", f"ALL SOURCES FAILED for bond:{country}")
        return None

    # ── DE and FR: ECB API works well from cloud ──────────────────────────────
    # 1. pandas_datareader → Stooq
    if stooq_sym:
        s = _pdr_stooq(stooq_sym)
        if s is not None:
            return s

    # 2. Yahoo Finance
    s = _yf_yield(country)
    if s is not None:
        return s

    # 3. ECB SDW API
    if country in ("DE", "FR"):
        s = _ecb_yield(country)
        if s is not None:
            return s

    # 4. Stooq manual HTTP
    if stooq_sym:
        s = _stooq_yield(stooq_sym)
        if s is not None:
            return s

    # 5. FRED via pdr
    if fred_id:
        s = _pdr_fred(fred_id)
        if s is not None:
            return s

    # 6. FRED direct HTTP
    if fred_id:
        s = _fred_monthly_ffill(fred_id)
        if s is not None:
            return s

    _log("fail", f"ALL SOURCES FAILED for bond:{country}")
    return None


# ─── DATA ROUTING ─────────────────────────────────────────────────────────────

def _resample(s: pd.Series, rule: str) -> pd.Series:
    s = _clean(s)
    if s is None:
        return pd.Series(dtype=float)
    try:
        return s.resample(rule).last().dropna()
    except Exception:
        try:
            return s.resample("M" if rule == "ME" else rule).last().dropna()
        except Exception:
            return pd.Series(dtype=float)


def get_series(ticker: str, tf: str) -> Optional[pd.Series]:
    """Return price/yield series resampled to the requested timeframe."""
    rule = TIMEFRAMES[tf]

    if ticker == "bond:GB":
        # Dedicated isolated fetcher — bypasses all shared session state
        daily = _uk10y_daily()
    elif ticker == "bond:JP":
        # Dedicated isolated fetcher — bypasses all shared session state
        daily = _jp10y_daily()
    elif ticker.startswith("bond:"):
        daily = _bond_yield_daily(ticker[5:])
    else:
        daily = _yf_fetch(ticker)

    if daily is None:
        return None

    daily = _clean(daily)
    if daily is None:
        return None

    result = _resample(daily, rule) if rule != "D" else daily
    if result is None or result.empty:
        return None
    return result


# ─── PINE V5 VALUATION ────────────────────────────────────────────────────────

def calc_valuation(front: pd.Series, back: pd.Series,
                   length: int, rescale_len: int) -> pd.Series:
    # Strip tz from both sides — last line of defence against tz mismatch
    front = _clean(front)
    back  = _clean(back)
    if front is None or back is None:
        return pd.Series(dtype=float)
    df = pd.DataFrame({"f": front, "b": back}).dropna()
    if len(df) < length + rescale_len + 5:
        return pd.Series(dtype=float)
    diff     = df["f"].pct_change(length) * 100 - df["b"].pct_change(length) * 100
    roll_max = diff.rolling(rescale_len).max()
    roll_min = diff.rolling(rescale_len).min()
    rng      = (roll_max - roll_min).replace(0, np.nan)
    return (diff - roll_min) / rng * 200 - 100


def latest_score(f, b, length, rescale_len) -> float:
    if f is None or b is None:
        return np.nan
    v = calc_valuation(f, b, length, rescale_len).dropna()
    return round(float(v.iloc[-1]), 1) if not v.empty else np.nan


def signal_for(score: float, threshold: int) -> str:
    if np.isnan(score):       return "No data"
    if score >=  threshold:   return "Overvalued"
    if score <= -threshold:   return "Undervalued"
    return "Neutral"


# ─── CHART ────────────────────────────────────────────────────────────────────

def _zone_color(v: float, thr: int) -> str:
    if np.isnan(v):   return "#555"
    if v >=  thr:     return "#E84040"
    if v <= -thr:     return "#0EB87A"
    return "#F0A500"


def _zone_fill(v: float, thr: int) -> str:
    if np.isnan(v):   return "rgba(85,85,85,0)"
    if v >=  thr:     return "rgba(232,64,64,0.14)"
    if v <= -thr:     return "rgba(14,184,122,0.14)"
    return "rgba(240,165,0,0.09)"


def build_chart(name, front_t, back_t, front, back, length, rescale_len, threshold, tf):
    val = calc_valuation(front, back, length, rescale_len)
    if val.empty:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data — reduce Period or Rescale.",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#666", size=13, family="IBM Plex Mono"))
        fig.update_layout(paper_bgcolor="#06060a", plot_bgcolor="#0c0c14",
                          height=320, margin=dict(l=20, r=20, t=20, b=20))
        return fig

    df = pd.DataFrame({"f": front, "b": back}).dropna()
    fp = df["f"].pct_change(length) * 100
    bp = df["b"].pct_change(length) * 100

    fig = make_subplots(rows=2, cols=1, row_heights=[0.68, 0.32],
                        shared_xaxes=True, vertical_spacing=0.04)

    # Zone shading + reference lines
    fig.add_hrect(y0=threshold,  y1=108,  fillcolor="rgba(232,64,64,0.06)",  line_width=0, row=1, col=1)
    fig.add_hrect(y0=-108, y1=-threshold, fillcolor="rgba(14,184,122,0.06)", line_width=0, row=1, col=1)
    fig.add_hline(y= threshold, line_dash="dash", line_color="rgba(232,64,64,0.45)",   line_width=1, row=1, col=1)
    fig.add_hline(y=-threshold, line_dash="dash", line_color="rgba(14,184,122,0.45)",  line_width=1, row=1, col=1)
    fig.add_hline(y=0,          line_dash="dot",  line_color="rgba(255,255,255,0.10)", line_width=1, row=1, col=1)

    # Coloured line segments + fill to zero
    xs, ys = val.index.tolist(), val.values.tolist()
    seg_x, seg_y = [xs[0]], [ys[0]]
    seg_c, seg_f = _zone_color(ys[0], threshold), _zone_fill(ys[0], threshold)

    def _flush(sx, sy, sc, sf):
        if len(sx) < 2: return
        fig.add_trace(go.Scatter(x=sx, y=sy, mode="none", fill="tozeroy",
            fillcolor=sf, showlegend=False, hoverinfo="skip"), row=1, col=1)
        fig.add_trace(go.Scatter(x=sx, y=sy, mode="lines",
            line=dict(color=sc, width=2), showlegend=False,
            hovertemplate="%{x|%Y-%m-%d}  Score: <b>%{y:.1f}</b><extra></extra>"), row=1, col=1)

    for i in range(1, len(ys)):
        c = _zone_color(ys[i], threshold)
        f = _zone_fill(ys[i], threshold)
        if c == seg_c:
            seg_x.append(xs[i]); seg_y.append(ys[i])
        else:
            seg_x.append(xs[i]); seg_y.append(ys[i])
            _flush(seg_x, seg_y, seg_c, seg_f)
            seg_x, seg_y, seg_c, seg_f = [xs[i]], [ys[i]], c, f
    _flush(seg_x, seg_y, seg_c, seg_f)

    # Current value annotation
    lv = val.dropna().iloc[-1]; ld = val.dropna().index[-1]
    fig.add_annotation(x=ld, y=lv, text=f"  {lv:+.1f}  {signal_for(lv, threshold)}",
        showarrow=False, xanchor="left",
        font=dict(color=_zone_color(lv, threshold), size=12, family="IBM Plex Mono"), row=1, col=1)
    x0 = val.index[0]
    fig.add_annotation(x=x0, y=threshold+3, text=f"  +{threshold}  Overvalued",
        showarrow=False, xanchor="left",
        font=dict(color="rgba(232,64,64,0.50)", size=10, family="IBM Plex Mono"), row=1, col=1)
    fig.add_annotation(x=x0, y=-threshold-3, text=f"  -{threshold}  Undervalued",
        showarrow=False, xanchor="left", yanchor="top",
        font=dict(color="rgba(14,184,122,0.50)", size=10, family="IBM Plex Mono"), row=1, col=1)

    # % change panel
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.07)", line_width=1, row=2, col=1)
    fig.add_trace(go.Scatter(x=fp.index, y=fp.values, mode="lines",
        name=f"Front  {front_t}", line=dict(color="#4D9EE8", width=1.2),
        hovertemplate="%{x|%Y-%m-%d}  <b>%{y:.3f}%</b><extra></extra>"), row=2, col=1)
    fig.add_trace(go.Scatter(x=bp.index, y=bp.values, mode="lines",
        name=f"Back  {back_t}", line=dict(color="#B06AD4", width=1.2),
        hovertemplate="%{x|%Y-%m-%d}  <b>%{y:.3f}%</b><extra></extra>"), row=2, col=1)

    ax = dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", zeroline=False,
              tickfont=dict(size=10, family="IBM Plex Mono"),
              linecolor="rgba(255,255,255,0.07)")
    fig.update_layout(
        height=580, paper_bgcolor="#06060a", plot_bgcolor="#0c0c14",
        font=dict(color="#7777aa", family="IBM Plex Mono"),
        margin=dict(l=64, r=60, t=28, b=36),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0f0f1a", bordercolor="#2a2a3e",
                        font=dict(family="IBM Plex Mono", size=11)),
        legend=dict(orientation="h", x=0, y=-0.06, font=dict(size=10),
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(**ax), xaxis2=dict(**ax),
        yaxis=dict(**ax, title="Score", range=[-108, 108],
                   tickvals=[-100, -threshold, 0, threshold, 100]),
        yaxis2=dict(**ax, title=f"% chg ({length}b)"),
    )
    return fig


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():

    # ── Sidebar ──────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            f'''<div style="text-align:center;padding:10px 0 6px">
            <img src="data:image/png;base64,{LOGO_B64}"
                 style="width:110px;height:110px;object-fit:contain;border-radius:8px"/>
            </div>
            <div style="text-align:center;font-family:IBM Plex Mono,monospace;
                        font-size:13px;font-weight:600;letter-spacing:.1em;
                        color:#C9A84C;margin-top:4px">CABERG</div>
            <div style="text-align:center;font-family:IBM Plex Mono,monospace;
                        font-size:9px;letter-spacing:.18em;color:#555;
                        text-transform:uppercase;margin-bottom:4px">Asset Management</div>''',
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown(
            '<div style="font-family:IBM Plex Mono,monospace;font-size:10px;'
            'letter-spacing:.12em;color:#7777aa;text-transform:uppercase">'
            'Valuation Screener · Pine v5</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        length      = st.number_input("Period (Length)",      min_value=1,  max_value=200, value=10,  step=1)
        rescale_len = st.number_input("Rescale Length",       min_value=20, max_value=500, value=100, step=10)
        threshold   = st.number_input("Signal Threshold (±)", min_value=10, max_value=99,  value=75,  step=5)
        st.divider()

        group_filter  = st.selectbox("Group", GROUPS)
        signal_filter = st.multiselect("Signal filter",
            ["Overvalued", "Neutral", "Undervalued", "No data"],
            default=["Overvalued", "Neutral", "Undervalued", "No data"])
        st.divider()

        if st.button("↺  Refresh data", use_container_width=True):
            st.cache_data.clear()
            _FETCH_LOG.clear()
            st.rerun()

        st.caption(f"Updated: {datetime.utcnow().strftime('%H:%M UTC')}")

    # ── Fetch all tickers ─────────────────────────────────
    _FETCH_LOG.clear()
    unique = list(set(t for _, f, b, _ in PAIRS for t in [f, b]))

    with st.spinner("Fetching data…"):
        bar = st.progress(0, text="")
        for i, tk in enumerate(unique):
            if tk.startswith("bond:"):
                _bond_yield_daily(tk[5:])
            else:
                _yf_fetch(tk)
            bar.progress((i + 1) / len(unique), text=tk)
        bar.empty()

    # ── Compute scores ────────────────────────────────────
    rows = []
    for name, ft, bt, grp in PAIRS:
        d_score = latest_score(get_series(ft,"Daily"),   get_series(bt,"Daily"),   length, rescale_len)
        w_score = latest_score(get_series(ft,"Weekly"),  get_series(bt,"Weekly"),  length, rescale_len)
        m_score = latest_score(get_series(ft,"Monthly"), get_series(bt,"Monthly"), length, rescale_len)
        rows.append({
            "Pair":      name,    "Group":  grp,
            "Front":     ft,      "Back":   bt,
            "Daily":     d_score, "D Sig":  signal_for(d_score, threshold),
            "Weekly":    w_score, "W Sig":  signal_for(w_score, threshold),
            "Monthly":   m_score, "M Sig":  signal_for(m_score, threshold),
        })

    df_all = pd.DataFrame(rows)

    # ── Filter ────────────────────────────────────────────
    df_v = df_all.copy()
    if group_filter != "All":
        df_v = df_v[df_v["Group"] == group_filter]
    if signal_filter:
        df_v = df_v[df_v["D Sig"].isin(signal_filter) |
                    df_v["W Sig"].isin(signal_filter) |
                    df_v["M Sig"].isin(signal_filter)]
    df_v = df_v.reset_index(drop=True)

    # ── Header + metrics ──────────────────────────────────
    st.markdown(
        f'''<div style="display:flex;align-items:center;gap:14px;margin-bottom:4px">
        <img src="data:image/png;base64,{LOGO_B64}"
             style="width:42px;height:42px;object-fit:contain;border-radius:6px"/>
        <div>
          <div style="font-family:IBM Plex Mono,monospace;font-size:18px;
                      font-weight:600;letter-spacing:.06em;color:#C9A84C">CABERG</div>
          <div style="font-family:IBM Plex Mono,monospace;font-size:10px;
                      letter-spacing:.14em;color:#555;text-transform:uppercase">
               Asset Management · Valuation Screener</div>
        </div></div>''',
        unsafe_allow_html=True,
    )
    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    c1.metric("Loaded",       int((df_all["D Sig"] != "No data").sum()))
    c2.metric("D — Over",     int((df_all["D Sig"] == "Overvalued").sum()))
    c3.metric("D — Under",    int((df_all["D Sig"] == "Undervalued").sum()))
    c4.metric("W — Over",     int((df_all["W Sig"] == "Overvalued").sum()))
    c5.metric("W — Under",    int((df_all["W Sig"] == "Undervalued").sum()))
    c6.metric("M — Over",     int((df_all["M Sig"] == "Overvalued").sum()))
    c7.metric("M — Under",    int((df_all["M Sig"] == "Undervalued").sum()))
    st.divider()

    # ── Debug fetch log ───────────────────────────────────
    with st.expander("🔍 Data fetch log (expand to diagnose missing pairs)", expanded=False):
        level_colors = {"ok": "🟢", "fail": "🔴", "warn": "🟡", "info": "⚪"}
        for level, msg in _FETCH_LOG:
            st.text(f"{level_colors.get(level, '⚪')} {msg}")

    # ── Table ─────────────────────────────────────────────
    st.caption(f"Showing {len(df_v)} pairs  ·  Click a row to open the valuation chart")

    def style_row(row):
        stls = [""] * len(row)
        cols = row.index.tolist()
        def clr(sig):
            return {"Overvalued":"color:#E84040;font-weight:600",
                    "Undervalued":"color:#0EB87A;font-weight:600",
                    "Neutral":"color:#F0A500"}.get(sig, "color:#3a3a4a")
        for sc, sg in [("Daily","D Sig"),("Weekly","W Sig"),("Monthly","M Sig")]:
            if sc in cols and sg in cols:
                c = clr(row[sg])
                stls[cols.index(sc)] = c
                stls[cols.index(sg)] = c
        return stls

    def fmt(v): return f"{v:+.1f}" if not np.isnan(v) else "—"

    styled = (df_v.style
              .apply(style_row, axis=1)
              .format({"Daily": fmt, "Weekly": fmt, "Monthly": fmt}))

    event = st.dataframe(
        styled, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row",
        height=min(40 * len(df_v) + 50, 640),
        column_config={
            "Pair":    st.column_config.TextColumn("Pair",    width=155),
            "Group":   st.column_config.TextColumn("Group",   width=130),
            "Front":   st.column_config.TextColumn("Front",   width=95),
            "Back":    st.column_config.TextColumn("Back",    width=95),
            "Daily":   st.column_config.NumberColumn("Daily", width=68),
            "D Sig":   st.column_config.TextColumn("D Sig",   width=100),
            "Weekly":  st.column_config.NumberColumn("Weekly",width=68),
            "W Sig":   st.column_config.TextColumn("W Sig",   width=100),
            "Monthly": st.column_config.NumberColumn("Monthly",width=68),
            "M Sig":   st.column_config.TextColumn("M Sig",   width=100),
        },
    )

    # ── Chart panel ───────────────────────────────────────
    sel = event.selection.rows if hasattr(event, "selection") else []
    if not sel:
        st.caption("← Select a row above to open the valuation chart")
        return

    row  = df_v.iloc[sel[0]]
    name, ft, bt = row["Pair"], row["Front"], row["Back"]
    st.divider()

    # Header
    sig_c = {"Overvalued":"#E84040","Undervalued":"#0EB87A","Neutral":"#F0A500"}.get(row["D Sig"],"#555")
    hc = st.columns([3,1,1,1,1,1,1])
    with hc[0]:
        st.markdown(
            f"<div style='font-size:22px;font-weight:500;font-family:IBM Plex Mono;color:{sig_c}'>{name}</div>"
            f"<div style='font-size:11px;color:#555;font-family:IBM Plex Mono;margin-top:2px'>{ft}  →  {bt}</div>",
            unsafe_allow_html=True)
    hc[1].metric("Daily",     fmt(row["Daily"]))
    hc[2].metric("D Signal",  row["D Sig"])
    hc[3].metric("Weekly",    fmt(row["Weekly"]))
    hc[4].metric("W Signal",  row["W Sig"])
    hc[5].metric("Monthly",   fmt(row["Monthly"]))
    hc[6].metric("M Signal",  row["M Sig"])

    tab_d, tab_w, tab_m = st.tabs(["Daily", "Weekly", "Monthly"])

    for tab, tf_label in [(tab_d,"Daily"),(tab_w,"Weekly"),(tab_m,"Monthly")]:
        with tab:
            fd = get_series(ft, tf_label)
            bd = get_series(bt, tf_label)

            if fd is None or bd is None:
                missing = ft if fd is None else bt
                clean   = missing.replace("bond:", "bond yield ")
                st.error(
                    f"**No data for `{clean}` ({tf_label})**  \n"
                    "Expand the **Data fetch log** above to see which sources were tried. "
                    "If all sources failed, try **↺ Refresh data** in the sidebar."
                )
                continue

            fig = build_chart(name, ft, bt, fd, bd,
                              length, rescale_len, threshold, tf_label)
            st.plotly_chart(fig, use_container_width=True,
                            key=f"chart_{name}_{tf_label}")

            val = calc_valuation(fd, bd, length, rescale_len).dropna()
            if len(val) >= 2:
                window = {"Daily":30,"Weekly":12,"Monthly":6}[tf_label]
                wl     = {"Daily":"30d","Weekly":"12wk","Monthly":"6mo"}[tf_label]
                s1,s2,s3,s4,s5 = st.columns(5)
                s1.metric("Current",       f"{val.iloc[-1]:+.1f}")
                s2.metric("Previous bar",  f"{val.iloc[-2]:+.1f}")
                s3.metric(f"{wl} high",    f"{val.iloc[-window:].max():.1f}" if len(val)>=window else "—")
                s4.metric(f"{wl} low",     f"{val.iloc[-window:].min():.1f}" if len(val)>=window else "—")
                s5.metric("Bars",          len(val))


if __name__ == "__main__":
    main()
