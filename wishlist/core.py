from __future__ import unicode_literals
import datetime
import re
import os
from contextlib import contextmanager

from .browser import Browser, ParseError, Soup
from .browser import NoSuchElementException, \
    WebDriverException, \
    NoSuchWindowException


class WishlistElement(Soup):
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
        el = self.soup.find("a", id=re.compile("^itemName_"))
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
        imgs = self.soup.find_all("img")
        for img in imgs:
            if "src" in img.attrs:
                if img.parent and img.parent.name == "a":
                    a = img.parent
                    if a.attrs["href"].startswith("/dp/"):
                        src = img.attrs["src"]
                        break

        if not src:
            for img in imgs:
                maybe_src = img.attrs.get("src", "")
                if "/images/I/" in maybe_src:
                    src = maybe_src
                    break

        return src

    @property
    def price(self):
        price = 0.0
        el = self.soup.find("span", id=re.compile("^itemPrice_"))
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
        el = self.soup.find("span", {"class": "itemUsedAndNewPrice"})
        if el and len(el.contents) > 0:
            price = float(el.contents[0].replace("$", "").replace(",", ""))
        return price

    @property
    def title(self):
        title = ""
        el = self.soup.find("a", id=re.compile("^itemName_"))
        if el and len(el.contents) > 0:
            title = el.contents[0].strip()

        else:
            el = self.soup.find("span", id=re.compile("^itemName_"))
            if el and len(el.contents) > 0:
                title = el.contents[0].strip()

        return title

    @property
    def comment(self):
        ret = ""
        el = self.soup.find("span", id=re.compile("^itemComment_"))
        if el and len(el.contents) > 0:
            ret = el.contents[0].strip()
        return ret

    @property
    def rating(self):
        stars = 0.0
        el = self.soup.find("a", {"class": "reviewStarsPopoverLink"})
        if el:
            el = el.find("span", {"class": "a-icon-alt"})
            if len(el.contents) > 0:
                stars = float(el.contents[0].strip().split()[0])
        return stars

    @property
    def author(self):
        author = ""
        el = self.soup.find("a", id=re.compile("^itemName_"))
        if el:
            author = el.parent.next_sibling
            if author:
                author = author.strip().replace("by ", "")
        return author

    @property
    def added(self):
        ret = None
        el = self.soup.find("div", id=re.compile("^itemAction_"))
        el = el.find("span", {"class": "a-size-small"})
        if el and len(el.contents) > 0:
            ret = el.contents[0].strip().replace("Added ", "")
            if ret:
                ret = datetime.datetime.strptime(ret, '%B %d, %Y')
        return ret

    @property
    def body(self):
        return self.soup.prettify()

    def __init__(self, element):
        self.soup = self.soupify(element)

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

    @classmethod
    @contextmanager
    def open(cls):
        with super(Wishlist, cls).open() as instance:
            instance.homepage() # we load homepage to force cookie loading
            instance.current_page = 0
            yield instance

    def get_items_from_body(self, body):
        """this will return the wishlist elements on the current page"""
        soup = self.soupify(body)
        html_items = soup.findAll("div", {"id": re.compile("^item_")})
        for i, html_item in enumerate(html_items):
            item = self.element_class(html_item)
            yield item

    def get_total_pages_from_body(self, body):
        """return the total number of pages of the wishlist

        body -- string -- the complete html page
        """
        page = 0
        soup = self.soupify(body)

        try:
            #el = soup.find("ul", id=re.compile("^itemAction_"))
            el = soup.find("ul", {"class": "a-pagination"})
            #el = el.find("li", {"class": "a-last"})
            els = el.findAll("li", {"class": re.compile("^a-")})
            #pout.v(len(els))
            #pout.v(els[-2])
            el = els[-2]
            if len(el.contents) and len(el.contents[0].contents):
                page = int(el.contents[0].contents[0].strip())

        except AttributeError:
            raise ParseError("Could not find pagination, is this a wishlist page?")

        return page

    def get_wishlist_url(self, name, page):
        base_url = "{}/gp/registry/wishlist/{}".format(self.host, name)
        if page > 1:
            base_url += "?page={}".format(page)
        return base_url

    def get(self, name, page=0):
        """return the items of the given wishlist name"""

        crash_count = 0
        page = page if page > 1 else 1
        self.current_page = page

        soup = None
        page_count = None

        while True:
            try:
                # https://www.amazon.com/gp/registry/wishlist/NAME
                self.location(self.get_wishlist_url(name, page))
                soup = self.soupify(self.body)

                if page_count is None:
                    page_count = self.get_total_pages_from_body(soup)

                for i, item in enumerate(self.get_items_from_body(soup)):
                    yield item

            finally:
                page += 1
                if page_count is None or page > page_count:
                    break

                self.current_page = page
                soup = None

    def homepage(self, **kwargs):
        """loads the amazon homepage, this forces cookies to load"""
        self.location(self.host, **kwargs)

