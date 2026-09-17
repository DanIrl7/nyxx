class AppState:
    """Holds the main loop's mutable state so handler functions don't need
    a dozen separate parameters."""

    def __init__(self, initial_state="home"):
        self.state = initial_state
        self.previous_state = "home"
        self.theme_mode = "scenes"
        self.confirm_delete = False
        self.running = True

        self.scene_theme = ""
        self.ui_theme = ""
        self.logo_enabled = True
