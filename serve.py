from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import build


DIRECTORY = build.PUBLIC_DIR
HOST = "localhost"
PORT = 8000
DIRECTORY_PATH = Path(DIRECTORY)


class WebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)


class FileChangeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.src_path.startswith(f".\\."):
            return
        print(":: Rebuilding")
        build.build()


if __name__ == "__main__":
    build.build()

    observer = Observer()

    event_handler = FileChangeHandler()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()
    
    server = HTTPServer((HOST, PORT), WebHandler)

    print(f":: ")
    print(f":: ")
    print(f":: Server started")
    print(f":: Serving {DIRECTORY}/ at http://{HOST}:{PORT}")
    print(f":: ")
    print(f":: Press Ctrl+C to exit the server")
    print(f":: ")
    print(f":: ")
    
    try:
        server.serve_forever(poll_interval=1)
    except KeyboardInterrupt:
        print(":: Shutting down")
    finally:
        observer.stop()
        observer.join(timeout=5)
        server.server_close()