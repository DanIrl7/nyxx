from src.nyxx.ui import UIEngine
from src.nyxx import screens
import time

try:
    ui = UIEngine()

    # Mock data: simulate directory listing
    mock_items = ["Documents", "Downloads", "Desktop", "Projects", "Config"]
    mock_path = "/Users/myname"

    # Render UI
    screens.draw_ui(ui, mock_path, mock_items)
    
    # Keep visible for 5 seconds
    time.sleep(5)
    
except KeyboardInterrupt:
    pass
finally:
    ui.cleanup()