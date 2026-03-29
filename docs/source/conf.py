# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import datetime
import os
import shutil
import sys
from pathlib import Path

from pygments.lexers.python import PythonLexer
from sphinx.highlighting import lexers

sys.path.insert(0, os.path.abspath("../../src"))
sys.path.insert(0, os.path.abspath("../../examples"))


def _sync_example_notebooks() -> None:
    """Keep docs notebook copies in sync for direct sphinx-build invocations."""
    repo_root = Path(__file__).resolve().parents[2]
    source_dir = Path(__file__).resolve().parent / "examples"
    notebook_names = ["quickstart.ipynb", "using_a_custom_teambuilder.ipynb"]

    for notebook_name in notebook_names:
        src = repo_root / "examples" / notebook_name
        dst = source_dir / notebook_name
        if src.exists() and (not dst.exists() or src.read_bytes() != dst.read_bytes()):
            shutil.copy2(src, dst)


_sync_example_notebooks()

# -- Project information -----------------------------------------------------

project = "Poke-env"
copyright = "%d, Haris Sahovic" % datetime.datetime.now().year
author = "Haris Sahovic"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx", "nbsphinx"]

# Notebook code cells often declare the "ipython3" lexer. Map it to Python so
# strict sphinx builds with -W do not fail on unknown lexer warnings.
lexers["ipython3"] = PythonLexer()

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

master_doc = "index"
