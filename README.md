# Wishlist

Python library to grab your Amazon wishlist so you can mess with it programmatically.


## Dependencies

Before you can use this you have to have a few things installed, on Ubuntu, you can run these commands:

    $ sudo su
    $ apt-get install --no-install-recommends firefox
    $ apt-get install --no-install-recommends xvfb

To install the Firefox web browser and the X11 virtual file buffer.


## 1 minute gettings started

Is your wishlist private? Then you will need to authenticate on the command line:

    $ wishlist auth

This will prompt you to signin and will even handle 2-factor authentication, after you signin your cookies will be saved so you can run now access your Amazon wishlist.

You can check access to your wishlist on the command line by running:

    $ wishlist dump NAME

where `NAME` is the part of a url like `https://www.amazon.com/gp/registry/wishlist/NAME`, so, if your wishlist was found at: `https://www.amazon.com/gp/registry/wishlist/9YDNFG31NSSRL` then you would run:

    $ wishlist dump 9YDNFG31NSSRL

If you wanted to do something in another python script, you can do:


```python
from wishlist.core import Wishlist, ParseError

name = "9YDNFG31NSSRL"
with Wishlist.lifecycle() as w:
    for item in w.get(name):
        # do something with the item
        pass
```

You can check the `wishlist.core.WishlistElement` code to understand the structure of each wishlist item.

