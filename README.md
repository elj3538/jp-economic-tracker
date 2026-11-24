# 日本経済指標トラッカー（`jp-economic-tracker`）

統計ダッシュボード（e-Stat）JSON API および FRED 公開CSV（**すべてAPIキー不要**）から日本主要27指標・主要マーケット6項目を自動取得し、「日本の景気を見る（先行・一致・遅行）」・2指標比較チャート・日銀会合スケジュールを備えた静的ダッシュボードを生成します。

## 実行方法
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py --workers 6
```
