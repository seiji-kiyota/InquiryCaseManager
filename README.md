# 問い合わせ・案件管理ツール（InquiryCaseManager）

顧客・取引先などから受け付けた問い合わせを登録し、必要に応じて案件化して管理する業務支援ツールです。

## 概要

問い合わせの受付から案件化、対応履歴、進捗・期限管理、集計までを一連で扱うことを目指しています。  
現在は **Phase 5（対応履歴）** まで実装済みです。案件化などの機能は今後のPhaseで追加します。

## 使用技術

- Python
- Streamlit
- SQLite
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

Phase 5：対応履歴（対応履歴追加、時系列表示、次回対応予定、ステータス変更履歴）
