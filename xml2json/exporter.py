import json
from xml2json.parser import DiscogsArtistParser, DiscogsLabelParser, DiscogsMasterParser, DiscogsReleaseParser

class DumpExporter:
    def __init__(self):
        self.parsers = {
            "artists": DiscogsArtistParser,
            "labels": DiscogsLabelParser,
            "masters": DiscogsMasterParser,
            "releases": DiscogsReleaseParser
        }

    def export(self, xml_path: str, parser_type: str, output_path: str):
        parser_class = self.parsers.get(parser_type)
        if not parser_class:
            raise ValueError(f"Unknown parser type: {parser_type}")

        parser = parser_class(xml_path)

        with open(output_path, 'w', encoding='utf-8') as f:
            for data in parser.parse():
                json_line = json.dumps(data.to_dict(), ensure_ascii=False,separators=(',', ':'))
                f.write(json_line + '\n')

        print(f"[{parser_type}] was exported")