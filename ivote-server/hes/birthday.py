#!/usr/bin/python2.7
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

import time

def date_today():
    # tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec,
    # tm_wday, tm_yday, tm_isdst
    now = time.localtime()
    return [now[0], now[1], now[2]]


def date_birthday(ik):
    lst = []

    # aasta
    if ik[0] == '1' or ik[0] == '2':
        lst.append(int('18' + ik[1:3]))
    elif ik[0] == '3' or ik[0] == '4':
        lst.append(int('19' + ik[1:3]))
    else:
        lst.append(int('20' + ik[1:3]))
    # kuu
    lst.append(int(ik[3:5]))
    # p2ev
    lst.append(int(ik[5:7]))

    return lst


def is_18(ik):
    today = date_today()
    birthday = date_birthday(ik)

    if today[0] - birthday[0] > 18:
        return True
    if today[0] - birthday[0] < 18:
        return False

    # today[0] - birthday[0] == 18, v6rrelda kuup2evasid
    if today[1] > birthday[1]:
        return True
    if today[1] < birthday[1]:
        return False

    # today[1] == birthday[1], v6rrelda p2evasid
    if today[2] >= birthday[2]:
        return True

    # today[2] < birthday[2]. Isik pole veel t2naseks 18 saanud
    # (saab t2na v6i hiljem).
    return False


if __name__ == '__main__':
    print 'No main'

# vim:set ts=4 sw=4 et fileencoding=utf8:
