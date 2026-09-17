import sys
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, process_holder):
        self.process_holder = process_holder

    def on_modified(self, event):
        # Only react to changes in smiley.py
        if event.src_path.endswith("smiley.py"):
            # Tell the main loop to restart the process
            if self.process_holder['process'] is not None:
                self.process_holder['process'].terminate()

def main():
    # A dictionary to hold our running process so the watcher can access it
    process_holder = {'process': None}
    
    # Set up the watcher
    observer = Observer()
    handler = ReloadHandler(process_holder)
    observer.schedule(handler, path=".", recursive=False)
    observer.start()

    print("Auto-reloader started. Edit 'smiley.py' and save to see it update!")
    print("Press Ctrl+C twice to stop completely.")

    try:
        while True:
            # Start smiley.py as a completely separate process
            # sys.executable is just the path to Python itself
            process_holder['process'] = subprocess.Popen([sys.executable, "smiley.py"])
            
            # Wait here until the process is killed (by the watcher) or exits (by pressing 'q')
            process_holder['process'].wait()
            
            # Small delay to prevent rapid-fire restarts if the text editor saves twice
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        # If you press Ctrl+C, stop everything
        pass
    finally:
        # Clean up
        if process_holder['process'] is not None:
            process_holder['process'].terminate()
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()