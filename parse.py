from __future__ import annotations

import argparse
import bz2
from dataclasses import dataclass
import json
import string
import traceback
from typing import List, Dict, Tuple, Optional, TypeVar, Union, Sequence
import itertools
from collections import defaultdict
import re

import cattrs
import bs4
import wikitextparser as wtp


flatten = itertools.chain.from_iterable


@dataclass
class Section:
    level: int
    subsections: Dict[str, "Section"]
    top: wtp.Section
    top_span: Tuple[int, int]
    title: str  # stripped

    @staticmethod
    def from_wtp_section(sec: wtp.Section) -> "Section":
        subsections = [
            Section.from_wtp_section(s)
            for s in sec.get_sections(level=sec.level + 1)
            if s.string
        ]
        top_section = sec.get_sections(False, level=sec.level)[0]
        return Section(
            title=not_none(sec.title).strip(),
            top=top_section,
            top_span=top_section.span,
            subsections={s.title: s for s in subsections},
            level=sec.level,
        )


def remove_markup(text: str) -> str:
    w = wtp.parse(text)

    for t in reversed(w.get_bolds(recursive=False)):
        try:
            t[:] = t.text
        except:
            continue
    for t in reversed(w.get_italics(recursive=False)):
        try:
            t[:] = t.text
        except:
            continue
    for t in reversed(w.wikilinks):
        if t.wikilinks:
            del t[:]  # image
        else:
            t[:] = t.text or t.target
    for t in reversed(w.get_tags()):
        try:
            t[:] = not_none(t.contents)
        except:
            continue
    return w.plain_text(
        replace_wikilinks=False,
        replace_tags=False,
        replace_bolds_and_italics=False,
        _mutate=True,
    ).strip()


@dataclass
class Example:
    text: str
    kind: str
    source: List[str]

    @staticmethod
    def from_str(s: str) -> "Example":
        wt = wtp.parse(s)
        if wt.templates:
            t = wt.templates[0]
            return Example(
                text=remove_markup(t.arguments[0].value) if t.arguments else "",
                kind=t.name,
                source=[x.value for x in t.arguments[1:]],
            )
        else:
            return Example(text=remove_markup(s), kind="plain-text", source=[])


@dataclass
class Definition:
    definition: str
    examples: List[Example]
    register: Optional[str]
    context: Optional[str]
    time_period: Optional[str]
    is_lacking: bool
    # FIXME: rename
    is_borrowed: bool

    # FIXME: rename
    @staticmethod
    def from_definition_and_str(definition: str, exs: str) -> "Definition":
        examples = wtp.parse(exs).get_lists(r"\#:\*")
        tems = {
            t.name: "|".join([x.value for x in t.arguments])
            for t in wtp.parse(definition).templates
        }
        return Definition(
            definition=remove_markup(definition),
            examples=[Example.from_str(x) for x in examples[0].items]
            if examples
            else [],
            register=tems.get("משלב")
            or tems.get('משלב/ר"ת')
            or ("סלנג" if "סלנג" in tems else None),
            context=tems.get("הקשר"),
            is_lacking="פירוש לקוי" in tems,
            is_borrowed="בהשאלה" in tems,
            time_period=tems.get("רובד")
            or ("חזל" if "חזל" in tems else None)
            or ("מקרא" if "מקרא" in tems else None),
        )


def get_list_from_subsection(section: Section, titles: List[str]) -> Optional[List]:
    subsection = None
    for t in titles:
        if t in section.subsections:
            subsection = section.subsections[t]
            break
    if subsection is not None:
        ls = subsection.top.get_lists()
        if ls:
            return list(flatten(map(lambda l: l.items, ls)))
    return None


@dataclass
class WikiLink:
    text: str
    link: str

    @staticmethod
    def from_wtp_wikilink(wl: wtp.WikiLink) -> "WikiLink":
        return WikiLink(text=wl.text or wl.target, link=wl.target)


def parse_wikilinks(a: str) -> List[WikiLink]:
    return list(map(WikiLink.from_wtp_wikilink, wtp.parse(a).wikilinks))


# antonym_regex = re.compile(r'^(\s*\[\[(\w|\||\s|\-|#|\'|"|׳|״|־|[ְֲֳִֵֶַָֹֻּׁׂ])*\]\],?\s*)+(\s*\([^\)]*\))*\.?$|^\s*$')
# TODO: include the definition number (it's in paren's)
def parse_antonym(a: str) -> Sequence[Union[WikiLink, str]]:
    wls: Sequence[Union[WikiLink, str]] = parse_wikilinks(a)
    if not wls and a.strip():
        return [a]
    return wls


wiktionary_gender_to_english: Dict[str, str] = {
    "זכר": "male",
    "נקבה": "female",
    "ז": "male",
    "נ": "female",
    "זכר רבוי": "male plural",
    "זכר רבים": "male plural",
    "זכר ונקבה": "male and female",
    "זכר ריבוי": "male plural",
    "זכר זוגי": "male dual",
    'זו"נ': "male and female",
    "נקבה רבוי": "female plural",
    "ז'": "male",
    "נקבה ריבוי": "female plural",
    "זכר יחיד": "male",
    'ז"ר': "male plural",
    "נ'": "female",
}

wiktionary_pos_to_english: Dict[str, str] = {
    "שם־עצם": "noun",
    "שם-עצם": "noun",
    "שם עצם": "noun",
    "צרף": "phrase",
    "תואר": "adjective",
    "שם־תואר": "adjective",
    "תואר הפועל": "adverb",
    "שם-תואר": "adjective",
    "שם תואר": "adjective",
    # "ע": "",
    "שם פרטי": "proper noun",
    "צירוף שמני": "noun",
    "מילת קריאה": "interjection",
    "פועל": "verb",
    "שם־פעולה": "gerund",
    "תואר־הפועל": "adverb",
    "שם-פרטי": "proper noun",
    "מילת חיבור": "conjunction",
    "שם־פרטי": "proper noun",
    "מילת יחס": "preposition",
    "ביטוי": "expression",
    "מילת שאלה": "interrogative",
    # "צירוף": "",
    "שם": "noun",
    "שם עצם (תואר)": "noun",
    # "שם־עצם פרטי": "",
    # "היגד": "",
    "תחילית": "prefix",
    "שם־תאר": "adjective",
    "שם־עצם, שם־תואר": "noun",
    "תאר": "adjective",
    "שם־עצם מופשט": "noun",
}

wiktionary_pronunciation_to_ipa: Dict[str, str] = {
    "׳": "ʔ",
    "'": "ʔ",
    "sh": "ʃ",
    "kh": "x",
    "ch": "tʃ",
    # "dj": "dʒ",
    "j": "ʒ",
    "y": "j",
}
wiktionary_pronunciation_regex = re.compile(
    "(" + "|".join(wiktionary_pronunciation_to_ipa) + ")"
)


wiktionary_form_tag: Dict[str, str] = {
    "ר'": "plural",
    "נ'": "female",
    'נ"ר': "female plural",
    "כ'": "possessive",
    'נ"י:': "female",
    "ר׳": "plural",
    'ס"ר': "construct plural",
    "ר':": "plural",
    'נ"ר:': "female plural",
    "כ':": "possessive",
    "נ':": "female",
    'ר"נ:': "female plural",
    'ר"ז:': "male plural",
    "ס'": "construct",
    "נ׳": "female",
    "נס'": "female construct",
    "נ״ר": "female plural",
    "<BR>ר'": "plural",
    '<BR>נ"ר': "female plural",
    '<br>נ"ר': "female plural",
    "זוגי": "dual",
    # "הפסק:": "x",
    "רבים": "plural",
    "ז'": "male",
    "יחיד": "singular",
    'נ"נ:': "female construct",
    "זוגי:": "dual",
    "ס״ר": "construct plural",
    'נ"י': "female",
    "נסמך": "construct",
    'ס"י:': "construct",
    "שלי:": "possessive",
    "שלו:": "possessive",
    "ס׳": "construct",
    # "הפסק": "x",
    "י'": "singular",
    "(נ'": "female",
    'ז"ר': "male plural",
    'ס"ר:': "construct plural",
    "יחידה:": "female",
    "ר": "plural",
    "ביידוע:": "definite",
}

form_tag_regex = re.compile("(" + "|".join(map(re.escape, wiktionary_form_tag)) + ")")

decl_delim_regex = re.compile(r"\s*[,;]\s*")


def parse_form(f: str) -> tuple[str, str]:
    if " " in f:
        if m := form_tag_regex.match(f):
            try:
                return wiktionary_form_tag[m.group(1)], f.split(maxsplit=1)[1]
            except Exception:
                print("form:", f, "m:", m)
    elif f.endswith("־"):
        return "construct", f[:-1]
    return "unknown", f


@dataclass
class GrammarInfo:
    pronunciation: Optional[str]
    ktiv_male: Optional[str]
    gender: Optional[str]
    root: Optional[str]
    part_of_speech: Optional[str]
    morphology: Optional[str]
    declensions: Optional[List[Tuple[str, str]]]

    @staticmethod
    def from_dict(d: Dict[str, str]) -> "GrammarInfo":
        root = d.get("שורש")
        if root is not None:
            w = wtp.parse(root)
            root = None
            if w.templates:
                t = w.templates[0]
                if t.name == "שרש":
                    root = t.arguments[0].value
                elif t.name in {"שרש3", "שרש4", "שרש5"}:
                    radicals_num = int(t.name[-1])
                    root = "".join(map(lambda a: a.value, t.arguments[:radicals_num]))

        gender = d.get("מין")
        pos = d.get("חלק דיבר")
        pronunciation = d.get("הגייה")
        if pronunciation is not None:
            w = wtp.parse(pronunciation)
            for b in reversed(w.get_bolds(recursive=False)):
                try:
                    b[:] = "!" + b.text
                except:
                    b[:] = "!"
            pronunciation = wiktionary_pronunciation_regex.sub(
                lambda x: wiktionary_pronunciation_to_ipa[x.group(1)],
                w.string,
            ).replace("!", "'")

        declensions = None
        if decls := d.get("נטיות"):
            declensions = list(map(parse_form, decl_delim_regex.split(decls)))

        return GrammarInfo(
            pronunciation=pronunciation or None,
            ktiv_male=d.get("כתיב מלא") or None,
            gender=wiktionary_gender_to_english.get(gender)
            if gender is not None
            else None,
            root=root,
            part_of_speech=wiktionary_pos_to_english.get(pos)
            if pos is not None
            else None,
            morphology=d.get("דרך תצורה") or None,
            declensions=declensions,
        )


@dataclass
class Entry:
    title: str
    grammatical_info: Optional[GrammarInfo]
    definitions: List[Definition]
    expressions: List[WikiLink]
    derivatives: List[WikiLink]
    synonyms: List[Union[WikiLink, str]]
    antonyms: List[Union[WikiLink, str]]
    translations: Dict[str, List[str]]  # lang -> translations
    see_also: List[WikiLink]
    external_links: Dict[str, str]  # site_name_in_hebrew -> entry_name
    etymology: List[str]
    extra_info: Optional[str]

    @staticmethod
    def from_section(sec: Section) -> "Entry":
        assert sec.level == 2

        grammatical_info = None
        tem = next(filter(lambda t: t.name == "ניתוח דקדוקי", sec.top.templates), None)
        if tem is not None:
            info = {}
            for arg in tem.arguments[1:]:
                info[arg.name.strip()] = arg.value.strip()
            grammatical_info = GrammarInfo.from_dict(info)

        translations: Dict[str, List[str]] = defaultdict(list)
        if "תרגום" in sec.subsections:
            tems = [t for t in sec.subsections["תרגום"].top.templates if t.name == "ת"]
            for t in tems:
                if len(t.arguments) >= 2:
                    translations[t.arguments[0].value].append(t.arguments[1].value)
        translations = dict(translations)

        external_links = {}
        if "קישורים חיצוניים" in sec.subsections:
            for temp in sec.subsections["קישורים חיצוניים"].top.templates:
                if temp.name == "מיזמים":
                    for arg in temp.arguments:
                        external_links[arg.name] = arg.value

        l = sec.top.get_lists()
        definitions = (
            [
                Definition.from_definition_and_str(
                    t, l[0].sublists(i)[0].string if l[0].sublists(i) else ""
                )
                for i, t in enumerate(l[0].items)
            ]
            if l
            else []
        )

        expressions = list(
            flatten(
                map(
                    parse_wikilinks,
                    get_list_from_subsection(
                        sec,
                        [
                            "צירופים",
                        ],
                    )
                    or [],
                )
            )
        )

        see_also = list(
            flatten(
                map(parse_wikilinks, get_list_from_subsection(sec, ["ראו גם"]) or [])
            )
        )

        # FIXME: it's not always a list [see https://he.wiktionary.org/wiki/%D7%99%D7%A9%D7%95%D7%9E%D7%95%D7%9F]
        etymology = list(
            map(remove_markup, get_list_from_subsection(sec, ["גיזרון", "גזרון"]) or [])
        )

        synonyms = antonyms = list(
            flatten(
                map(
                    parse_antonym, get_list_from_subsection(sec, ["מילים נרדפות"]) or []
                )
            )
        )

        antonyms = list(
            flatten(
                map(
                    parse_antonym,
                    get_list_from_subsection(sec, ["ניגודים", "הפכים"]) or [],
                )
            )
        )

        derivatives = list(
            flatten(
                map(parse_wikilinks, get_list_from_subsection(sec, ["נגזרות"]) or [])
            )
        )

        return Entry(
            title=sec.title,
            grammatical_info=grammatical_info,
            definitions=definitions,
            expressions=expressions,
            derivatives=derivatives,
            synonyms=synonyms,
            antonyms=antonyms,
            translations=translations,
            see_also=see_also,
            external_links=external_links,
            etymology=etymology,
            extra_info=None,  # TODO
        )


T = TypeVar("T")


def not_none(v: T | None) -> T:
    assert v is not None
    return v


@dataclass
class Page:
    pid: int
    revision_id: int
    sha1: str
    entries: List[Entry]
    title: str

    @staticmethod
    def from_xml(xml: bs4.Tag) -> "Page":
        rev = xml.revision
        text = not_none(not_none(rev).find("text")).get_text()
        parsed = wtp.parse(text)
        sections = parsed.get_sections(level=2)

        return Page(
            title=not_none(xml.title).get_text(),
            pid=int(not_none(xml.id).get_text()),
            revision_id=int(not_none(not_none(rev).id).get_text()),
            sha1=not_none(not_none(rev).sha1).get_text(),
            entries=list(
                map(Entry.from_section, [Section.from_wtp_section(s) for s in sections])
            ),
        )


def try_parse_page(xml: bs4.Tag) -> Page | None:
    try:
        return Page.from_xml(xml)
    except Exception as exc:
        print(not_none(xml.title).get_text(), exc, traceback.print_exc())
        return None


def parse_pages(path: str) -> List[Page]:
    with bz2.open(path, "rt") as f:
        soup = bs4.BeautifulSoup(f.read(), "xml")

    return list(
        filter(
            None,
            map(
                try_parse_page,
                filter(
                    lambda p: p.ns.text == "0",
                    not_none(soup.mediawiki).find_all("page", recursive=False),
                ),
            ),
        )
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ns = ap.parse_args()
    pages = [
        p
        for p in parse_pages(ns.dump)
        if not (set(p.title) & set(string.ascii_letters))
    ]
    with open("pages.json", "w") as fh:
        json.dump(cattrs.unstructure(pages), fh)


if __name__ == "__main__":
    main()
