import os
import time
import subprocess
import signal



FILES = [
    "background.py",
    "preview_background.py",
]


def get_times():
    return {
        file: os.path.getmtime(file)
        for file in FILES
    }


def start():
    return subprocess.Popen(
        ["python", "preview_background.py"]
    )


def main():

    process = start()

    last_times = get_times()

    try:
        while True:

            time.sleep(0.5)

            current_times = get_times()

            if current_times != last_times:

                print("Change detected. Restarting preview...")

                last_times = current_times

                # stop curses program
                process.send_signal(signal.SIGTERM)
                process.wait()

                time.sleep(0.2)

                process = start()


    except KeyboardInterrupt:

        process.send_signal(signal.SIGTERM)
        process.wait()


if __name__ == "__main__":
    main()