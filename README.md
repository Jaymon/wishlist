# Wishlist

Python library to grab your Amazon wishlist so you can mess with it programmatically.


## Dependencies

### What do I need if I have a private wishlist?

Wishlist depends on [Brow](https://github.com/Jaymon/brow) in order to login from the command line (including 2 factor if enabled), and Brow depends on Selenium and Firefox to be installed, so you'll need to read [Brow's README](https://github.com/Jaymon/brow/blob/master/README.md) if you need help installing those on Linux.


### What do I need if I have a public wishlist?

Nothing special, `pip install wishlist` should cover you, jump down to "Commandline wishlist access" and get started.

## 1 minute gettings started


### Authentication for private lists

Is your wishlist private? Then you will need to authenticate on the command line:

    $ wishlist auth

This will prompt you to signin and will even handle 2-factor authentication, after you signin your cookies will be saved so you can run now access your Amazon wishlist.


### Commandline wishlist access

You can check access to your wishlist on the command line by running:

    $ wishlist dump NAME

where `NAME` is the part of a url like `https://www.amazon.com/gp/registry/wishlist/NAME`, so, if your wishlist was found at: `https://www.amazon.com/gp/registry/wishlist/9YDNFG31NSSRL` then you would run:

    $ wishlist dump 9YDNFG31NSSRL


### Programmatic wishlist access

If you wanted to do something in another python script, you can do:

```python
from wishlist.core import Wishlist

name = "9YDNFG31NSSRL"
w = Wishlist(name)
for item in w:
    print(w.jsonable())
```

You can check the [wishlist.core.WishlistElement](https://github.com/Jaymon/wishlist/blob/master/wishlist/core.py) code to understand the structure of each wishlist item.


## Installation

use pip:

    $ pip install wishlist

Or be bleeding edge:

    $ pip install "git+https://github.com/Jaymon/wishlist#egg=wishlist"


## Other things

* Why are you using Firefox for logging in? Why not Chrome? I tried to get it to work in Chrome but headless Chrome doesn't have all the features needed to work out authentication on the command line.

* This only works on **amazon.com**, because I only use **amazon.com**, if you want it to use a different Amazon site, I take pull requests :)

* Would you rather use php? [There's a library for that](https://github.com/doitlikejustin/amazon-wish-lister) ([also related](https://shkspr.mobi/blog/2015/11/an-api-for-amazon-wishlists/)).

* [Amazon's advertising api](http://docs.aws.amazon.com/AWSECommerceService/latest/DG/Welcome.html), this is where the officially supported wishlist api used to live.

