"""Utilities for working with pair of texts in two different languages."""
from collections import namedtuple
from functools import partial
from pathlib import Path
from typing import Dict, Generator, Optional, Tuple, Union
import csv
import logging
import os
import re
import string
import unicodedata

from lxml import etree
from translate.storage.tmx import tmxfile, tmxunit
import sacremoses as sm


log = logging.getLogger(__name__)


_non_printable_chars = re.compile('[^{}]'.format(
    re.escape(string.printable)))


LanguagePair = namedtuple('LanguagePair', ('source', 'target'))
"""A pair of languages used to describe a bitext."""


Sentence = namedtuple('Sentence', ('text', 'lang'))
"""A namedtuple storing a sentaece with given `text` in a language `lang`."""


text_xpath = etree.XPath('text()')
"""Return text of xml node subtree."""


def remove_control_characters(s, unicat='C'):
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != unicat)


def normalize(text: str, lang: str = None) -> str:
    """Normalize `text` for a given `lang`."""
    text = unicodedata.normalize('NFKD', text)
    text = remove_control_characters(text)
    text = sm.MosesPunctNormalizer(lang=lang).normalize(text)
    words = text.split(' ')
    text = ' '.join(_non_printable_chars.sub('', w) for w in words)
    return text


class tmxunitl2(tmxunit):
    """Version of tmxunit with support for LeveL 2 of the TMX specification."""

    def getNodeText(self, lang_node, xml_space='preserve'):
        xml_text = super().getNodeText(lang_node, xml_space)
        if xml_text is not None and any(('{' in xml_text, '}' in xml_text)):
            terms = lang_node.iterdescendants(self.namespaced(self.textNode))
            node = next(terms, None)
            if node is not None:
                sep = ' ' if '{j' in xml_text else ''
                return sep.join(text_xpath(node))
            return None
        return xml_text


class tmxfilel2(tmxfile):
    """Version of tmxfile with support for Level 2 of the TMX specification."""
    UnitClass = tmxunitl2


def sentences_from_lang_data(
        data: Dict,
        langs: Union[LanguagePair, tuple],
        fieldnames: Optional[Tuple[str, str]] = None) -> [Tuple[Sentence]]:
    """Return a 2-tuple of sentences from `data`.

    Sentences are returned in in the order described by `langs`.
    """
    sentences = []
    langs = LanguagePair(*langs)
    if fieldnames:
        keys = fieldnames
    else:
        keys = list(getattr(langs, loc)
                    for loc in ('source', 'target'))
    for (lang, key) in zip(langs, keys):
        text = data[key]
        if text is not None:
            text = normalize(data[key], lang)
            sentences.append(Sentence(text, lang))
    return tuple(sentences)


def sentences_from_tmx_node(
        node: [tmxunit],
        source_langs: Union[LanguagePair, tuple]) -> [Tuple[Sentence]]:
    """Return a 2-tuple of sentences from a `node` in TMX file."""
    directions = ('source', 'target')
    nm = {}
    langs = []
    for direction in directions:
        dom = getattr(node, f'{direction}_dom', None)
        if dom is None:
            return None
        lang_val = next(iter(dom.attrib.values()))
        lang_val = lang_val.split('-')[0]  # e.g: cope with en-GB
        lang = lang_val.lower()  # guard against case-mismatch
        text = getattr(node, direction)
        langs.append(lang)
        nm[lang] = text
    langs = tuple(langs)
    if source_langs != langs:
        raise ValueError(
            'Languages in TMX source are not in the expected order.',
            dict(source=langs,
                 expected=source_langs))
    if len(nm) == 2:
        try:
            return sentences_from_lang_data(nm, tuple(langs))
        except KeyError as ke:
            raise ValueError('Unexpected TMX', nm) from ke
    return None


def bitext_from_tmx(
        path: [Path],
        source_langs: Union[LanguagePair, tuple],
        **kw) -> Generator[Sentence, None, None]:
    """Generate sentences from a given a `path` to a TMX file."""
    with open(path, 'rb') as tmx_file:
        tmx = tmxfilel2(tmx_file)
        for node in tmx.unit_iter():
            sentences = sentences_from_tmx_node(node, source_langs)
            if sentences is not None:
                yield sentences


def bitext_from_csv(
        path: Path,
        source_langs: Union[LanguagePair, tuple],
        separator: str = ',',
        **kw) -> Generator[Sentence, None, None]:
    """Generate sentences from a given `path` to a CSV/TSV file.

    Sentences are returned in the order denoted by the 2-tuple `source_langs`.
    """
    source_langs = LanguagePair(*source_langs)
    dialect = type('CSVDialect' if separator == ',' else 'TSVDialect',
                   (csv.Dialect,),
                   dict(vars(csv.excel),
                        delimiter=separator,
                        quoting=csv.QUOTE_ALL))
    fieldnames = kw.get('fieldnames')
    if fieldnames is None:
        fieldnames = (source_langs.source, source_langs.target)
    with open(path) as fp:
        reader = csv.DictReader(fp, dialect=dialect)
        for row in reader:
            yield sentences_from_lang_data(row,
                                           source_langs,
                                           fieldnames=fieldnames)


_readers = (
    ('csv', bitext_from_csv),
    ('tsv', partial(bitext_from_csv, separator='\t')),
    ('tmx', bitext_from_tmx)
)


_replacements = (('\r\n', '\n'),
                 ('\n', ' '),
                 ('\t', ' ' * 4))


def process_sentence(sentence):
    replacements = dict(_replacements)
    text = sentence.text
    for (char, replacement) in replacements.items():
        text = text.replace(char, replacement)
    return Sentence(text.strip(), sentence.lang)


def to_bitext(
        path: Path,
        source_langs: Optional[Union[LanguagePair, Tuple]] = None,
        replacements: Dict[str, str] = None,
        **kw) -> Generator[Sentence, None, None]:
    """A generator `bitext` sentences from data in path `path`.

    Optional:

    `replacements`:

       Specify a mapping of character to replacement in
       `text_replacements`, to apply to items in the source data (e.g
       CSV row, XML tag) - by default - new-lines and tabs will be
       replaced with one 1 and 4 spaces respectively.

    Any keyword arguments are passed onto the relevant implementation.
    i.e: bitext_from_tmx or bitext_from_csv.
    """
    ext = os.path.splitext(path)[-1][1:]
    reader = dict(_readers).get(ext)
    if reader is None:
        raise NotImplementedError(f'No reader implemented for {ext} files')

    for sentences in reader(path, source_langs, **kw):
        yield tuple(map(process_sentence, sentences))


__all__ = ('Sentence',
           'bitext_from_csv',
           'bitext_from_tmx',
           'normalize',
           'process_sentence',
           'sentences_from_lang_data',
           'sentences_from_tmx_node'
           'tmxfilel2',
           'tmxunitl2'
           'to_bitext',)
