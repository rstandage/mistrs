# __init__.py
__version__ = "0.2.0"

from .auth import get_credentials, get_headers
from .api import get, get_paginated, post, put, delete
from .data import create_xlsx, create_csv, read_xlsx, read_csv, list_ids, jprint, print_table, clean_mac, edittime, analyze_errors
from .net import subnet
