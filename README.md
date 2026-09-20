# InquiryCaseManager

## 概要

問い合わせ受付から案件化・進捗管理までを一元管理する業務支援デモアプリです。  
受付、対応履歴、案件完了、KPI集計、CSV / Excel出力までの一連の流れを Streamlit 上で確認できます。

## Demo

[Streamlit Community Cloud でデモを開く](https://inquirycasemanager-demo.streamlit.app)

## 主な機能

- 問い合わせ登録
- 一覧・検索・絞り込み
- 詳細・編集
- 対応履歴
- ステータス変更履歴
- 案件化
- 案件管理
- 進捗率管理
- KPIダッシュボード
- Plotlyグラフ
- CSV / Excel出力

## デモデータ

初回起動時、問い合わせ・案件・履歴がすべて0件の場合だけ、サンプルデータを自動投入します。  
既存データがある場合は投入しません。

ダッシュボード下部に「デモ用サンプルデータを使用しています」と表示されます。

## 使用技術

- Python
- Streamlit
- SQLite
- Plotly
- openpyxl
- pytest
- Git / GitHub

## ローカル起動方法

```bash
pip install -r requirements.txt
streamlit run app.py
```

## テスト方法

```bash
python -m pytest -q
```

## Streamlit Community Cloud

1. このリポジトリを GitHub に Push する
2. [Streamlit Community Cloud](https://share.streamlit.io/) に GitHub アカウントでログインする
3. New app からリポジトリ・ブランチ `main`・Main file `app.py` を選ぶ
4. Deploy する
5. 公開URLは上記 Demo 欄を参照する

## 注意事項

- SQLite はデモ用途です。本番運用向けのDBではありません
- Streamlit Community Cloud では再起動などによりデータが初期化される可能性があります
- 本番用途では PostgreSQL などの外部DBを推奨します

## 今後の拡張

- 認証
- 権限管理
- メール通知
- 添付ファイル
- マスタ管理
- PostgreSQL
