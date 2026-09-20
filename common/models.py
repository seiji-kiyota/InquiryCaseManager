"""問い合わせ・案件管理で利用する定数定義。"""

INQUIRY_STATUSES = ("未対応", "対応中", "保留", "完了")
CASE_STATUSES = ("未着手", "対応中", "保留", "完了")
CASE_COMPLETED_STATUS = "完了"
PRIORITIES = ("低", "中", "高", "緊急")
CHANNELS = ("電話", "メール", "Web", "来店", "その他")
CATEGORIES = ("商品", "契約", "修理", "クレーム", "要望", "その他")
ACTION_TYPES = ("電話", "メール", "訪問", "社内確認", "その他")
STATUS_CHANGE_ACTION_TYPE = "ステータス変更"
TARGET_TYPES = ("問い合わせ", "案件")
INQUIRY_TARGET_TYPE = "問い合わせ"
ASSIGNEES = ("未割当", "山田", "佐藤", "鈴木")
UNASSIGNED_ASSIGNEE = "未割当"
