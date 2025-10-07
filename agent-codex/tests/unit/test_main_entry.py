import importlib
import sys
import types


def test_main_calls_run_app(monkeypatch):
    called = {"v": False}

    fake_app = types.ModuleType("src.ui.app")

    def fake_run_app():
        called["v"] = True

    fake_app.run_app = fake_run_app

    # Inject fake module to avoid importing real Tkinter UI
    sys.modules["src.ui.app"] = fake_app

    main_mod = importlib.import_module("src.main")
    main_mod.main()
    assert called["v"] is True
