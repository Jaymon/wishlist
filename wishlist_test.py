# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from unittest import TestCase
import os
from contextlib import contextmanager

import testdata

from wishlist.core import WishlistElement, WebDriver, Wishlist


class WishlistElementTest(TestCase):

    @contextmanager
    def element_from_file(self, filename):
        basepath = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))
        path = os.path.join(basepath, "testdata", filename)

        with Wishlist.lifecycle() as w:
            #w.location("file://testdata/failed_wishilist_element_2.html")
            w.location("file://{}".format(path))
            element = w.browser.find_element_by_tag_name("div")
            we = WishlistElement(element)
            yield we

    def test_comment_with_moneysign(self):
        with Wishlist.lifecycle() as w:
            #w.location("file://testdata/failed_wishilist_element_2.html")
            w.location("file:///vagrant/testdata/failed_wishlist_element_2.html")
            element = w.browser.find_element_by_tag_name("div")
            we = WishlistElement(element)
            we_json = we.jsonable()
            self.assertTrue(we_json["comment"].startswith("$"))
            self.assertEqual(21.59, we_json["price"])


    def test_unavailable(self):
        with Wishlist.lifecycle() as w:
            #w.location("file://testdata/failed_wishilist_element_2.html")
            w.location("file:///vagrant/testdata/failed_wishlist_element_1.html")
            element = w.browser.find_element_by_tag_name("div")
            we = WishlistElement(element)
            we_json = we.jsonable()
            self.assertEqual("", we_json["title"])
            self.assertEqual(0.0, we_json["price"])


    def test_marketplace_price(self):
        with self.element_from_file("failed_wishlist_element_3.html") as we:
            we_json = we.jsonable()
            self.assertEqual(0.01, we_json["marketplace_price"])
            self.assertEqual(0.0, we_json["price"])
            #pout.v(we.jsonable())

    def test_marketplace_price_thousand(self):
        # test WishlistElement price with 1,140.96
        with self.element_from_file("failed_wishlist_element_5.html") as we:
            we_json = we.jsonable()
            #pout.v(we.jsonable())
            self.assertEqual(1424.05, we_json["marketplace_price"])


    def test_no_rating(self):
        with self.element_from_file("failed_wishlist_element_4.html") as we:
            we_json = we.jsonable()
            self.assertEqual(0.0, we_json["rating"])

