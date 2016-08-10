"""
Pelican BibTeX
==============

A Pelican plugin that populates the context with a list of formatted
citations, loaded from a BibTeX file at a configurable path.

The use case for now is to generate a ``Publications'' page for academic
websites.
"""
# Author: Vlad Niculae <vlad@vene.ro>
# Modified by: Jochen Schroeder <cycomanic@gmail.com>
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
    metadata['journal_src']:
        local path to the BibTeX file for journal articles to read.
    metadata['conference_src']:
        local path to the BibTeX file for conference articles to read.
    metadata['invited_src']:
        local path to the BibTeX file for invited conference articles to read.
    metadata['patents_src']:
        local path to the BibTeX file for patents to read.
    metadata['bookchapter_src']:
        local path to the BibTeX file for book chapters to read.
    metadata['book_src']:
        local path to the BibTeX file for book read.


    Output
    ------
    generator.context['journal']:
        List of tuples (key, year, text, bibtex, pdf, slides, poster).
    generator.context['conference']:
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
    html_backend.tags['strong'] = u'strong'

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

    for bibtype in bibtypes:
        try:
            refs_file = metadata[bibtype+'_src']
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
        pdp = []
        invited = []

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
            text = text.decode('ulatex').replace('{', '').replace('}', '')

            if  bibtype is 'conference':
                logger.warn("conference bibtype")
                if 'postdeadline' in entry.fields.get('keywords'):
                    pdp.append((key,
                                 year,
                                 text,
                                 bib_buf.getvalue(),
                                 pdf,
                                 slides,
                                 poster))
                elif 'invited' in entry.fields.get('keywords'):
                    invited.append((key,
                                 year,
                                 text,
                                 bib_buf.getvalue(),
                                 pdf,
                                 slides,
                                 poster))
                else:
                    publications.append((key,
                                 year,
                                 text,
                                 bib_buf.getvalue(),
                                 pdf,
                                 slides,
                                 poster))
            else:
                publications.append((key,
                                 year,
                                 text,
                                 bib_buf.getvalue(),
                                 pdf,
                                 slides,
                                 poster))

        if bibtype is 'conference':
            generator.context['postdeadline'] = pdp
            generator.context['postdeadlineNos'] = len(pdp)
            generator.context['invited'] = invited
            generator.context['invitedNos'] = len(invited)
        generator.context[bibtype] = publications
        generator.context[bibtype+"Nos"] = len(publications)

def register():
    signals.page_generator_context.connect(add_publications)
