import json
import time
import xml.etree.ElementTree as ET
import argparse
from datetime import timedelta
from typing import Any, Dict


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


@timer
def run(input_file) -> None:
    for event, element in ET.iterparse(input_file, events=("end",)):
        if element.tag == "release":
            print(element.find("title").text)
            element.clear()


def element_to_dict(element: ET.Element) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    if element.attrib:
        result["@attributes"] = element.attrib

    if element.text and element.text.strip():
        result["#text"] = element.text.strip()

    for child in element:
        child_data: Dict[str, Any] = element_to_dict(child)

        if child.tag in result:
            if isinstance(result[child.tag], list):
                result[child.tag].append(child_data)
            else:
                result[child.tag] = [result[child.tag], child_data]
        else:
            result[child.tag] = child_data

    return result

@timer
def convert_xml_to_jsonl(input_file: str, output_file: str) -> None:
    with open(output_file, 'w', encoding='utf-8') as json_file:
        for event, element in ET.iterparse(input_file, events=('end',)):
            if element.tag == "release":
                release_dict: Dict[str, Any] = element_to_dict(element)
                json_line: str = json.dumps(release_dict, ensure_ascii=False)
                json_file.write(json_line + '\n')
                element.clear()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process XML file')
    parser.add_argument('-i','--input', type=str, nargs='?',
                        default="d:\\Downloads\\discogs_20241201_releases.xml\\discogs_20241201_releases.xml",
                        help='Path to XML file')
    parser.add_argument('-o','--output', type=str, nargs='?',
                        default="d:\\Downloads\\discogs_20241201_releases.xml\\discogs_20241201_releases.jsonl",
                        help='Path to JSONL file')
    args = parser.parse_args()

    convert_xml_to_jsonl(args.input, args.output)