# -*- coding: UTF8 -*-

"""
Copyright: Eesti Vabariigi Valimiskomisjon
(Estonian National Electoral Committee), www.vvk.ee
Written in 2004-2014 by Cybernetica AS, www.cyber.ee

This work is licensed under the Creative Commons
Attribution-NonCommercial-NoDerivs 3.0 Unported License.
To view a copy of this license, visit
http://creativecommons.org/licenses/by-nc-nd/3.0/.
"""

import traceback
import sys


def trace():
    exctype, value, tb = sys.exc_info()[:3]
    msg = 'Unhandled [%s, \"%s\"]' % (exctype, value)
    errlst = traceback.extract_tb(tb)
    for el in errlst:
        msg += "[" + el[0] + "," + str(el[1]) + "," + el[2] + "]"
    del tb
    return msg

# vim:set ts=4 sw=4 et fileencoding=utf8:
