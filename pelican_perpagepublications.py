"""
Pelican PerPagePublications
==============

A Pelican plugin that populates the context with a list of formatted
citations, loaded from a BibTeX several bibtex files  given in the page or post
metadata. This is based on the Pelica Bibtex plugin by Vlad Niculae.

This plugin will create per type publication lists (i.e. conference, books, journals ...)
based on bibtex databases given in the page/post metadata for example for a CV.
"""
# Author of Pelican Bibtex: Vlad Niculae <vlad@vene.ro>
# Author of PerPagePublications: Jochen Schroeder <cycomanic@gmail.com>
# Unlicense (see UNLICENSE for details)

import logging
import codecs
import latexcodec
logger = logging.getLogger(__name__)
from tempfile import TemporaryDirectory, mkdtemp
import os

from pelican import signals

__version__ = '0.1.0'


def add_publications(generator, metadata):
    """
    Populates context with a list of BibTeX publications.

    Configuration
    -------------
    generator.settings['Publication_SRC']
     local path to the Bibtex file to read
    
    Output
    ------
    generator.context['journal']:
        List of tuples (key, year, text, bibtex, url, slides, poster).
    generator.context['conference']:
        List of tuples (key, year, text, bibtex, url, slides, poster).
    generator.context['invited']:
        List of tuples (key, year, text, bibtex, url, slides, poster).
    generator.context['postdeadline']:
        List of tuples (key, year, text, bibtex, url, slides, poster).
    generator.context['patent']:
        List of tuples (key, year, text, bibtex, url, slides, poster).
    generator.context['book_chapter']:
        List of tuples (key, year, text, bibtex, url, slides, poster).
    generator.context['book']:
        List of tuples (key, year, text, bibtex, url, slides, poster).
    generator.context['journalNos']:
        Integer: number of journal publications
    generator.context['conferenceNos']:
        Integer: number of journal publications
    generator.context['invited']:
        Integer: number of invited conference publications
    generator.context['postdeadline']:
        List of tuples (key, year, text, bibtex, url, slides, poster).
        Integer: number of postdeadline publications
    generator.context['patent']:
        List of tuples (key, year, text, bibtex, url, slides, poster).
        Integer: number of patent publications
    generator.context['book_chapter']:
        Integer: number of book_chapter publications
    generator.context['book']:
        Integer: number of book publications
        See Readme.md for more details.
    """
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO
    try:
        from pybtex.database.input.bibtex import Parser
        from pybtex.database.output.bibtex import Writer
        from pybtex.database import BibliographyData, PybtexError
        from pybtex.backends import html
        from pybtex.style.formatting import unsrt
        from pybtex.style.formatting import BaseStyle, toplevel
        from pybtex.style.template import (
            join, words, field, optional, first_of,
            names, sentence, tag, optional_field, href
            )

    except ImportError:
        logger.warn('`pelican_bibtex` failed to load dependency `pybtex`')
        return
    bibtypes = ['journal', 'conference',  'patent', 'book_chapter',
                'book' ]

    html_backend = html.Backend()
    #html_backend.tags['strong'] = u'strong'

    class Naturestyle(unsrt.Style):
        def format_article(self, e):
            template = toplevel [
                self.format_names('author'),
                self.format_title(e, 'title'),
                join [tag('emph') [field('journal')], ' ',
                    tag('strong')[field('volume')], ', ', unsrt.pages,
                    ' (', field('year'), ')'],
                sentence(capfirst=False) [ optional_field('note') ],
                self.format_web_refs(e),
                ]
            return template.format_data(e)

        def format_web_refs(self, e):
        # based on urlbst output.web.refs
            return sentence(capfirst=False) [
                #optional [ self.format_url(e) ],
                optional [ self.format_eprint(e) ],
                optional [ self.format_pubmed(e) ],
                optional [ self.format_doi(e) ],
                ]
        def format_patent(self, e):
            template = toplevel [
                self.format_names('author'),
                self.format_title(e, 'title'),
                join [tag('emph') [field('number')], ' ', '(', field('year'), ')']
            ]
            return template.format_data(e)

    try:
        refs_file = metadata["publications_src"]
    except:
        sys.exit()
    try:
        bibdata_all = Parser().parse_file(refs_file)
    except PybtexError as e:
        logger.warn('`pelican_bibtex` failed to parse file %s: %s' % (
            refs_file,
            str(e)))
        return

    articles = []
    pdp = []
    invited = []
    conferences = []
    patents = []
    book_chapters = []
    books = []


    # format entries
    plain_style = Naturestyle()
    formatted_entries = plain_style.format_entries(bibdata_all.entries.values())

    for formatted_entry in formatted_entries:
        key = formatted_entry.key
        entry = bibdata_all.entries[key]
        year = entry.fields.get('year')
        # This shouldn't really stay in the field dict
        # but new versions of pybtex don't support pop
        pdf = entry.fields.get('pdf', None)
        slides = entry.fields.get('slides', None)
        poster = entry.fields.get('poster', None)
        url = entry.fields.get('url', None)
        if url is not None:
            pdf = url

        #render the bibtex string for the entry
        bib_buf = StringIO()
        bibdata_this = BibliographyData(entries={key: entry})
        Writer().write_stream(bibdata_this, bib_buf)
        text = formatted_entry.text.render(html_backend)
        #text = text.decode('ulatex').replace('{', '').replace('}', '')
        text = codecs.decode(text, 'ulatex').replace('{', '').replace('}', '')
        bibtype = entry.type
        out = (key, year, text, bib_buf.getvalue(), pdf, slides, poster)

        if bibtype in ['conference' , 'inproceedings']:
            if 'postdeadline' in entry.fields.get('keywords'):
                pdp.append(out)
            elif 'invited' in entry.fields.get('keywords'):
                invited.append(out)
            else:
                conferences.append(out)
        elif bibtype in ['article']:
            articles.append(out)
        elif bibtype in ['patent']:
            patents.append(out)
        elif bibtype in ['book_chapter']:
            book_chapters.append(out)
        elif bibtype in ['book']:
            books.append(out)



    generator.context['postdeadline'] = pdp
    generator.context['postdeadlineNos'] = len(pdp)
    generator.context['invited'] = invited
    generator.context['invitedNos'] = len(invited)
    generator.context['journal'] = articles
    generator.context['journalNos'] = len(articles)
    generator.context['patent'] = patents
    generator.context['patentNos'] = len(patents)
    generator.context['conference'] = conferences
    generator.context['conferenceNos'] = len(conferences)
    generator.context['book'] = books
    generator.context['bookNos'] = len(books)
    generator.context['book_chapter'] = book_chapters
    generator.context['book_chapterNos'] = len(book_chapters)


def register():
    signals.page_generator_context.connect(add_publications)
