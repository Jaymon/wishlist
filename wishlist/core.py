from __future__ import unicode_literals
import os
import tempfile
import pickle
import time
import re
from contextlib import contextmanager
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from pyvirtualdisplay import Display
from bs4 import BeautifulSoup

from selenium.webdriver.firefox.webdriver import WebDriver as BaseWebDriver
#from selenium.webdriver.firefox.webelement import FirefoxWebElement as BaseWebElement # selenium 3.0
from selenium.webdriver.remote.webelement import WebElement as BaseWebElement # selenium <3.0


class WebElement(BaseWebElement):
    @property
    def body(self):
        # http://stackoverflow.com/a/22227980/5006
        return self.get_attribute('innerHTML')

    @property
    def soup(self):
        """Return a beautiful soup object with the contents of this element"""
        soup = getattr(self, "_soup", None)
        if soup is None:
            soup = BeautifulSoup(self.body, "html.parser")
            self._soup = soup
        return soup


class WebDriver(BaseWebDriver):
    _web_element_cls = WebElement # selenium 3.0

    def create_web_element(self, element_id):
        # TODO -- remove when upgrading to selenium 3.0
        return WebElement(self, element_id, w3c=self.w3c)


class ParseError(RuntimeError):
    def __init__(self, body, e):
        self.body - body
        self.error = e
        super(ParseError, self).__init__(e.message)


class Cookies(object):

    @property
    def directory(self):
        directory = getattr(self, "_directory", None)
        if directory is None:
            directory = os.environ.get("WISHLIST_CACHE_DIR", "")
            if directory:
                directory = os.path.abspath(os.path.expanduser(directory))
            else:
                directory = tempfile.gettempdir()

            self._directory = directory
        return directory

    @property
    def path(self):
        cookies_d = self.directory
        cookies_f = os.path.join(cookies_d, "{}.txt".format(self.domain))
        return cookies_f

    def __iter__(self):
        cookies_f = self.path
        if os.path.isfile(cookies_f):
            with open(cookies_f, "rb") as f:
                cookies = pickle.load(f)

            for cookie in cookies:
                yield cookie

    def save(self, cookies):
        """save the cookies in browser"""
        cookies_f = self.path
        with open(cookies_f, "w+b") as f:
            pickle.dump(cookies, f)

    def __init__(self, domain):
        """
        browser -- selenium web driver -- usually Firefox or Chrome
        """
        self.domain = domain



class WishlistElement(object):
    @property
    def uuid(self):
        m = re.search("/dp/([^/]+)", self.url)
        return m.group(1) if m else ""

    @property
    def url(self):
        href = ""
        for a in self.element.soup.find_all("a"):
            if "href" in a.attrs:
                if a.attrs["href"].startswith("/dp/"):
                    href = "https://www.amazon.com{}".format(a.attrs["href"])
                    break
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
        if el:
            price = float(el.contents[0].strip()[1:].split()[0].replace(",", ""))
        return price

    @property
    def title(self):
        title = ""
        el = self.element.soup.find("a", id=re.compile("^itemName_"))
        if el:
            title = el.contents[0].strip()
        return title

    @property
    def comment(self):
        ret = ""
        el = self.element.soup.find("span", id=re.compile("^itemComment_"))
        if el:
            ret = el.contents[0].strip()
        return ret

    def __init__(self, element):
        self.element = element

    def jsonable(self):
        lines = self.element.text.splitlines()

        json_item = {}
        json_item["title"] = self.title
        json_item["image"] = self.image
        json_item["uuid"] = self.uuid
        json_item["url"] = self.url
        json_item["price"] = self.price
        json_item["comment"] = self.comment

        for j, line in enumerate(lines[1:], 1):
            if line.startswith("Added "):
                json_item["added"] = line.replace("Added ", "")

            elif line.startswith("by "):
                json_item["author"] = line.replace("by ", "")

            else:
                if "Used & New" in line:
                    json_item["marketplace"] = line

        return json_item


class Wishlist(object):

    @property
    def body(self):
        # http://stackoverflow.com/a/7866938/5006
        return self.browser.page_source

    @property
    def current_url(self):
        # http://stackoverflow.com/questions/15985339/how-do-i-get-current-url-in-selenium-webdriver-2-python
        return self.browser.current_url

    @property
    def browser(self):
        """wrapper around the browser in case we want to switch from Firefox"""
        browser = getattr(self, "_browser", None)
        if browser is None:
            # http://coreygoldberg.blogspot.com/2011/06/python-headless-selenium-webdriver.html
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()
            browser = self.firefox
            #browser._web_element_cls = WebElement
            self._browser = browser

        return browser

    @property
    def firefox(self):
        profile = webdriver.FirefoxProfile()
        #firefox = webdriver.Firefox(firefox_profile=profile)
        firefox = WebDriver(firefox_profile=profile)
        return firefox

    @classmethod
    @contextmanager
    def lifecycle(cls):
        try:
            instance = cls()
            yield instance

        finally:
            instance.close()

    def get(self, name):
        """return the items of the given wishlist name"""

        # https://www.amazon.com/gp/registry/wishlist/NAME
        base_url = "https://www.amazon.com/gp/registry/wishlist/{}".format(name)
        self.location(base_url)
        driver = self.browser

        current_item = None # for debugging
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
                    current_item = html_item
                    item = WishlistElement(html_item)
                    yield item.jsonable()

        except NoSuchElementException as e:
            if current_item:
                pout.v(current_item.body)
            raise ParseError(self.body, e)

        except Exception as e:
            if current_item:
                pout.v(current_item.body)
            pout.v(e)
            raise

    def homepage(self, **kwargs):
        """loads the amazon homepage, this forces cookies to load"""
        self.location("https://www.amazon.com", **kwargs)

    def location(self, url, ignore_cookies=False):
        driver = self.browser
        driver.get(url)
        url_bits = urlparse.urlparse(url)
        domain = url_bits.hostname
        self.domain = domain

        if not ignore_cookies:
            if domain and (domain not in self.domains):
                self.domains[domain] = domain
                cookies = Cookies(domain)
                for cookie in cookies:
                    driver.add_cookie(cookie)

    def element(self, css_selector):
        return self.browser.find_element_by_css_selector(css_selector)

    def wait_for_element(self, css_selector, seconds):
        elem = None
        driver = self.browser
        for count in range(seconds):
            elem = driver.find_element_by_css_selector(css_selector)
            if elem:
                break
            else:
                time.sleep(1)

        return elem


#     def open(self):
#         ret = True
#         driver = self.browser
# 
#         driver.get("https://www.amazon.com")
#         cookies = Cookies()
# 
#         button = driver.find_element_by_css_selector("#a-autoid-0-announce")
#         if button:
#             button.click()
#             if "/ref=gw_sgn_ib/" in driver.current_url:
#                 #https://www.amazon.com/ref=gw_sgn_ib/853-0204854-22247543
#                 ret = False
#                 self.is_authed = True
# 
#         return ret

    def __init__(self):
        self.is_authed = False
        self.domains = {}

    def save(self):
        """save the browser session for the given domain"""
        cookie = Cookies(self.domain)
        cookie.save(self.browser.get_cookies())

    def close(self):
        self.browser.close()
        self.display.stop()
    
