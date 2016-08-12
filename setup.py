import pelican_bibtex
from distutils.core import setup

CLASSIFIERS = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: Public Domain
Programming Language :: Python
Programming Language :: Python :: 3
Topic :: Software Development
Operating System :: POSIX
Operating System :: Unix

"""

LONG_DESCRIPTION = """\
Requirements
============

pelican\_perpagepublications requires pybtex.

Create scientific publications list for different publication type BibTeX databases given in the page or post metadata. This plugin is an extension of the Pelican BibTex plugni by Vlad Vene.
"""

setup(
    name='pelican_perpagepublications',
    description='Create per page/post publication lists with BibTeX in Pelican',
    long_description=LONG_DESCRIPTION,
    version=pelican_bibtex.__version__,
    author='Jochen Schroeder',
    author_email='jochen.schroeder@jochenschroeder.com',
    url='https://pypi.python.org/pypi/pelican_perpagepublications',
    py_modules=['pelican_perpagepublications'],
    classifiers=[_f for _f in CLASSIFIERS.split('\n') if _f]
)
