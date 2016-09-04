from __future__ import unicode_literals
import datetime
import re
import os
from contextlib import contextmanager

from .browser import Browser, ParseError, NoSuchElementException


class WishlistElement(object):
    """Wishlist.get() returns an instance of this object"""
    @property
    def host(self):
        return os.environ.get("WISHLIST_HOST", "https://www.amazon.com")

    @property
    def uuid(self):
        m = re.search("/dp/([^/]+)", self.url)
        return m.group(1) if m else ""

    @property
    def url(self):
        href = ""
        el = self.element.soup.find("a", id=re.compile("^itemName_"))
        if el and ("href" in el.attrs):
            m = re.search("/dp/([^/]+)", el.attrs["href"])
            if m:
                href = "{}/dp/{}/".format(self.host, m.group(1))
                tag = os.environ.get("WISHLIST_REFERRER", "marcyescom-20")
                if tag:
                    href += "?tag={}".format(tag)

        return href

    @property
    def image(self):
        src = ""
        for img in self.element.soup.find_all("img"):
            if "src" in img.attrs:
                if img.parent and img.parent.name == "a":
                    a = img.parent
                    if a.attrs["href"].startswith("/dp/"):
                        src = img.attrs["src"]
                        break
        return src

    @property
    def price(self):
        price = 0.0
        el = self.element.soup.find("span", id=re.compile("^itemPrice_"))
        if el and len(el.contents) > 0:
            try:
                price_str = el.contents[0].strip()
                if price_str:
                    price = float(price_str[1:].split()[0].replace(",", ""))
            except (ValueError, IndexError):
                price = 0.0

        return price

    @property
    def marketplace_price(self):
        price = 0.0
        el = self.element.soup.find("span", {"class": "itemUsedAndNewPrice"})
        if el and len(el.contents) > 0:
            price = float(el.contents[0].replace("$", "").replace(",", ""))
        return price

    @property
    def title(self):
        title = ""
        el = self.element.soup.find("a", id=re.compile("^itemName_"))
        if el and len(el.contents) > 0:
            title = el.contents[0].strip()
        return title

    @property
    def comment(self):
        ret = ""
        el = self.element.soup.find("span", id=re.compile("^itemComment_"))
        if el and len(el.contents) > 0:
            ret = el.contents[0].strip()
        return ret

    @property
    def rating(self):
        stars = 0.0
        el = self.element.soup.find("a", {"class": "reviewStarsPopoverLink"})
        if el:
            el = el.find("span", {"class": "a-icon-alt"})
            if len(el.contents) > 0:
                stars = float(el.contents[0].strip().split()[0])
        return stars

    @property
    def author(self):
        author = ""
        el = self.element.soup.find("a", id=re.compile("^itemName_"))
        if el:
            author = el.parent.next_sibling
            if author:
                author = author.strip().replace("by ", "")
        return author

    @property
    def added(self):
        ret = None
        el = self.element.soup.find("div", id=re.compile("^itemAction_"))
        el = el.find("span", {"class": "a-size-small"})
        if el and len(el.contents) > 0:
            ret = el.contents[0].strip().replace("Added ", "")
            if ret:
                ret = datetime.datetime.strptime(ret, '%B %d, %Y')
        return ret

    def __init__(self, element):
        self.element = element

    def jsonable(self):
        json_item = {}
        json_item["title"] = self.title
        json_item["image"] = self.image
        json_item["uuid"] = self.uuid
        json_item["url"] = self.url
        json_item["price"] = self.price
        json_item["marketplace_price"] = self.marketplace_price
        json_item["comment"] = self.comment
        json_item["author"] = self.author
        json_item["added"] = self.added.strftime('%B %d, %Y')
        json_item["rating"] = self.rating
        return json_item


class Wishlist(Browser):
    """Wrapper that is specifically designed for getting amazon wishlists"""

    element_class = WishlistElement

    @property
    def host(self):
        return os.environ.get("WISHLIST_HOST", "https://www.amazon.com")

    @classmethod
    @contextmanager
    def lifecycle(cls):
        with super(Wishlist, cls).lifecycle() as instance:
            instance.homepage() # we load homepage to force cookie loading
            yield instance

    def get(self, name):
        """return the items of the given wishlist name"""

        # https://www.amazon.com/gp/registry/wishlist/NAME
        base_url = "{}/gp/registry/wishlist/{}".format(self.host, name)
        self.location(base_url)
        driver = self.browser
        html_item = None

        try:
            # http://stackoverflow.com/questions/1604471/how-can-i-find-an-element-by-css-class-with-xpath
            xpath = "//ul[@class=\"a-pagination\"]"
            html_pagination = driver.find_element_by_xpath(xpath)
            page_count = int(html_pagination.text.splitlines()[-2])

            for page in range(1, page_count + 1):
                if page > 1:
                    self.location(base_url + "?page={}".format(page))

                html_items = driver.find_elements_by_xpath("//div[starts-with(@id, 'item_')]")
                for i, html_item in enumerate(html_items):
                    item = self.element_class(html_item)
                    yield item

        except (NoSuchElementException, ParseError) as e:
            raise ParseError(html_item.body, e)

    def homepage(self, **kwargs):
        """loads the amazon homepage, this forces cookies to load"""
        self.location(self.host, **kwargs)

