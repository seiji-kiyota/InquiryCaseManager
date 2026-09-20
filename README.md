# 問い合わせ・案件管理ツール（InquiryCaseManager）

顧客・取引先などから受け付けた問い合わせを登録し、必要に応じて案件化して管理する業務支援ツールです。

## 概要

問い合わせの受付から案件化、対応履歴、進捗・期限管理、集計までを一連で扱うことを目指しています。  
現在は **Phase 8（CSV / Excel出力）** まで実装済みです。UI改善などの機能は今後のPhaseで追加します。

## 使用技術

- Python
- Streamlit
- SQLite
- Plotly
- openpyxl
- pytest

## 起動方法

```bash
pip install -r requirements.txt
streamlit run app.py
```

## テスト実行方法

```bash
python -m pytest -q
```

## 現在の開発状況

Phase 8：CSV / Excel出力（問い合わせ一覧・案件一覧の検索・絞り込み結果をそのまま出力、Excelはopenpyxl利用）
