# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import pathlib

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(__file__, "..", "..")
    )
)

import sadrive.helpers.utils as _u
_u.get_config_dir = lambda: pathlib.Path(__file__).parent / "fake_conf"

project = 'sadrive'
copyright = '2025, jsmaskeen'
author = 'jsmaskeen'
release = '2.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_click.ext',
    'sphinx.ext.autosummary'
]
autosummary_generate = True
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
