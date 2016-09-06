import logging

from .core import Wishlist, WishlistElement, ParseError


__version__ = "0.0.6"


# get rid of "No handler found" warnings (cribbed from requests)
logging.getLogger(__name__).addHandler(logging.NullHandler())

