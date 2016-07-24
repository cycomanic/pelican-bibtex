"""
Pelican BibTeX
==============

A Pelican plugin that populates the context with a list of formatted
citations, loaded from a BibTeX file at a configurable path.

The use case for now is to generate a ``Publications'' page for academic
websites.
"""
# Author: Vlad Niculae <vlad@vene.ro>
# Unlicense (see UNLICENSE for details)

import logging
import codecs
import latexcodec
logger = logging.getLogger(__name__)

from pelican import signals

__version__ = '0.2.1'


def add_publications(generator, metadata):
    """
    Populates context with a list of BibTeX publications.

    Configuration
    -------------
    generator.metadata['journal_src']:
        local path to the BibTeX file for journal articles to read.
    generator.metadata['conference_src']:
        local path to the BibTeX file for conference articles to read.
    generator.metadata['invited_src']:
        local path to the BibTeX file for invited conference articles to read.
    generator.metadata['patents_src']:
        local path to the BibTeX file for patents to read.
    generator.metadata['bookchapter_src']:
        local path to the BibTeX file for book chapters to read.
    generator.metadata['book_src']:
        local path to the BibTeX file for book read.


    Output
    ------
    generator.context['journals']:
        List of tuples (key, year, text, bibtex, pdf, slides, poster).
    generator.context['conferences']:
        List of tuples (key, year, text, bibtex, pdf, slides, poster).
    generator.context['invited']:
        List of tuples (key, year, text, bibtex, pdf, slides, poster).
    generator.context['patent']:
        List of tuples (key, year, text, bibtex, pdf, slides, poster).
    generator.context['book_chapter']:
        List of tuples (key, year, text, bibtex, pdf, slides, poster).
    generator.context['book']:
        List of tuples (key, year, text, bibtex, pdf, slides, poster).
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
        from pybtex.style.formatting import plain
    except ImportError:
        logger.warn('`pelican_bibtex` failed to load dependency `pybtex`')
        return
    bibtypes = ['journal', 'conference', 'invited', 'patent', 'book_chapter', 'book']
    for bibtype in bibtypes:
        try:
            refs_file = generator.metadata[bibtype+'_src']
        except:
            continue
        try:
            bibdata_all = Parser().parse_file(refs_file)
        except PybtexError as e:
            logger.warn('`pelican_bibtex` failed to parse file %s: %s' % (
                refs_file,
                str(e)))
            return

        publications = []

        # format entries
        plain_style = plain.Style()
        html_backend = html.Backend()
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

            #render the bibtex string for the entry
            bib_buf = StringIO()
            bibdata_this = BibliographyData(entries={key: entry})
            Writer().write_stream(bibdata_this, bib_buf)
            text = formatted_entry.text.render(html_backend)

            publications.append((key,
                                 year,
                                 text,
                                 bib_buf.getvalue(),
                                 pdf,
                                 slides,
                                 poster))

        generator.context[bibtype] = publications


def register():
    signals.page_generator_context.connect(add_publications)
