import json
import time
from datetime import timedelta
from typing import Dict

from xml2json.parser import DiscogsArtistParser, DiscogsLabelParser, DiscogsMasterParser, DiscogsReleaseParser


def data2dict(entity) -> Dict:
    result = {'id': entity.id}

    for attr_name in dir(entity):
        if attr_name.startswith('_') or attr_name == 'id':
            continue

        try:
            attr_value = getattr(entity, attr_name)
        except AttributeError:
            continue

        if callable(attr_value):
            continue

        if isinstance(attr_value, (str, int, float, bool)) or attr_value is None:
            result[attr_name] = attr_value
        elif hasattr(attr_value, '__iter__'):
            result[attr_name] = [
                v.to_dict() if hasattr(v, 'to_dict') else v
                for v in attr_value
            ]
        elif hasattr(attr_value, 'to_dict'):
            result[attr_name] = attr_value.to_dict()
        else:
            result[attr_name] = str(attr_value)

    return result


class DumpExporter:
    def __init__(self):
        self.parsers = {
            "artists": DiscogsArtistParser,
            "labels": DiscogsLabelParser,
            "masters": DiscogsMasterParser,
            "releases": DiscogsReleaseParser
        }

    def export(self, xml_path: str, parser_type: str, output_path: str):
        start_time = time.time()

        parser_class = self.parsers.get(parser_type)
        if not parser_class:
            raise ValueError(f"Unknown parser type: {parser_type}")

        parser = parser_class(xml_path)

        with open(output_path, 'w', encoding='utf-8') as f:
            for data in parser.parse():
                if hasattr(data, 'to_dict'):
                    entity_dict = data.to_dict()
                else:
                    entity_dict = data2dict(data)
                json_line = json.dumps(entity_dict, ensure_ascii=False,separators=(',', ':'))
                f.write(json_line + '\n')

        total_time = time.time() - start_time
        total_time_str = str(timedelta(seconds=int(total_time)))
        print(f"Export[{parser_type}] Total time: {total_time_str}")