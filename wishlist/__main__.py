# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging
import sys
import argparse

from captain import echo, exit, ArgError
from captain.decorators import arg, args

from wishlist import __version__
from wishlist.core import Wishlist
from wishlist.exception import RobotError, ParseError


def main_auth(**kwargs):
    """Signin to amazon so you can access private wishlists"""
    with Wishlist.authenticate() as b:
        # If you access from another country, amazon might prompt to redirect to
        # country specific store, we don't want that
        if b.has_element("#redir-opt-out"):
            echo.out("Circumventing redirect")
            remember = b.element("#redir-opt-out")
            stay = b.element("#redir-stay-at-www")
            remember.click()
            stay.click()

        #button = b.element("a[data-nav-role=signin]")
        button = b.element("a[id=nav-link-accountList]")
        echo.out("Clicking sign in button")
        button.click()

        # now put in your creds
        if b.has_element("#continue"):
            # I'd never seen a flow like this before, it first prompts for email
            # and then moves onto password
            email = b.element("#ap_email")
            submit = b.element("#continue")
            echo.out("Found alternate signin form")
            email_in = echo.prompt("Amazon email address")
            email.send_keys(email_in)
            submit.click()

            password = b.element("#ap_password")
            submit = b.element("#signInSubmit")
            password_in = echo.prompt("Amazon password")
            password.send_keys(password_in)
            echo.out("Signing in")
            submit.click()

        else:
            # typical flow, email/password are on the same page
            email = b.element("#ap_email")
            password = b.element("#ap_password")
            submit = b.element("#signInSubmit")
            echo.out("Found signin form")
            email_in = echo.prompt("Amazon email address")
            password_in = echo.prompt("Amazon password")

            email.send_keys(email_in)
            password.send_keys(password_in)
            echo.out("Signing in")
            submit.click()

        # for 2-factor, wait for this element
        code = b.element("#auth-mfa-otpcode", 5)
        if code:
            echo.out("2-Factor authentication is on, you should be receiving a text")
            submit = b.element("#auth-signin-button")
            remember = b.element("#auth-mfa-remember-device")
            remember.click()
            authcode = echo.prompt("2-Factor authcode")
            code.send_keys(authcode)
            submit.click()

        # original: https://www.amazon.com/ref=gw_sgn_ib/853-0204854-22247543
        # 12-1-2017: https://www.amazon.com/?ref_=nav_ya_signin&
        echo.out("Redirect url was: {}", b.url)
        if "=gw_sgn_ib" in b.url or "=nav_ya_signin" in b.url:
            echo.out("Success, you are now signed in")
            b.cookies.dump()


@arg('name', nargs=1, help="the name of the wishlist, amazon.com/gp/registry/wishlist/NAME")
def main_dump(name, **kwargs):
    """This is really here just to test that I can parse a wishlist completely and
    to demonstrate (by looking at the code) how to iterate through a list"""
    name = name[0]
    #pout.v(name, start_page, stop_page, kwargs)
    #pout.x()

    w = Wishlist(name)
    i = 1
    for i, item in enumerate(w, 1):
        try:
            item_json = item.jsonable()
            echo.out("{}. {} is ${:.2f}", i, item_json["title"], item_json["price"])

        except RobotError:
            raise

        except ParseError as e:
            echo.err("{}. Failed!", i)
            echo.err(e.body)
            echo.exception(e)

    echo.out("Done with wishlist, {} total items", i)


def console():
    exit(__name__)

if __name__ == "__main__":
    console()

