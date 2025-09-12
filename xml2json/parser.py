from typing import Iterator, Optional
from dataclasses import dataclass
import lxml.etree as etree


def get_element_id(element: etree.Element) -> int:
    """ The artists.xml and labels.xml have no 'id' attribute, but have children <id> tag """
    id_ = element.get("id")
    if id_ is None:
        id__ = element.find("id")
        if id__ is not None:
            id_ = id__.text
        if id_ is None:
            raise ValueError(f"Element has no id")
    return int(id_)


xpath_ancestor_finder = 'ancestor-or-self::*'


def clear_memory(element: etree.Element):
    """ This function should clear unnecessary elements with their parents """
    element.clear()
    for ancestor in element.xpath(xpath_ancestor_finder):
        while ancestor.getprevious() is not None:
            del ancestor.getparent()[0]


def children_text(element: etree.Element) -> Optional[list[str],Iterator[str]]:
    for child in element.iterchildren():
        if child.text is not None:
            yield stripped(child)

def stripped(element: etree.Element) -> str:
    return element.text.strip() if element.text is not None else ""

@dataclass
class DumpData:
    id: int

class DiscogsXMLParser:
    parsed_element: str = None

    def parse(self) -> object:
        for event, element in etree.iterparse(self.path, events=('start', 'end'), tag=self.parsed_element):
            yield self.build(get_element_id(element), element)
            clear_memory(element)

    def build(self, element_id: int, element: etree.Element) -> object:
        raise NotImplementedError

    def __init__(self, path: str) -> None:
        self.path = path
        pass


class DiscogsArtistParser(DiscogsXMLParser):
    parsed_element = "artist"

    def build(self, element_id: int, element: etree.Element) -> DumpData:
        artist = DumpData(element_id)
        for child in element.iterchildren():
            tag = child.tag
            if tag in ("name", "realname", "profile", "data_quality"):
                setattr(artist, tag, stripped(child))
            elif tag in ("aliases", "namevariations", "groups", "urls"):
                setattr(artist, tag, children_text(child))
            elif tag in ("members",):
                """<name id="12186">John Ciafone</name></members>"""
                setattr(artist, tag,list([(int(child_.get('id')), stripped(child_)) for child_ in child.iterchildren()]))

        return artist


class DiscogsLabelParser(DiscogsXMLParser):
    parsed_element = "label"

    def build(self, element_id: int, element: etree.Element) -> DumpData:
        label = DumpData(element_id)
        for child in element.iterchildren():
            tag = child.tag
            if tag in ("name", "contactinfo", "profile", "data_quality"):
                setattr(label, tag, stripped(child))
            elif tag in ("urls",):
                setattr(label, tag, children_text(child))
            elif tag in ("parentLabel",):
                setattr(label, tag, list([int(child.get('id')), stripped(child)]))
            elif tag in ("sublabels",):
                setattr(label, tag,list([(int(child_.get('id')), stripped(child_)) for child_ in child.iterchildren()]))

        return label


def build_artists(element: etree.Element) -> Iterator[DumpData]:
    for child in element.iterchildren():
        artist = DumpData(get_element_id(child))
        for child_ in child.iterchildren():
            tag = child_.tag
            if tag in ("name", "join", "anv", "role"):
                setattr(artist, tag, stripped(child_))
        yield artist


def build_videos(element: etree.Element) -> Iterator[object]:
    for child in element.iterchildren():
        video = object()
        for child_ in child.iterchildren():
            tag = child_.tag
            if tag in ("title", "description"):
                setattr(video, tag, stripped(child_))
        for key, value in child.attrib.items():
            setattr(video, key, value.strip())
        yield video


class DiscogsMasterParser(DiscogsXMLParser):
    parsed_element = "master"

    def build(self, element_id: int, element: etree.Element) -> DumpData:
        master = DumpData(element_id)
        for child in element.iterchildren():
            tag = child.tag
            if tag in ("main_release", "year", "title", "data_quality"):
                setattr(master, tag, stripped(child))
            elif tag in ("genres", "styles"):
                setattr(master, tag, list(children_text(child)))
            elif tag == "artists":
                setattr(master, tag, list(build_artists(child)))
            elif tag == "videos":
                setattr(master, tag, list(build_videos(child)))

        return master


class DiscogsReleaseParser(DiscogsXMLParser):
    parsed_element = "release"

    def __build_attribute_tags(self, element: etree.Element) -> Iterator[object]:
        for child in element.iterchildren():
            video = object()
            for key, value in child.attrib.items():
                setattr(video, key, value.strip())
            yield video

    def __build_tracklist(self, element: etree.Element) -> Iterator[object]:
        for child in element.iterchildren():
            video = object()
            for child_ in child.iterchildren():
                tag = child_.tag
                if tag in ("position", "title","duration"):
                    setattr(video, tag, stripped(child_))
            yield video

    def __build_companies(self, element: etree.Element) -> Iterator[DumpData]:
        for child in element.iterchildren():
            company = DumpData(get_element_id(element))
            for child_ in child.iterchildren():
                tag = child_.tag
                if tag in ("name", "entity_type","entity_type_name","resource_url"):
                    setattr(company, tag, stripped(child_))
            yield company


    def __build_formats(self, element: etree.Element) -> Iterator[object]:
        for child in element.iterchildren():
            video = object()
            for e in child.iterchildren():
                t = e.tag
                if t in ('descriptions'):
                    setattr(video, t, "; ".join(children_text(e)))
            for key, value in child.attrib.items():
                setattr(video, key, value.strip())
            yield video

    def build(self, element_id: int, element: etree.Element) -> object:
        release = DumpData(element_id)
        setattr(release, 'status', element.get('status'))
        for child in element.iterchildren():
            tag = child.tag
            if tag in ("title", "country", "released", "notes","data_quality"):
                setattr(release, tag, stripped(child))
            elif tag in ("genres","styles"):
                setattr(release, tag, list(children_text(child)))
            elif tag in ("artists", "extraartists"):
                setattr(release, tag, list(build_artists(child)))
            elif tag in ("identifiers","labels"):
                setattr(release, tag, list(self.__build_attribute_tags(child)))
            elif tag == "videos":
                setattr(release, tag, list(build_videos(child)))
            elif tag == "tracklist":
                setattr(release, tag, list(self.__build_tracklist(child)))
            elif tag == "companies":
                setattr(release, tag, list(self.__build_companies(child)))
            elif tag == "formats":
                setattr(release, tag, list(self.__build_formats(child)))
            elif tag == "master_id":
                setattr(release, tag, int(child.text))
        return release

