import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.nyxx import background
from src.nyxx.background import SCENE_THEMES, USER_IMAGE_SCENE, resolve_scene
from src.nyxx.config import DEFAULTS


class TestSceneResolution:
    def test_default_scene_is_a_bundled_image(self):
        """A fresh install must not land on the empty 'user image' slot"""
        scene = resolve_scene(DEFAULTS["scene_theme"])
        assert scene != USER_IMAGE_SCENE
        assert "image_path" in SCENE_THEMES[scene]

    def test_saved_names_resolve_in_either_form(self):
        """Older configs saved the file stem ('vaporwave_sunset')"""
        assert resolve_scene("vaporwave_sunset") == "vaporwave sunset"
        assert resolve_scene("Vaporwave Sunset") == "vaporwave sunset"

    def test_unknown_scene_falls_back_to_default(self):
        assert resolve_scene("no_such_image") == DEFAULTS["scene_theme"]
        assert resolve_scene(None) == DEFAULTS["scene_theme"]

    def test_user_image_scene_is_kept(self):
        assert resolve_scene(USER_IMAGE_SCENE) == USER_IMAGE_SCENE

    def test_labels_are_readable_titles(self):
        assert SCENE_THEMES["vaporwave sunset"]["label"] == "Vaporwave Sunset"
        assert SCENE_THEMES[USER_IMAGE_SCENE]["label"] == "Browse File..."


class TestLoadError:
    def _engine(self, image_path):
        # Skips __init__, which needs a live curses screen.
        engine = background.BackgroundEngine.__new__(background.BackgroundEngine)
        engine.scene_theme = SCENE_THEMES[USER_IMAGE_SCENE]
        engine.user_image_path = image_path
        engine.load_error = None
        engine._register_user_image_combinations = lambda palette: None
        return engine

    def test_successful_load_clears_earlier_error(self, tmp_path):
        engine = self._engine(str(tmp_path / "missing.png"))
        engine._generate_scene(4, 8)
        assert engine.load_error

        engine.user_image_path = SCENE_THEMES["vaporwave sunset"]["image_path"]
        engine._generate_scene(4, 8)
        assert engine.load_error is None
