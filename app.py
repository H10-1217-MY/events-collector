from pathlib import Path

import pandas as pd
import streamlit as st


CSV_PATH = Path("outputs/events.csv")


st.set_page_config(
    page_title="地域イベント収集ダッシュボード",
    layout="wide",
)


st.title("地域イベント収集ダッシュボード")
st.caption("大分・福岡の公開イベント情報を収集して一覧表示します。")


@st.cache_data
def load_events(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(csv_path)

    for col in [
        "title",
        "date_text",
        "date_start",
        "date_end",
        "location",
        "area",
        "price",
        "source_name",
        "source_url",
        "fetched_at",
    ]:
        if col not in df.columns:
            df[col] = ""

    df["date_start_dt"] = pd.to_datetime(df["date_start"], errors="coerce")
    df["date_end_dt"] = pd.to_datetime(df["date_end"], errors="coerce")

    return df


df = load_events(CSV_PATH)

if df.empty:
    st.warning("events.csv が見つからないか、データが空です。先に `python main.py` を実行してください。")
    st.stop()


st.sidebar.header("フィルタ")

areas = sorted([a for a in df["area"].dropna().unique().tolist() if a])
selected_areas = st.sidebar.multiselect(
    "地域",
    options=areas,
    default=areas,
)

keyword = st.sidebar.text_input("キーワード検索", "")

valid_dates = df["date_start_dt"].dropna()

if not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    date_range = st.sidebar.date_input(
        "開催開始日",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
else:
    date_range = None


filtered = df.copy()

if selected_areas:
    filtered = filtered[filtered["area"].isin(selected_areas)]

if keyword.strip():
    key = keyword.strip()
    mask = (
        filtered["title"].fillna("").str.contains(key, case=False, na=False)
        | filtered["location"].fillna("").str.contains(key, case=False, na=False)
        | filtered["date_text"].fillna("").str.contains(key, case=False, na=False)
    )
    filtered = filtered[mask]

if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        (filtered["date_start_dt"].isna())
        | (
            (filtered["date_start_dt"].dt.date >= start_date)
            & (filtered["date_start_dt"].dt.date <= end_date)
        )
    ]


col1, col2, col3 = st.columns(3)
col1.metric("表示件数", len(filtered))
col2.metric("全件数", len(df))
col3.metric("収集元数", df["source_name"].nunique())


display_cols = [
    "title",
    "date_start",
    "date_end",
    "date_text",
    "location",
    "area",
    "source_name",
    "source_url",
]

st.subheader("イベント一覧")

st.dataframe(
    filtered[display_cols],
    use_container_width=True,
    hide_index=True,
)

st.subheader("CSVダウンロード")

csv_bytes = filtered[display_cols].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

st.download_button(
    label="表示中のデータをCSVでダウンロード",
    data=csv_bytes,
    file_name="filtered_events.csv",
    mime="text/csv",
)