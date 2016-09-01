# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from unittest import TestCase

import testdata

from wishlist.core import WishlistElement, WebDriver, Wishlist

# test WishlistElement price with 1,140.96

class WishlistElementTest(TestCase):
    def test_title_with_moneysign(self):
        with Wishlist.lifecycle() as w:
            #w.location("file://testdata/failed_wishilist_element_2.html")
            w.location("file:///vagrant/testdata/failed_wishilist_element_2.html")
            element = w.browser.find_element_by_tag_name("div")
            we = WishlistElement(element)
            #import re
            #pout.v(element.soup.find("div", id=re.compile("^itemPrice_")))
            #pout.v(element.text)
            pout.v(we.jsonable())






