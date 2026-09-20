# InquiryCaseManager

## 概要

顧客・取引先などから受け付けた問い合わせを登録し、案件化して進捗・期限まで一元管理する業務支援アプリです。  
受付から対応履歴、案件完了、集計、CSV / Excel出力までの一連の流れを、Streamlit上で操作できます。

## 主な機能

- 問い合わせ登録
- 一覧・検索
- 詳細・編集
- 対応履歴
- ステータス履歴
- 案件化
- 案件管理
- ダッシュボード
- CSV / Excel出力

## 使用技術

- Python
- Streamlit
- SQLite
- Plotly
- openpyxl
- pytest
- Git / GitHub

## 起動方法

```bash
pip install -r requirements.txt
streamlit run app.py
```

## テスト方法

```bash
python -m pytest -q
```

## 開発Phase

Phase 9：UI改善・総合テストまで完了しています。

1. 基盤構築
2. 問い合わせ登録
3. 一覧・検索
4. 詳細・編集
5. 対応履歴
6. 案件化・案件管理
7. ダッシュボード・集計
8. CSV / Excel出力
9. UI改善・総合テスト

## 今後の拡張

- ユーザー認証
- 権限管理
- メール通知
- 添付ファイル
- 担当者 / カテゴリマスタ
- PostgreSQL等
