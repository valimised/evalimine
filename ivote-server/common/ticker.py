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

import sys

class Counter:

    def __init__(self, prefix='', formatstr=''):
        self._prefix = '\t' + prefix + ' %d '
        self._count = 0
        self._meter = 0
        self._level = 1000
        self._txt = self._prefix + formatstr
        self._clear = ''
        for _i in range(0, 80):
            self._clear += ' '

    def __do_output(self, *arglist):
        _args = (self._count,) + arglist
        self.__print_out(self._txt % _args)

    def __print_out(self, out):
        output = ''
        if (len(out) > 80):
            output = out[0:80] + '...'
        else:
            output = out

        sys.stdout.write('\r' + self._clear)
        sys.stdout.write('\r' + output)
        sys.stdout.flush()

    def start(self, txt):
        sys.stdout.write(txt + '\n')
        self.__print_out(self._prefix % self._count)

    def finish(self):
        sys.stdout.write('\r' + self._clear)
        sys.stdout.write('\n')

    def tick(self, amount=1, *arglist):
        self._count += amount
        self._meter += amount
        if (self._meter >= self._level):
            while self._meter >= self._level:
                self._meter -= self._level

            self.__do_output(*arglist)


class Ticker:
    # pylint: disable=R0903

    def __init__(self, all_, txt):
        self._txt = txt
        self._per = all_ / 100
        if self._per == 0:
            self._per = all_ + 1

        self._mod = 0
        self._out = 0

    def tick(self, amount=1):

        if self._out < 100:
            self._mod += amount
            if (self._mod >= self._per):
                while self._mod >= self._per:
                    self._mod = self._mod - self._per
                    self._out += 1
                if self._out > 100:
                    self._out = 100
                print '%s%d%%\r' % (self._txt, self._out),
                sys.stdout.flush()
                if self._out == 100:
                    print


def tickit(max_, msg):
    ticker = Ticker(max_, msg)

    for _ in range(max_):
        ticker.tick()


if __name__ == "__main__":
    tickit(1000000, 'Teade: ')

# vim:set ts=4 sw=4 et fileencoding=utf8:
