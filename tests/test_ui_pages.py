from streamlit.testing.v1 import AppTest


MENUS = (
    "ダッシュボード",
    "問い合わせ登録",
    "問い合わせ一覧",
    "案件一覧",
    "集計・分析",
    "設定",
)


def _open_menu(menu):
    app = AppTest.from_file("app.py", default_timeout=15)
    app.run()
    app.radio[0].set_value(menu)
    app.run()
    return app


def test_all_menus_render_without_exception():
    for menu in MENUS:
        app = _open_menu(menu)
        assert not list(app.exception), menu
        assert any(item.value == menu for item in app.subheader)


def test_inquiry_register_form_is_visible():
    app = _open_menu("問い合わせ登録")
    labels = [item.label for item in app.text_input]
    assert "顧客名（必須）" in labels
    assert "件名（必須）" in labels
    assert any(button.label == "問い合わせを登録" for button in app.button)


def test_list_pages_render():
    for menu in ("問い合わせ一覧", "案件一覧"):
        app = _open_menu(menu)
        assert not list(app.exception)
        assert any(item.value == menu for item in app.subheader)


def test_placeholder_menus_explain_status():
    analytics = _open_menu("集計・分析")
    settings = _open_menu("設定")
    assert any("ダッシュボード" in item.value for item in analytics.info)
    settings_texts = [item.value for item in settings.caption] + [item.value for item in settings.info]
    assert any("Ver1.0" in text or "今後の拡張" in text for text in settings_texts)
