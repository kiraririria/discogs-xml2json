import json

from xml2json.parser import parse


def export(xml_path: str, output_path: str):

    with open(output_path, 'w', encoding='utf-8') as f:
        for data in parse(xml_path):
            pass
            #json_line = json.dumps(data, ensure_ascii=False,separators=(',', ':'))
            #f.write(json_line + '\n')

    print(f"[{output_path}] was exported")