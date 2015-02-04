#!/usr/bin/python2.7
# -*- coding: UTF8 -*-

"""
Copyright: Eesti Vabariigi Valimiskomisjon
(Estonian National Electoral Committee), www.vvk.ee
Written in 2004-2013 by Cybernetica AS, www.cyber.ee

This work is licensed under the Creative Commons
Attribution-NonCommercial-NoDerivs 3.0 Unported License.
To view a copy of this license, visit
http://creativecommons.org/licenses/by-nc-nd/3.0/.
"""

import time
from election import Election
from evlog import AppLog


class Purger:

    """Common base class for purging keys or values from the registry."""

    def __init__(self, description, key):
        AppLog().set_app("purge.py")
        self._desc = description
        self._key = key

    def work(self, check_fn, purge_fn):
        reg = Election().get_root_reg()
        runtime = int(time.time())
        AppLog().log("Purging %ss as of %s: START" % (self._desc,
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(runtime))))

        try:
            if not reg.check(self._key):
                return
            for key in reg.list_keys(self._key):
                try:
                    if check_fn(reg, key, runtime):
                        AppLog().log("Purging %s %s" % (self._desc, key))
                        purge_fn(reg, key)
                except:
                    AppLog().log("Error processing %s %s" % (self._desc, key))
                    AppLog().log_exception()
        except:
            AppLog().log_exception()
        finally:
            AppLog().log("Purging %ss: DONE" % self._desc)


if __name__ == "__main__":
    pass

# vim:set ts=4 sw=4 et fileencoding=utf8:
