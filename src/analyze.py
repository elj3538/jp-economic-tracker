"""日本経済指標28項目のトレンド・zスコア・先行/一致/遅行サイクル分析を行うモジュール。"""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any


def _lookback_steps(freq: str) -> int:
    if freq == "daily":
        return 63
    if freq == "quarterly":
        return 1
    return 3


def analyze_jp_indicators(indicators: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    improving: list[dict[str, Any]] = []
    worsening: list[dict[str, Any]] = []
    neutral: list[dict[str, Any]] = []
    z_alerts: list[dict[str, Any]] = []
    turning_signals: list[dict[str, Any]] = []
    cycles: dict[str, list[dict[str, Any]]] = {"leading": [], "coincident": [], "lagging": []}
    by_id: dict[str, dict[str, Any]] = {}

    for ind in indicators:
        pts = ind.get("points", [])
        if len(pts) < 2:
            ind["stats"] = {"latest": None, "prev": None, "date": None, "diff": None, "diff_3m": None, "zscore": None, "trend": "neutral", "trend_label": "横ばい"}
            by_id[ind["id"]] = ind
            continue

        latest = pts[-1]["value"]
        latest_date = pts[-1]["date"]
        prev = pts[-2]["value"]
        diff = round(latest - prev, 3)

        lb = _lookback_steps(ind["frequency"])
        val_3m = pts[-1 - lb]["value"] if len(pts) > lb else pts[0]["value"]
        diff_3m = round(latest - val_3m, 3)

        win = pts[-756:] if ind["frequency"] == "daily" else pts[-60:]
        vals = [p["value"] for p in win]
        mu = mean(vals)
        sd = pstdev(vals) if len(vals) >= 3 else 0.0
        zscore = round((latest - mu) / sd, 2) if sd > 1e-6 else 0.0

        bw = ind.get("betterWhen", "neutral")
        th = sd * 0.20 if sd > 1e-6 else 0.0
        if bw == "neutral" or abs(diff_3m) <= th:
            trend, trend_label = "neutral", "横ばい"
        elif (bw == "up" and diff_3m > 0) or (bw == "down" and diff_3m < 0):
            trend, trend_label = "improving", "改善"
        else:
            trend, trend_label = "worsening", "悪化"

        turned = False
        if len(pts) > lb + 1 and abs(diff) > sd * 0.15 and abs(diff_3m) > sd * 0.20:
            if (diff > 0 and diff_3m < 0) or (diff < 0 and diff_3m > 0):
                turned = True

        ind["stats"] = {
            "latest": latest,
            "prev": prev,
            "date": latest_date,
            "diff": diff,
            "diff_3m": diff_3m,
            "mean_5y": round(mu, 3),
            "zscore": zscore,
            "trend": trend,
            "trend_label": trend_label,
            "turned": turned,
        }
        by_id[ind["id"]] = ind

        row = {
            "id": ind["id"],
            "shortName": ind["shortName"],
            "category": ind["category"],
            "latest": latest,
            "unit": ind["unit"],
            "digits": ind["digits"],
            "diff_3m": diff_3m,
            "zscore": zscore,
            "trend": trend,
            "trend_label": trend_label,
        }
        if trend == "improving":
            improving.append(row)
        elif trend == "worsening":
            worsening.append(row)
        else:
            neutral.append(row)

        if abs(zscore) >= 1.5:
            z_alerts.append(row)
        if turned:
            turning_signals.append(row)
        if ind.get("cycle") in cycles:
            cycles[ind["cycle"]].append(row)

    # 日本景気の総合判定（CI一致・CI先行・実質賃金・コアCPI）
    ci_c = by_id.get("coincident_ci", {}).get("stats", {})
    ci_l = by_id.get("leading_ci", {}).get("stats", {})
    rw = by_id.get("real_wage_index_yoy", {}).get("stats", {})
    cpi = by_id.get("cpi_core_yoy", {}).get("stats", {})

    checks: list[dict[str, Any]] = []
    if ci_c.get("diff_3m") is not None:
        checks.append({"name": "CI一致指数 3M改善", "ok": ci_c["diff_3m"] >= 0, "value": f"{ci_c['latest']:.1f} (3M {ci_c['diff_3m']:+.1f})"})
    if ci_l.get("diff_3m") is not None:
        checks.append({"name": "CI先行指数 3M改善", "ok": ci_l["diff_3m"] >= 0, "value": f"{ci_l['latest']:.1f} (3M {ci_l['diff_3m']:+.1f})"})
    if rw.get("latest") is not None:
        checks.append({"name": "実質賃金 プラス圏", "ok": rw["latest"] >= 0, "value": f"{rw['latest']:+.1f}%"})
    if cpi.get("latest") is not None:
        checks.append({"name": "コアCPI 2%目標達成", "ok": cpi["latest"] >= 2.0, "value": f"{cpi['latest']:.1f}%"})

    imp_n, wor_n = len(improving), len(worsening)
    if imp_n >= wor_n + 3:
        regime, regime_level = "景気回復・改善基調", "good"
    elif wor_n >= imp_n + 3:
        regime, regime_level = "景気減速・足踏み警戒", "bad"
    else:
        regime, regime_level = "緩やかな回復・強弱混在", "warn"

    z_alerts.sort(key=lambda x: abs(x["zscore"]), reverse=True)

    econ_summary = {
        "regime": regime,
        "regime_level": regime_level,
        "counts": {
            "total": len(indicators),
            "improving": imp_n,
            "worsening": wor_n,
            "neutral": len(neutral),
        },
        "jp_checks": checks,
        "cycles": cycles,
        "z_alerts": z_alerts[:8],
        "turning_signals": turning_signals[:8],
    }
    return indicators, econ_summary
