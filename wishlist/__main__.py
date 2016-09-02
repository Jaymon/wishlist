
from captain import echo, exit, ArgError
from captain.decorators import arg, args

from wishlist import __version__
from wishlist.core import Wishlist

def main_auth():
    """Signin to amazon so you can access private wishlists"""
    with Wishlist.lifecycle() as w:
        echo.out("Requesting amazon.com")
        w.homepage(ignore_cookies=True)

        button = w.element("#a-autoid-0-announce")
        echo.out("Clicking sign in button")
        button.click()

        # now put in your creds
        email = w.element("#ap_email")
        password = w.element("#ap_password")
        submit = w.element("#signInSubmit")
        if email and password and submit:
            echo.out("Found sign in form")
            email_in = echo.prompt("Amazon email address")
            password_in = echo.prompt("Amazon password")

        email.send_keys(email_in)
        password.send_keys(password_in)
        echo.out("Signing in")
        submit.click()

        # for 2-factor, wait for this element
        code = w.wait_for_element("#auth-mfa-otpcode", 5)
        if code:
            echo.out("2-Factor authentication is on, you should be receiving a text")
            submit = w.element("#auth-signin-button")
            remember = w.element("#auth-mfa-remember-device")
            remember.click()
            authcode = echo.prompt("2-Factor authcode: ")
            code.send_keys(authcode)
            submit.click()

        #https://www.amazon.com/ref=gw_sgn_ib/853-0204854-22247543
        if "/ref=gw_sgn_ib/" in w.current_url:
            echo.out("Success, you are now signed in")
            w.save()


@arg('name', help="the name of the wishlist, amazon.com/gp/registry/wishlist/NAME")
def main_dump(name):
    with Wishlist.lifecycle() as w:
        w.homepage() # we load homepage to force cookies
        current_url = ""

        # https://www.amazon.com/gp/registry/wishlist/1XDNMA31SYSRC
        for item in w.get(name):
            if current_url:
                if w.current_url != current_url:
                    current_url = w.current_url
                    echo.err(current_url)
            else:
                current_url = w.current_url
                echo.err(current_url)

            pout.v(item)


if __name__ == "__main__":
    exit()

