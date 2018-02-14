# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from unittest import TestCase
import os
from contextlib import contextmanager
import codecs
import logging
import sys

import testdata

from wishlist.core import WishlistElement, Wishlist
from wishlist.exception import ParseError


# configure root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler(stream=sys.stderr)
log_formatter = logging.Formatter('[%(levelname)s] %(message)s')
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)


class BaseTestCase(TestCase):
    def get_body(self, filename):
        basepath = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))
        path = os.path.join(basepath, "testdata", filename)
        with codecs.open(path, encoding='utf-8', mode='r') as f:
        #with open(path) as f:
            body = f.read()
        return body


class WishlistElementTest(BaseTestCase):
    def get_item(self, filename):
        body = self.get_body(filename)
        we = WishlistElement(body)
        return we

    def test_unavailable(self):
        we = self.get_item("failed_wishlist_element_1.html")
        we_json = we.jsonable()
        self.assertTrue(bool(we_json["title"]))
        self.assertEqual(0.0, we_json["price"])

    def test_comment_with_moneysign(self):
        we = self.get_item("failed_wishlist_element_2.html")
        self.assertTrue(we.comment.startswith("$"))
        self.assertEqual(21.59, we.price)

    def test_marketplace_price(self):
        we = self.get_item("failed_wishlist_element_3.html")
        self.assertEqual(0.01, we.marketplace_price)
        self.assertEqual(0.0, we.price)

    def test_no_rating(self):
        we = self.get_item("failed_wishlist_element_4.html")
        self.assertEqual(0.0, we.rating)

    def test_marketplace_price_thousand(self):
        # test WishlistElement price with 1,140.96
        we = self.get_item("failed_wishlist_element_5.html")
        self.assertEqual(1424.05, we.price)

    def test_unavailable_2(self):
        """test an item that has no url"""
        we = self.get_item("failed_wishlist_element_6.html")
        we_json = we.jsonable()
        self.assertTrue(bool(we_json["title"]))
        self.assertFalse(bool(we_json["url"]))
        self.assertTrue(bool(we_json["image"]))

    def test_external(self):
        """Make sure an item added from an external source is parsed correctly"""
        we = self.get_item("failed_wishlist_element_7.html")
        we_json = we.jsonable()
        self.assertTrue(bool(we_json["uuid"]))
        self.assertTrue(bool(we_json["url"]))

    def test_unavailable_3(self):
        """Make sure an unavailable item's asin value is returned as uuid"""
        we = self.get_item("failed_wishlist_element_8.html")
        we_json = we.jsonable()
        self.assertTrue(bool(we_json["uuid"]))

    def test_quantity(self):
        we = self.get_item("failed_wishlist_element_1.html")
        self.assertEqual((1, 0), we.quantity)
        self.assertEqual(1, we.wanted_count)
        self.assertEqual(0, we.has_count)

    def test_is_digital(self):
        we = self.get_item("failed_wishlist_element_2.html")
        self.assertTrue(we.is_digital())

        we = self.get_item("failed_wishlist_element_1.html")
        self.assertFalse(we.is_digital())

    def test_is_digital_2(self):
        we = self.get_item("digital_element_1.html")
        self.assertTrue(we.is_digital())

    def test_range(self):
        we = self.get_item("ranged_wishlist_element_1.html")
        self.assertEqual(18.95, we.price)
        self.assertFalse(we.is_amazon())

    def test_external(self):
        we = self.get_item("external_element_1.html")
        self.assertEqual(159.99, we.price)
        #pout.v(we.jsonable())

