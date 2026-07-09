from src.firebase import admin as firebase_admin_module


def test_is_firebase_configured_false_without_project_id(monkeypatch):
    firebase_admin_module.reset_for_tests()
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)

    assert firebase_admin_module.is_firebase_configured() is False
    assert firebase_admin_module.get_firebase_app() is None

    firebase_admin_module.reset_for_tests()


def test_get_firestore_client_raises_when_not_configured(monkeypatch):
    firebase_admin_module.reset_for_tests()
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)

    try:
        firebase_admin_module.get_firestore_client()
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass

    firebase_admin_module.reset_for_tests()


def test_get_firebase_app_is_idempotent_once_init_attempted(monkeypatch):
    firebase_admin_module.reset_for_tests()
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)

    first = firebase_admin_module.get_firebase_app()
    second = firebase_admin_module.get_firebase_app()

    assert first is None
    assert second is None

    firebase_admin_module.reset_for_tests()
