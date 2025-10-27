# __init__.py
__version__ = "0.1.8"

from .auth import get_credentials, get_headers
from .api import get, get_paginated, post, put, delete, debug_get, debug_put, debug_delete, debug_post
from .data import create_xlsx, create_csv, read_xlsx, read_csv, list_ids, jprint, print_table, clean_mac, edittime, analyze_errors
from .net import subnet