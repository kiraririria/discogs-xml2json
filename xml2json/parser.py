import time
from datetime import timedelta
from typing import Iterator, Generator
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


def children_text(element: etree.Element) -> Iterator[str]:
    for child in element.iterchildren():
        if child.text is not None:
            yield stripped(child)

def stripped(element: etree.Element) -> str:
    return element.text.strip() if element.text is not None else ""

@dataclass
class DumpData:
    id: int
    def __post_init__(self):
        pass
    def to_dict(self):
        result = {'id': self.id}
        for key in dir(self):
            if not key.startswith('_') and key != 'id' and not callable(getattr(self, key)):
                value = getattr(self, key)
                if hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()
                elif isinstance(value, (list, tuple)):
                    result[key] = [v.to_dict() if hasattr(v, 'to_dict') else v for v in value]
                else:
                    result[key] = value
        return result


class DynamicObject:
    __slots__ = ('__dict__',)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        result = {}
        for key in dir(self):
            if key.startswith('_'):
                continue

            try:
                value = getattr(self, key)
            except AttributeError:
                continue

            if callable(value):
                continue

            if isinstance(value, Generator):
                value = list(value)

            if hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            elif isinstance(value, (list, tuple)):
                result[key] = [v.to_dict() if hasattr(v, 'to_dict') else v for v in value]
            else:
                result[key] = value

        return result

class DiscogsXMLParser:
    parsed_element: str = None
    parent_element: str = None

    def parse(self) -> Iterator[DumpData]:
        count = 0
        start_time = time.time()
        last_log_time = start_time

        for event, element in etree.iterparse(self.path, events=('end',), tag=self.parsed_element):
            if element.getparent().tag!=self.parent_element:
                continue
            count += 1
            current_time = time.time()

            if count % 1000000 == 0:
                elapsed = current_time - start_time
                elapsed_str = str(timedelta(seconds=int(elapsed)))
                print(f"Count: {count}. Elapsed time: {elapsed_str}")
                last_log_time = current_time

            yield self.build(get_element_id(element), element)
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]

        total_time = time.time() - start_time
        total_time_str = str(timedelta(seconds=int(total_time)))
        print(f"[{self.parsed_element}] Elements: {count}. Total time: {total_time_str}")

    def build(self, element_id: int, element: etree.Element) -> DumpData:
        raise NotImplementedError

    def __init__(self, path: str) -> None:
        self.path = path
        pass


class DiscogsArtistParser(DiscogsXMLParser):
    parsed_element = "artist"
    parent_element = "artists"

    def build(self, element_id: int, element: etree.Element) -> DumpData:
        artist = DumpData(element_id)
        for child in element.iterchildren():
            tag = child.tag
            if tag in ("name", "realname", "profile", "data_quality"):
                setattr(artist, tag, stripped(child))
            elif tag in ("aliases", "namevariations", "groups", "urls"):
                setattr(artist, tag, list(children_text(child)))
            elif tag in ("members",):
                setattr(artist, tag,list([(int(child_.get('id')), stripped(child_)) for child_ in child.iterchildren()]))

        return artist


class DiscogsLabelParser(DiscogsXMLParser):
    parsed_element = "label"
    parent_element = "labels"

    def __build_sublabels_tags(self, element: etree.Element) -> Iterator[DynamicObject]:
        for child in element.iterchildren():
            sub_label = DynamicObject()
            setattr(sub_label, "id", child.get("id"))
            setattr(sub_label, "name", stripped(child))
            yield sub_label

    def build(self, element_id: int, element: etree.Element) -> DumpData:
        label = DumpData(element_id)
        for child in element.iterchildren():
            tag = child.tag
            if tag in ("name", "contactinfo", "profile", "data_quality"):
                setattr(label, tag, stripped(child))
            elif tag in ("urls",):
                setattr(label, tag, list(children_text(child)))
            elif tag in ("sublabels"):
                setattr(label, tag, list(self.__build_sublabels_tags(child)))
            elif tag in ("parentLabel",):
                setattr(label, tag, list([int(child.get('id')), stripped(child)]))

        return label


def build_artists(element: etree.Element) -> Iterator[DynamicObject]:
    for child in element.iterchildren():
        #okay.. some of the artists have no id :(
        artist = DynamicObject()
        for child_ in child.iterchildren():
            tag = child_.tag
            if tag in ("name", "join", "anv", "role"):
                setattr(artist, tag, stripped(child_))
            if tag in ("id",):
                setattr(artist, tag, int(child_.text))

        yield artist


def build_videos(element: etree.Element) -> Iterator[DynamicObject]:
    for child in element.iterchildren():
        video = DynamicObject()
        for child_ in child.iterchildren():
            tag = child_.tag
            if tag in ("title", "description"):
                setattr(video, tag, stripped(child_))
        for key, value in child.attrib.items():
            setattr(video, key, value.strip())
        yield video


class DiscogsMasterParser(DiscogsXMLParser):
    parsed_element = "master"
    parent_element = "masters"

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
    parent_element = "releases"

    def __build_attribute_tags(self, element: etree.Element) -> Iterator[DynamicObject]:
        for child in element.iterchildren():
            video = DynamicObject()
            for key, value in child.attrib.items():
                setattr(video, key, value.strip())
            yield video

    def __build_tracklist(self, element: etree.Element) -> Iterator[DynamicObject]:
        for child in element.iterchildren():
            video = DynamicObject()
            for child_ in child.iterchildren():
                tag = child_.tag
                if tag in ("position", "title","duration"):
                    setattr(video, tag, stripped(child_))
            yield video

    def __build_companies(self, element: etree.Element) -> Iterator[DynamicObject]:
        for child in element.iterchildren():
            company = DynamicObject()
            for child_ in child.iterchildren():
                tag = child_.tag
                if tag in ("name", "entity_type","entity_type_name","resource_url"):
                    setattr(company, tag, stripped(child_))
                if tag in ("id",):
                    setattr(company, tag, int(child_.text))
            yield company


    def __build_formats(self, element: etree.Element) -> Iterator[DynamicObject]:
        for child in element.iterchildren():
            video = DynamicObject()
            for e in child.iterchildren():
                t = e.tag
                if t in ('descriptions'):
                    setattr(video, t, list((children_text(e))))
            for key, value in child.attrib.items():
                setattr(video, key, value.strip())
            yield video

    def build(self, element_id: int, element: etree.Element) -> DumpData:
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

