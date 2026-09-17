import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.nyxx import config


class TestConfig:
    def setup_method(self, method):
        self._orig_path = config.CONFIG_PATH

    def teardown_method(self, method):
        config.CONFIG_PATH = self._orig_path

    def _use_tmp_path(self, tmp_path):
        config.CONFIG_PATH = str(tmp_path / "config.json")

    def test_load_config_returns_defaults_when_missing(self, tmp_path):
        self._use_tmp_path(tmp_path)
        assert config.load_config() == config.DEFAULTS

    def test_load_config_backfills_missing_keys(self, tmp_path):
        self._use_tmp_path(tmp_path)
        with open(config.CONFIG_PATH, "w") as f:
            json.dump({"ui_theme": "matrix green"}, f)

        loaded = config.load_config()
        assert loaded["ui_theme"] == "matrix green"
        assert loaded["bg_mode"] == config.DEFAULTS["bg_mode"]

    def test_load_config_ignores_invalid_json(self, tmp_path):
        self._use_tmp_path(tmp_path)
        with open(config.CONFIG_PATH, "w") as f:
            f.write("not valid json")

        assert config.load_config() == config.DEFAULTS

    def test_save_config_roundtrip(self, tmp_path):
        self._use_tmp_path(tmp_path)
        cfg = dict(config.DEFAULTS)
        cfg["ui_theme"] = "cyber cyan"
        config.save_config(cfg)

        assert config.load_config()["ui_theme"] == "cyber cyan"

    def test_get_returns_saved_value(self, tmp_path):
        self._use_tmp_path(tmp_path)
        config.set("ui_theme", "matrix green")
        assert config.get("ui_theme") == "matrix green"

    def test_get_returns_default_for_unset_key(self, tmp_path):
        self._use_tmp_path(tmp_path)
        assert config.get("bg_mode") == config.DEFAULTS["bg_mode"]
