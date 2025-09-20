import lxml.etree as etree
from typing import Dict, Any, List, Generator
import json


def parse_element(element: etree.Element) -> Any:
    if len(element) > 0 or element.attrib:
        result = {}

        for key, value in element.attrib.items():
            stripped_value = value.strip()
            if stripped_value:
                result[key] = stripped_value

        if element.text and element.text.strip():
            result['text'] = element.text.strip()

        children_by_tag = {}
        for child in element.iterchildren():
            if child.tag not in children_by_tag:
                children_by_tag[child.tag] = []
            children_by_tag[child.tag].append(parse_element(child))

        for tag, children in children_by_tag.items():
            if len(children) == 1 and not isinstance(children[0], dict):
                result[tag] = children[0]
            else:
                result[tag] = children

        return result
    else:
        return element.text.strip() if element.text and element.text.strip() else None


def parse(path: str) -> Generator[Dict[str, Any], None, None]:
    for event, element in etree.iterparse(path, events=("end",), tag="master"):
        result = parse_element(element)
        print(result)
        yield result
        element.clear()