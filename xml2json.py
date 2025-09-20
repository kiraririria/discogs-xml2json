import time
from datetime import timedelta
from typing import Any

from xml2json.exporter import export

def timer(func) -> Any:
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        td = timedelta(seconds=elapsed_time)
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int(td.microseconds / 1000)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        print(f"Total Time: {time_str}")
        return result

    return wrapper

@timer
def main():
    export("samples/masters.xml",  "out/masters.jsonl")
    # exporter.export("D:\\Downloads\\dicogs\\discogs_20250901_labels.xml", "labels", "out/labels.jsonl")
    # exporter.export("D:\\Downloads\\dicogs\\discogs_20250901_artists.xml", "artists", "out/artists.jsonl")
    # exporter.export("D:\\Downloads\\dicogs\\discogs_20250901_masters.xml", "masters", "out/masters.jsonl")
    # exporter.export("D:\\Downloads\\dicogs\\discogs_20241201_releases.xml", "releases", "out/releases.jsonl")

if __name__ == '__main__':
    main()