# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from brow.exception import ParseError


class RobotError(ParseError):
    """Raised when programatic access is detected"""
    pass

