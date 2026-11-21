"""日本経済指標28項目および日銀金融政策決定会合スケジュールのマスター定義。"""

from __future__ import annotations

from typing import Any

CATEGORY_ORDER: list[str] = ["景気", "物価", "雇用・所得", "対外", "金利", "為替・市場"]

CATEGORY_GUIDES: dict[str, str] = {
    "景気": "実質GDP・景気動向指数（先行/一致/遅行）・鉱工業生産・機械受注・住宅着工・消費者信頼感など日本景気の体温計。",
    "物価": "総合CPI・コアCPI・コアコアCPI・企業物価指数など、日銀の金融政策正常化を左右するインフレ指標群。",
    "雇用・所得": "完全失業率・有効求人倍率・新規求人倍率・実質賃金など、賃金と物価の好循環を測る指標群。",
    "対外": "貿易収支・経常収支など、日本の対外収支と円需給の背景を示す指標群。",
    "金利": "無担保コール翌日物（政策金利）・日本10年国債利回り・マネタリーベースなど、日銀の金融政策と金利環境。",
    "為替・市場": "ドル円・日経平均株価・TOPIX・NT倍率など、日本株と為替マーケットの動向。",
}

# source_type: "estat" | "fred" | "calc_mom" | "calc_nt"
# cycle: "leading" (先行) | "coincident" (一致) | "lagging" (遅行) | None
INDICATORS_DEF: list[dict[str, Any]] = [
    # --- 景気 ---
    {
        "id": "gdp_real_growth", "source_type": "estat", "code": "0705020501000060000", "cycle": "coincident",
        "category": "景気", "name": "実質GDP成長率（前期比）", "shortName": "実質GDP",
        "unit": "%", "digits": 1, "frequency": "quarterly", "betterWhen": "up", "importance": 3,
        "ref_line": 0.0, "description": "日本経済全体の成長ペース（物価変動を除いた実質ベース）。プラス圏維持が景気拡大の基本。",
    },
    {
        "id": "leading_ci", "source_type": "estat", "code": "0706010400000090010", "cycle": "leading",
        "category": "景気", "name": "景気動向指数 CI先行指数", "shortName": "CI先行指数",
        "unit": "", "digits": 1, "frequency": "monthly", "betterWhen": "up", "importance": 3,
        "ref_line": 100.0, "description": "景気に数か月先行して動く主要指標を合成した指数（2020年=100）。転換点の早期察知に有用。",
    },
    {
        "id": "coincident_ci", "source_type": "estat", "code": "0706010500000090010", "cycle": "coincident",
        "category": "景気", "name": "景気動向指数 CI一致指数", "shortName": "CI一致指数",
        "unit": "", "digits": 1, "frequency": "monthly", "betterWhen": "up", "importance": 3,
        "ref_line": 100.0, "description": "内閣府が景気の現状（改善・足踏み・悪化）を判定する中核指標（2020年=100）。",
    },
    {
        "id": "industrial_production", "source_type": "estat", "code": "0502070301000090010", "cycle": "coincident",
        "category": "景気", "name": "鉱工業生産指数", "shortName": "鉱工業生産",
        "unit": "", "digits": 1, "frequency": "monthly", "betterWhen": "up", "importance": 3,
        "ref_line": 100.0, "description": "製造業を中心とした生産活動の水準を示す代表的な一致指標。",
    },
    {
        "id": "machinery_orders", "source_type": "estat", "code": "0701030000000010010", "cycle": "leading",
        "category": "景気", "name": "機械受注（船舶・電力を除く民需）", "shortName": "機械受注",
        "unit": "百万円", "digits": 0, "frequency": "monthly", "betterWhen": "up", "importance": 2,
        "ref_line": None, "description": "企業の設備投資の約6〜9か月先を占う代表的な先行指標。",
    },
    {
        "id": "machinery_orders_mom", "source_type": "calc_mom", "base_id": "machinery_orders", "cycle": "leading",
        "category": "景気", "name": "機械受注（前月比）", "shortName": "機械受注(前月比)",
        "unit": "%", "digits": 1, "frequency": "monthly", "betterWhen": "up", "importance": 2,
        "ref_line": 0.0, "description": "船舶・電力を除く民需の機械受注額から算出した前月比変化率。",
    },
    {
        "id": "housing_starts", "source_type": "estat", "code": "0802010103000010000", "cycle": "leading",
        "category": "景気", "name": "新設住宅着工戸数", "shortName": "住宅着工戸数",
        "unit": "戸", "digits": 0, "frequency": "monthly", "betterWhen": "up", "importance": 2,
        "ref_line": None, "description": "住宅投資の動向を映す先行指標。建設・家具・家電など裾野が広い。",
    },
    {
        "id": "household_spending_yoy", "source_type": "estat", "code": "0704010101000230000", "cycle": "coincident",
        "category": "景気", "name": "家計消費支出（実質・前年比）", "shortName": "家計消費支出",
        "unit": "%", "digits": 1, "frequency": "monthly", "betterWhen": "up", "importance": 2,
        "ref_line": 0.0, "description": "2人以上世帯の実質消費支出の前年比。個人消費の底堅さを測る。",
    },
    {
        "id": "tertiary_industry_activity", "source_type": "estat", "code": "0603100300000090010", "cycle": "coincident",
        "category": "景気", "name": "第3次産業活動指数", "shortName": "第3次産業活動",
        "unit": "", "digits": 1, "frequency": "monthly", "betterWhen": "up", "importance": 2,
        "ref_line": 100.0, "description": "GDPの約7割を占めるサービス産業全体の活動水準を示す指数。",
    },
    {
        "id": "consumer_confidence_jp", "source_type": "fred", "code": "CSCICP02JPM460S", "cycle": "leading",
        "category": "景気", "name": "消費者信頼感指数（OECD日本）", "shortName": "消費者信頼感",
        "unit": "", "digits": 2, "frequency": "monthly", "betterWhen": "up", "importance": 2,
        "ref_line": 100.0, "description": "家計の暮らし向き・収入見通しを映す先行指標。100が長期平均の目安。",
    },
    # --- 物価 ---
    {
        "id": "cpi_total_yoy", "source_type": "estat", "code": "0703010601010030000", "cycle": "lagging",
        "category": "物価", "name": "消費者物価指数 CPI（総合・前年比）", "shortName": "CPI(総合)",
        "unit": "%", "digits": 1, "frequency": "monthly", "betterWhen": "neutral", "importance": 3,
        "ref_line": 2.0, "description": "生鮮食品を含む総合インフレ率。家計の実感物価に近い。",
    },
    {
        "id": "cpi_core_yoy", "source_type": "estat", "code": "0703010601010030010", "cycle": "lagging",
        "category": "物価", "name": "コアCPI（生鮮食品除く・前年比）", "shortName": "コアCPI",
        "unit": "%", "digits": 1, "frequency": "monthly", "betterWhen": "neutral", "importance": 3,
        "ref_line": 2.0, "description": "日銀が物価安定目標（2%）の基準として最も重視するインフレ指標。",
    },
    {
        "id": "cpi_corecore_yoy", "source_type": "estat", "code": "0703010601010030040", "cycle": "lagging",
        "category": "物価", "name": "コアコアCPI（生鮮・エネルギー除く・前年比）", "shortName": "コアコアCPI",
        "unit": "%", "digits": 1, "frequency": "monthly", "betterWhen": "neutral", "importance": 3,
        "ref_line": 2.0, "description": "エネルギー価格変動を除いた基調的なインフレ圧力を示す指標。",
    },
    {
        "id": "ppi_yoy", "source_type": "estat", "code": "0703040400000030010", "cycle": None,
        "category": "物価", "name": "国内企業物価指数（前年比）", "shortName": "企業物価指数",
        "unit": "%", "digits": 1, "frequency": "monthly", "betterWhen": "neutral", "importance": 2,
        "ref_line": 2.0, "description": "企業間の取引価格の変動。CPIへの価格転嫁を見極める先行指標。",
    },
    # --- 雇用・所得 ---
    {
        "id": "unemployment_rate", "source_type": "estat", "code": "0301010000020020010", "cycle": "lagging",
        "category": "雇用・所得", "name": "完全失業率", "shortName": "失業率",
        "unit": "%", "digits": 1, "frequency": "monthly", "betterWhen": "down", "importance": 3,
        "ref_line": 3.0, "description": "労働市場の需給を表す遅行指標。2%台後半以下は構造的な人手不足水準。",
    },
    {
        "id": "jobs_to_applicants_ratio", "source_type": "estat", "code": "0301020001000010010", "cycle": "coincident",
        "category": "雇用・所得", "name": "有効求人倍率", "shortName": "有効求人倍率",
        "unit": "倍", "digits": 2, "frequency": "monthly", "betterWhen": "up", "importance": 3,
        "ref_line": 1.0, "description": "求職者1人あたりの求人数。1.0倍超は売り手市場を示す代表的な一致指標。",
    },
    {
        "id": "new_job_openings_ratio", "source_type": "estat", "code": "0301020002000010010", "cycle": "leading",
        "category": "雇用・所得", "name": "新規求人倍率", "shortName": "新規求人倍率",
        "unit": "倍", "digits": 2, "frequency": "monthly", "betterWhen": "up", "importance": 2,
        "ref_line": 2.0, "description": "新規求人に絞った倍率で、有効求人倍率より早く雇用環境の変化を映す先行指標。",
    },
    {
        "id": "real_wage_index_yoy", "source_type": "estat", "code": "0302030201010030010", "cycle": None,
        "category": "雇用・所得", "name": "実質賃金（前年比）", "shortName": "実質賃金",
        "unit": "%", "digits": 1, "frequency": "monthly", "betterWhen": "up", "importance": 3,
        "ref_line": 0.0, "description": "名目賃金から物価上昇分を差し引いた購買力。プラス定着が内需拡大と日銀利上げの鍵。",
    },
    # --- 対外 ---
    {
        "id": "trade_balance", "source_type": "estat", "code": "1601010101000010020", "cycle": None,
        "category": "対外", "name": "貿易収支（国際収支ベース）", "shortName": "貿易収支",
        "unit": "億円", "digits": 0, "frequency": "monthly", "betterWhen": "up", "importance": 2,
        "ref_line": 0.0, "description": "輸出と輸入の差額。資源価格や円相場の影響を受けやすい。",
    },
    {
        "id": "current_account", "source_type": "estat", "code": "1601010100000010000", "cycle": None,
        "category": "対外", "name": "経常収支", "shortName": "経常収支",
        "unit": "億円", "digits": 0, "frequency": "monthly", "betterWhen": "up", "importance": 2,
        "ref_line": 0.0, "description": "貿易・サービス収支と第一次所得収支（海外投資収益）の合計。",
    },
    # --- 金利 ---
    {
        "id": "call_rate", "source_type": "estat", "code": "0702020300000010010", "cycle": None,
        "category": "金利", "name": "無担保コール翌日物金利（政策金利）", "shortName": "政策金利",
        "unit": "%", "digits": 2, "frequency": "monthly", "betterWhen": "neutral", "importance": 3,
        "ref_line": 0.5, "description": "日本銀行の金融政策の誘導目標。利上げサイクルの進捗を直接示す。",
    },
    {
        "id": "jgb_10y_yield", "source_type": "estat", "code": "0702020300000010020", "cycle": None,
        "category": "金利", "name": "日本10年国債利回り（月次）", "shortName": "日本10年金利",
        "unit": "%", "digits": 2, "frequency": "monthly", "betterWhen": "neutral", "importance": 3,
        "ref_line": 1.0, "description": "日本の長期金利の指標。住宅ローン・銀行株・円相場に大きく影響する。",
    },
    {
        "id": "monetary_base_yoy", "source_type": "estat", "code": "0702010102000030010", "cycle": None,
        "category": "金利", "name": "マネタリーベース（前年比）", "shortName": "マネタリーベース",
        "unit": "%", "digits": 1, "frequency": "monthly", "betterWhen": "neutral", "importance": 2,
        "ref_line": 0.0, "description": "日銀が世の中に供給する資金量の前年比。金融緩和・引き締めの度合いを測る。",
    },
    # --- 為替・市場 ---
    {
        "id": "usdjpy", "source_type": "fred", "code": "DEXJPUS", "cycle": None,
        "category": "為替・市場", "name": "ドル円相場（日次）", "shortName": "ドル円",
        "unit": "円", "digits": 2, "frequency": "daily", "betterWhen": "neutral", "importance": 3,
        "ref_line": 150.0, "description": "輸出企業の業績と輸入物価を左右する日本の最重要為替レート。",
    },
    {
        "id": "nikkei225", "source_type": "fred", "code": "NIKKEI225", "cycle": "leading",
        "category": "為替・市場", "name": "日経平均株価（日次）", "shortName": "日経平均",
        "unit": "円", "digits": 0, "frequency": "daily", "betterWhen": "up", "importance": 3,
        "ref_line": None, "description": "東証プライム代表225銘柄で構成される株価指数（景気先行指標）。",
    },
    {
        "id": "topix", "source_type": "estat", "code": "0702020590000090010", "cycle": "leading",
        "category": "為替・市場", "name": "TOPIX（東証株価指数・月次）", "shortName": "TOPIX",
        "unit": "", "digits": 1, "frequency": "monthly", "betterWhen": "up", "importance": 3,
        "ref_line": None, "description": "日本株市場全体の時価総額を映す広範な株価指数。",
    },
    {
        "id": "nt_ratio", "source_type": "calc_nt", "code": "CALC_NT", "cycle": None,
        "category": "為替・市場", "name": "NT倍率（日経平均 ÷ TOPIX）", "shortName": "NT倍率",
        "unit": "倍", "digits": 2, "frequency": "monthly", "betterWhen": "neutral", "importance": 2,
        "ref_line": 14.0, "description": "日経平均とTOPIXの相対強弱。上昇は半導体・値がさ株優位、低下はバリュー・銀行株優位。",
    },
]

# 日銀金融政策決定会合スケジュール（2026〜2027年）
BOJ_EVENTS: list[dict[str, str]] = [
    {"date": "2026-01-23", "title": "日銀 金融政策決定会合（展望レポート）", "type": "BOJ", "note": "経済・物価情勢の展望公表"},
    {"date": "2026-03-19", "title": "日銀 金融政策決定会合", "type": "BOJ", "note": "春闘集中回答日直後の会合"},
    {"date": "2026-04-28", "title": "日銀 金融政策決定会合（展望レポート）", "type": "BOJ", "note": "経済・物価情勢の展望公表"},
    {"date": "2026-06-16", "title": "日銀 金融政策決定会合", "type": "BOJ", "note": "国債買入れ減額計画の中間評価等"},
    {"date": "2026-07-31", "title": "日銀 金融政策決定会合（展望レポート）", "type": "BOJ", "note": "経済・物価情勢の展望公表"},
    {"date": "2026-09-18", "title": "日銀 金融政策決定会合", "type": "BOJ", "note": "金融政策発表・総裁会見"},
    {"date": "2026-10-30", "title": "日銀 金融政策決定会合（展望レポート）", "type": "BOJ", "note": "経済・物価情勢の展望公表"},
    {"date": "2026-12-18", "title": "日銀 金融政策決定会合", "type": "BOJ", "note": "年内最終会合・総裁会見"},
    {"date": "2027-01-22", "title": "日銀 金融政策決定会合（展望レポート）", "type": "BOJ", "note": "経済・物価情勢の展望公表"},
    {"date": "2027-03-19", "title": "日銀 金融政策決定会合", "type": "BOJ", "note": "2027年春闘直後の会合"},
]
