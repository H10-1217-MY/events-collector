# event-collector

公開されている地域イベント情報を対象に、API優先・ルール順守の方針で収集し、統一形式に整形して保存・出力するツールです。

---

## 🧭 概要

本ツールは、大分・福岡などの地域イベント情報を、公式サイトの公開ページから収集し、再利用しやすい形に整形・保存・表示することを目的としています。

単なるスクレイピングではなく、

- 取得方法の切り分け（API / HTML）
- データの正規化
- 重複除去
- 保存形式の統一
- Streamlitによる一覧表示

といった「情報収集基盤」として設計しています。

---

## 🚀 現在の対応状況

### 対応収集元

- 大分県公式観光サイト  
  https://www.visit-oita.jp/events/

- 福岡県観光情報サイト クロスロードふくおか  
  https://www.crossroadfukuoka.jp/event

### 実装内容

- 一覧ページ取得
- ページネーション対応
- 詳細ページ取得
- イベント情報抽出
- 日付正規化
- 重複除去
- CSV / JSON / SQLite 出力
- Streamlitダッシュボード表示

### 取得実績（例）

- 大分イベント：約59件
- 福岡イベント：約43件
- 合計：約102件

---

## 🧩 取得データ形式

```json
{
  "title": "イベント名",
  "date_text": "2026年4月21日～2026年5月6日",
  "date_start": "2026-04-21",
  "date_end": "2026-05-06",
  "location": "開催地",
  "area": "大分",
  "price": "",
  "source_name": "visit_oita_events",
  "source_url": "https://www.visit-oita.jp/events/detail/xxx",
  "fetched_at": "2026-04-21T13:00:00"
}
```

## ⚙️機能

- HTMLページからのイベント情報収集
- 複数サイト対応
- ページネーション対応
- 詳細ページ解析
- 日付の正規化
- 重複イベントの除去
- データ保存
- Streamlitによる可視化

```text
events-collector/
├─ main.py
├─ app.py
├─ config/
│  └─ sources.yaml
├─ collectors/
│  ├─ base.py
│  ├─ api_collector.py
│  ├─ html_collector.py
│  └─ source_xxx.py
├─ models/
│  └─ event.py
├─ services/
│  ├─ normalize.py
│  ├─ dedup.py
│  └─ storage.py
├─ db/
│  └─ events.db
├─ outputs/
│  ├─ events.csv
│  └─ events.json
├─ logs/
│  └─ app.log
└─ tests/
   └─ test_normalize.py
```

## ▶️イベント情報の収集

```bash
python main.py
```

実行後、以下のファイルが出力されます。

- outputs/events.csv
- outputs/events.json
- db/events.db

## 🖥️ ダッシュボード表示

```bash
streamlit run app.py
```

ブラウザでStreamlitの画面が開き、収集したイベント情報を確認できます。

主な表示機能:

- 地域ごとの絞り込み
- キーワード検索
- 開催開始日での絞り込み
- 表形式での確認
- 表示中データのCSVダウンロード

### スクリーンショット

![dashboard](images\104238.png)

## 利用方針

本ツールは以下の方針で設計しています。

- 公開されている情報のみを対象とする
- APIが存在する場合はAPIを優先する
- 利用規約・robots.txt に配慮する
- 過剰なアクセスを行わない
- 学習・ポートフォリオ用途を想定する
- 画像や本文全文の再配布ではなく、イベント情報の整理を目的とする

## 今後の拡張予定

- 日付解析の精度向上（曖昧表現対応）
- 取得元サイトの追加
- ダッシュボードのUI改善
- 定期実行（スケジューラ）
