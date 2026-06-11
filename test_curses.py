from src.navii.ui import UIEngine
import time

try:
    ui = UIEngine()
    
    # Mock data: simulate directory listing
    mock_items = ["Documents", "Downloads", "Desktop", "Projects", "Config"]
    mock_path = "/Users/myname"
    
    # Render UI
    ui.draw_ui(mock_path, mock_items)
    
    # Keep visible for 5 seconds
    time.sleep(5)
    
except KeyboardInterrupt:
    pass
finally:
    ui.cleanup()