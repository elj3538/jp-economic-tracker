"""統計ダッシュボード（e-Stat API）・FRED公開CSV・stooqから日本経済指標とマーケットを取得するモジュール。"""

from __future__ import annotations

import io
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None
import requests as std_requests

logger = logging.getLogger(__name__)

ESTAT_API_URL = "https://dashboard.e-stat.go.jp/api/1.0/Json/getData?Lang=JP&IndicatorCode={code}&RegionCode=00000&TimeFrom={time_from}"
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
}


def _http_get(url: str, timeout: int = 20):
    if cffi_requests is not None:
        return cffi_requests.get(url, impersonate="chrome", timeout=timeout)
    return std_requests.get(url, headers=HEADERS, timeout=timeout)


def _parse_estat_time(t_str: str) -> str | None:
    """e-Statの @time（例: '20260900' や '20263Q00'）を 'YYYY-MM-DD' に変換する。"""
    s = str(t_str).strip()
    if len(s) < 6:
        return None
    yr = s[:4]
    if "Q" in s:
        q_map = {"1Q": "03-31", "2Q": "06-30", "3Q": "09-30", "4Q": "12-31"}
        q = s[4:6]
        if q in q_map:
            return f"{yr}-{q_map[q]}"
        return None
    mo = s[4:6]
    if mo.isdigit() and 1 <= int(mo) <= 12:
        return f"{yr}-{mo}-01"
    if mo == "00":
        return f"{yr}-12-31"
    return None


def fetch_estat_series(code: str, cache_dir: Path | None = None, use_cache: bool = True, quarterly: bool = False) -> list[dict[str, Any]]:
    cache_file = cache_dir / f"estat_{code}.json" if cache_dir else None
    if use_cache and cache_file and cache_file.exists():
        if (time.time() - cache_file.stat().st_mtime) / 3600.0 <= 16.0:
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    time_from = "20101Q00" if quarterly else "20100100"
    url = ESTAT_API_URL.format(code=code, time_from=time_from)
    for attempt in range(3):
        try:
            resp = _http_get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            objs = data.get("GET_STATS", {}).get("STATISTICAL_DATA", {}).get("DATA_INF", {}).get("DATA_OBJ", [])
            if isinstance(objs, dict):
                objs = [objs]
            by_date: dict[str, float] = {}
            for obj in objs:
                val_obj = obj.get("VALUE", {})
                # 全国データのみ（regionCode が '00000' または未指定）
                reg = str(val_obj.get("@regionCode", "00000"))
                if reg not in ("00000", ""):
                    continue
                dt = _parse_estat_time(val_obj.get("@time", ""))
                raw_v = val_obj.get("$")
                if not dt or raw_v is None or str(raw_v).strip() in ("", "-", "***", "..."):
                    continue
                try:
                    by_date[dt] = round(float(raw_v), 4)
                except (TypeError, ValueError):
                    continue
            pts = [{"date": d, "value": by_date[d]} for d in sorted(by_date.keys())]
            if cache_file and pts:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps(pts), encoding="utf-8")
            return pts
        except Exception as exc:
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            logger.warning("e-Stat [%s] 取得失敗: %s", code, exc)
            return []
    return []


def fetch_fred_series(series_id: str, cache_dir: Path | None = None, use_cache: bool = True) -> list[dict[str, Any]]:
    cache_file = cache_dir / f"fred_{series_id}.json" if cache_dir else None
    if use_cache and cache_file and cache_file.exists():
        if (time.time() - cache_file.stat().st_mtime) / 3600.0 <= 16.0:
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    url = FRED_CSV_URL.format(series_id=series_id)
    for attempt in range(3):
        try:
            resp = _http_get(url, timeout=20)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text))
            if df.shape[1] < 2:
                return []
            pts: list[dict[str, Any]] = []
            for d_raw, v_raw in zip(df.iloc[:, 0], df.iloc[:, 1]):
                if pd.isna(v_raw) or str(v_raw).strip() in ("", "."):
                    continue
                try:
                    pts.append({"date": str(d_raw)[:10], "value": round(float(v_raw), 4)})
                except (TypeError, ValueError):
                    continue
            if cache_file and pts:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps(pts), encoding="utf-8")
            return pts
        except Exception as exc:
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            logger.warning("FRED [%s] 取得失敗: %s", series_id, exc)
            return []
    return []


def _parse_wareki_date(s: str) -> str | None:
    s = s.strip()
    if not s or "." not in s:
        return None
    era = s[0].upper()
    parts = s[1:].split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return None
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    base = {"R": 2018, "H": 1988, "S": 1925}.get(era)
    if base is None:
        return None
    return f"{base + y:04d}-{m:02d}-{d:02d}"


def fetch_jgb10y_daily(cache_dir: Path | None = None, use_cache: bool = True) -> list[dict[str, Any]]:
    """財務省公式CSV（jgbcm_all.csv + jgbcm.csv）から最新の日本10年国債利回り日次推移を取得する。"""
    by_date: dict[str, float] = {}
    for url in (
        "https://www.mof.go.jp/jgbs/reference/interest_rate/data/jgbcm_all.csv",
        "https://www.mof.go.jp/jgbs/reference/interest_rate/jgbcm.csv",
    ):
        try:
            resp = _http_get(url, timeout=15)
            if resp.status_code != 200:
                continue
            for line in resp.content.decode("cp932", errors="ignore").splitlines():
                cols = [c.strip() for c in line.split(",")]
                if len(cols) <= 10:
                    continue
                dt = _parse_wareki_date(cols[0])
                if not dt or cols[10] in ("", "-"):
                    continue
                try:
                    by_date[dt] = round(float(cols[10]), 3)
                except ValueError:
                    continue
        except Exception:
            continue
    if by_date:
        return [{"date": d, "value": by_date[d]} for d in sorted(by_date.keys())[-90:]]
    return fetch_fred_series("IRLTLT01JPM156N", cache_dir=cache_dir, use_cache=use_cache)


def _fetch_yf_series(symbol: str) -> list[dict[str, Any]]:
    try:
        import yfinance as yf
        hist = yf.Ticker(symbol).history(period="4mo", interval="1d")
        if hist is None or hist.empty or "Close" not in hist.columns:
            return []
        close = hist["Close"].dropna()
        return [{"date": idx.strftime("%Y-%m-%d"), "value": round(float(v), 4)} for idx, v in close.items()]
    except Exception:
        return []


def fetch_all_jp_indicators(
    defs: list[dict[str, Any]],
    cache_dir: Path | None = None,
    use_cache: bool = True,
    workers: int = 6,
) -> tuple[list[dict[str, Any]], list[str]]:
    fetched: dict[str, list[dict[str, Any]]] = {}

    tasks = [d for d in defs if d["source_type"] in ("estat", "fred")]
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        fmap = {}
        for d in tasks:
            if d["source_type"] == "estat":
                fmap[pool.submit(fetch_estat_series, d["code"], cache_dir, use_cache, d["frequency"] == "quarterly")] = d["id"]
            else:
                fmap[pool.submit(fetch_fred_series, d["code"], cache_dir, use_cache)] = d["id"]
        for fut in as_completed(fmap):
            fetched[fmap[fut]] = fut.result()

    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for d in defs:
        st = d["source_type"]
        if st in ("estat", "fred"):
            pts = fetched.get(d["id"], [])
            src_url = (
                f"https://dashboard.e-stat.go.jp/graph?screenCode=00010"
                if st == "estat"
                else f"https://fred.stlouisfed.org/series/{d['code']}"
            )
        elif st == "calc_mom":
            base_pts = fetched.get(d["base_id"], [])
            pts = []
            for i in range(1, len(base_pts)):
                prev = base_pts[i - 1]["value"]
                if prev != 0:
                    pts.append({"date": base_pts[i]["date"], "value": round((base_pts[i]["value"] / prev - 1.0) * 100.0, 2)})
            src_url = "https://dashboard.e-stat.go.jp/"
        elif st == "calc_nt":
            nk = fetched.get("nikkei225", [])
            tp = fetched.get("topix", [])
            # 月末近傍の日経平均とTOPIX（月次）を照合してNT倍率を算出
            nk_by_ym: dict[str, float] = {}
            for p in nk:
                nk_by_ym[p["date"][:7]] = p["value"]
            pts = []
            for p in tp:
                ym = p["date"][:7]
                if ym in nk_by_ym and p["value"] > 0:
                    pts.append({"date": p["date"], "value": round(nk_by_ym[ym] / p["value"], 2)})
            src_url = "https://www.jpx.co.jp/"
        else:
            pts, src_url = [], ""

        if not pts:
            failures.append(d["id"])
        if d["frequency"] == "daily" and len(pts) > 2500:
            pts = pts[-2500:]
        item = dict(d)
        item["points"] = pts
        item["source_url"] = src_url
        results.append(item)
    return results, failures


def fetch_market_cards(cache_dir: Path | None = None, use_cache: bool = True) -> list[dict[str, Any]]:
    specs = [
        {"id": "nikkei225", "label": "日経平均株価", "unit": "円", "digits": 0, "yf": "^N225", "fred_id": "NIKKEI225", "source": "Yahoo Finance / FRED"},
        {"id": "usdjpy", "label": "ドル円", "unit": "円", "digits": 2, "yf": "JPY=X", "fred_id": "DEXJPUS", "source": "Yahoo Finance (日次)"},
        {"id": "jgb10y", "label": "日本10年国債利回り", "unit": "%", "digits": 2, "yf": None, "fred_id": "_JGB10Y_", "source": "財務省（日次国債金利）"},
        {"id": "us10y", "label": "米10年国債利回り", "unit": "%", "digits": 2, "yf": "^TNX", "fred_id": "DGS10", "source": "Yahoo Finance / 米財務省"},
        {"id": "sp500", "label": "S&P 500", "unit": "", "digits": 1, "yf": "^GSPC", "fred_id": "SP500", "source": "Yahoo Finance (日次)"},
        {"id": "wti", "label": "WTI原油", "unit": "ドル", "digits": 2, "yf": "CL=F", "fred_id": "DCOILWTICO", "source": "Yahoo Finance (先物日次)"},
    ]
    cards: list[dict[str, Any]] = []
    for sp in specs:
        if sp["fred_id"] == "_JGB10Y_":
            pts = fetch_jgb10y_daily(cache_dir=cache_dir, use_cache=use_cache)
        else:
            yf_pts = _fetch_yf_series(sp["yf"]) if sp.get("yf") else []
            fr_pts = fetch_fred_series(sp["fred_id"], cache_dir=cache_dir, use_cache=use_cache)
            if yf_pts and (not fr_pts or yf_pts[-1]["date"] >= fr_pts[-1]["date"]):
                pts = yf_pts
            else:
                pts = fr_pts
        if not pts:
            cards.append({**sp, "latest": None, "prev": None, "change": None, "change_pct": None, "date": None, "spark": [], "spark_dates": []})
            continue
        latest_d, latest_v = pts[-1]["date"], pts[-1]["value"]
        prev_v = pts[-2]["value"] if len(pts) >= 2 else latest_v
        chg = round(latest_v - prev_v, 4)
        chg_pct = round((latest_v / prev_v - 1.0) * 100.0, 2) if prev_v != 0 else None
        spark = [round(p["value"], 3) for p in pts[-60:]]
        spark_dates = [p["date"] for p in pts[-60:]]
        cards.append(
            {
                "id": sp["id"],
                "label": sp["label"],
                "unit": sp["unit"],
                "digits": sp["digits"],
                "source": sp["source"],
                "latest": round(latest_v, sp["digits"] if sp["digits"] > 0 else 1),
                "prev": round(prev_v, sp["digits"] if sp["digits"] > 0 else 1),
                "change": round(chg, 3),
                "change_pct": chg_pct,
                "date": latest_d,
                "spark": spark,
                "spark_dates": spark_dates,
            }
        )
    return cards
