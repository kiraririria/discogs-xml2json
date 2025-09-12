import time
import argparse
from datetime import timedelta
from typing import Any

from xml2json.parser import DiscogsXMLParser


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
        print(f"Время выполнения: {time_str}")
        return result

    return wrapper



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Process XML file')
    parser.add_argument('-i','--input', type=str, nargs='?',
                        default="C:\\Users\\Ivan\\PycharmProjects\\discogs-xml2json\\samples\\artists.xml",
                        help='Path to XML file')
    parser.add_argument('-o','--output', type=str, nargs='?',
                        default="C:\\Users\\Ivan\\PycharmProjects\\discogs-xml2json\\out\\artists.jsonl",
                        help='Path to JSONL file')
    args = parser.parse_args()



    xml_parser = DiscogsXMLParser(args.input)
    xml_parser.parse()
    # convert_xml_to_jsonl(args.input, args.output)