# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging

from .core import Wishlist, WishlistElement
from .exception import ParseError # external import convenience


__version__ = "0.5.3"


# get rid of "No handler found" warnings (cribbed from requests)
logging.getLogger(__name__).addHandler(logging.NullHandler())

