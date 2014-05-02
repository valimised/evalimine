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

from evlog import AppLog
import hts
import time

def start_revocation(elid):
    AppLog().set_app('HTS', elid)
    p_time = "00:00:00"

    try:
        try:
            s_time = time.time()
            AppLog().log('Üleminek tühistusperioodi: ALGUS')
            _hts = hts.HTS(elid)
            all_, rev, res = _hts.tyhistusperioodi()
            p_time = time.strftime("%H:%M:%S", \
                    time.gmtime(long(time.time() - s_time)))

            print '\tVastuvõetud häälte koguarv: %d' % all_
            print '\tTühistatud korduvate häälte arv: %d' % rev
            print '\tHääletanute nimekirja kantud kirjete arv: %d' % res
            print '\nAega kulus: %s' % p_time

        except:
            print 'Üleminek tühistusperioodi ebaõnnestus'
            AppLog().log_exception()
    finally:
        AppLog().log('Üleminek tühistusperioodi (%s): LÕPP' % p_time)


def start_tabulation(elid):
    AppLog().set_app('HTS', elid)
    p_time = "00:00:00"

    try:
        try:
            s_time = time.time()
            AppLog().log('Loendamisele minevate ' \
                    'häälte nimekirja koostamine: ALGUS')
            _hts = hts.HTS(elid)
            g_v, r_v, a_v, b_v = _hts.lugemisperioodi()
            p_time = time.strftime("%H:%M:%S", \
                    time.gmtime(long(time.time() - s_time)))
            print '\tLoendamisele minevate häälte arv: %d' % g_v
            print '\tAvalduse alusel tühistatud häälte arv: %d' % r_v
            print '\tKorduvate häälte arv: %d' % a_v
            if (b_v > 0):
                print '\tProbleemsete häälte arv: %d' % b_v
            print '\nAega kulus: %s' % p_time
        except:
            print 'Loendamisele minevate häälte nimekirja ' \
                'koostamine ebaõnnestus'
            AppLog().log_exception()
    finally:
        AppLog().log('Loendamisele minevate häälte nimekirja ' \
            'koostamine (%s): LÕPP' % p_time)


if __name__ == '__main__':
    pass

# vim:set ts=4 sw=4 et fileencoding=utf8:
