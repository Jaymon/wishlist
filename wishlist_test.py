# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
from unittest import TestCase
import os
from contextlib import contextmanager
import codecs
import datetime

import testdata
from bs4 import BeautifulSoup

from wishlist.core import WishlistElement, Wishlist
from wishlist.exception import ParseError
from brow.utils import Soup


testdata.basic_logging()


class BaseTestCase(TestCase):
    def get_body(self, filename):
        return testdata.get_contents(filename)

    def get_soup(self, filename, parser=""):
        body = self.get_body(filename)
        soup = Soup(body, parser)
        return soup


class WishlistElementTest(BaseTestCase):

    def get_item(self, filename):
        body = self.get_body(filename)
        we = WishlistElement(body)
        return we

    def get_items(self, filename, name="WISHLIST_NAME"):
        soup = self.get_soup(filename)
        w = Wishlist(name)
        items = list(w.get_items(soup, w.get_wishlist_url()))
        return items

    def test_zero_price(self):
        we = self.get_item("zero-price-1.html")
        we.price

        items = self.get_items("zero-price-2.html")
#         pout.v(len(items))
#         for item in items:
#             pout.v(item.title, item.price)

        with self.assertRaises(ParseError):
            we = items[2]
            we.price

        with self.assertRaises(ParseError):
            we = items[4]
            we.price

    def test_redesign_2018_06(self):
        """In mid June Amazon updated the html and it had a bug or something in it
        and so my wishlist didn't parse for a few days and then it was magically
        fixed, but I managed to grab the first page so I could figure out what was
        wrong and it turned out I didn't need to change anything except allow
        Brow to use different parsers because the more liberal non built-in parsers
        were both able to parse the html"""
        #body = self.get_body("redesign-2018-06")
        soup = self.get_soup("html-2018-06", "html.parser")
        w = Wishlist("WISHLISTNAME")
        items = list(w.get_items(soup, w.get_wishlist_url()))
        self.assertEqual(0, len(items))

        soup = self.get_soup("html-2018-06", "lxml")
        w = Wishlist("WISHLISTNAME")
        items = list(w.get_items(soup, w.get_wishlist_url()))
        self.assertEqual(10, len(items))

        soup = self.get_soup("html-2018-06", "html5lib")
        w = Wishlist("WISHLISTNAME")
        items = list(w.get_items(soup, w.get_wishlist_url()))
        self.assertEqual(10, len(items))

    def test_permalinks(self):
        we = self.get_item("permalinks.html")
        we._page_url = "{}/hz/wishlist/ls/XXX?filter=DEFAULT&lek=xxxxx-xxxx&sort=default&type=wishlist".format(
            we.host
        )

        self.assertTrue("lv_ov_lig_dp_it" in we.url)
        self.assertEqual("B00A6QRKU6", we.uuid)
        self.assertTrue("#itemMain_IU2UIE3ANI9WG" in we.page_url)

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

    def test_external_2(self):
        we = self.get_item("external_element_1.html")
        self.assertEqual(159.99, we.price)

    def test_external_3(self):
        we1 = self.get_item("external_element_1.html")
        we2 = self.get_item("external_element_2.html")
        self.assertEqual(we1.uuid, we2.uuid)

    def test_unavailable_3(self):
        """Make sure an unavailable item's asin value is returned as uuid"""
        we = self.get_item("failed_wishlist_element_8.html")
        we_json = we.jsonable()
        self.assertTrue(bool(we_json["uuid"]))

    def test_unavailable_4(self):
        we = self.get_item("unavailable_element_1.html")
        self.assertEqual(0.0, we.price)
        self.assertFalse(we.in_stock())

    def test_quantity_1(self):
        we = self.get_item("failed_wishlist_element_1.html")
        self.assertEqual((1, 0), we.quantity)
        self.assertEqual(1, we.wanted_count)
        self.assertEqual(0, we.has_count)

    def test_quantity_2(self):
        we = self.get_item("unavailable_element_3.html")
        self.assertEqual((1, 0), we.quantity)

        we = self.get_item("unavailable_element_4.html")
        self.assertEqual((0, 0), we.quantity)

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

    def test_failing_added_date(self):
        """On march 31, 2018 the date added started failing"""
        we = self.get_item("failed_wishlist_element_9.html")
        dt = datetime.datetime(2018, 3, 30)
        self.assertEqual(dt, we.added)

        d = we.jsonable()
        self.assertTrue("added" in d)

