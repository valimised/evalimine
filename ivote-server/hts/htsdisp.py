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

from election import Election
from election import ElectionState
from evlog import AppLog
import election
import sys
import hts
import htsrevoke
import time


class HTSDispatcher:

    def __init__(self, elid):
        self._elid = elid
        AppLog().set_app('HTS', self._elid)

    def yleminek_tyhistusperioodi(self, pref=''):
        p_time = "00:00:00"

        try:
            try:
                s_time = time.time()
                AppLog().log('Üleminek tühistusperioodi: ALGUS')
                if ElectionState().get() == election.ETAPP_TYHISTUS:
                    _hts = hts.HTS(self._elid)
                    all_, rev, res = _hts.tyhistusperioodi()
                    p_time = time.strftime("%H:%M:%S", \
                            time.gmtime(long(time.time() - s_time)))

                    print '%sVastuvõetud häälte koguarv: %d' % (pref, all_)
                    print '%sTühistatud korduvate häälte arv: %d' % \
                        (pref, rev)
                    print \
                        '%sHääletanute nimekirja kantud kirjete arv: %d' % \
                            (pref, res)
                    print '\nAega kulus: %s' % p_time

                else:
                    mess = \
                        'Antud funktsioon on lubatud vaid tühistusperioodil'
                    print mess
                    AppLog().log_error(mess)
            except:
                print 'Üleminek tühistusperioodi ebaõnnestus'
                AppLog().log_exception()
        finally:
            AppLog().log(\
                'Üleminek tühistusperioodi (%s): LÕPP' % p_time)

    def tyhista_ennista(self, filename):
        p_time = "00:00:00"

        try:
            try:
                s_time = time.time()
                AppLog().log(\
                    'Tühistus-/ennistusnimekirja laadimine: ALGUS')
                if ElectionState().get() == election.ETAPP_TYHISTUS:
                    _htsr = htsrevoke.HTSRevoke(self._elid)
                    all_, res_a, res_u = _htsr.tyhista_ennista(filename)
                    p_time = time.strftime("%H:%M:%S", \
                            time.gmtime(long(time.time() - s_time)))

                    print 'Tühistamine/ennistamine'
                    print '\tKirjeid kokku: %d' % all_
                    print '\tEdukalt töödeldud kirjeid: %d' % res_a
                    print '\tProbleemseid kirjeid: %d' % res_u
                    print '\nAega kulus: %s' % p_time
                else:
                    mess = \
                        'Antud funktsioon on lubatud vaid tühistusperioodil'
                    print mess
                    AppLog().log_error(mess)
            except:
                print 'Tühistus-/ennistusnimekirja laadimine ebaõnnestus'
                AppLog().log_exception()
        finally:
            AppLog().log(\
                'Tühistus-/ennistusnimekirja laadimine (%s): LÕPP' % p_time)

    def loendamisele_minevad_haaled(self, pref=''):
        p_time = "00:00:00"

        try:
            try:
                s_time = time.time()
                AppLog().log(\
                    'Loendamisele minevate ' \
                        'häälte nimekirja koostamine: ALGUS')
                if ElectionState().get() == election.ETAPP_LUGEMINE:
                    _hts = hts.HTS(self._elid)
                    g_v, b_v = _hts.lugemisperioodi()
                    p_time = time.strftime("%H:%M:%S", \
                            time.gmtime(long(time.time() - s_time)))

                    print '%sLoendamisele minevate häälte arv: %d' % \
                        (pref, g_v)
                    print '%sAvalduse alusel tühistatud häälte arv: %d' % \
                            (pref, b_v)
                    print '\nAega kulus: %s' % p_time
                else:
                    mess = 'Antud funktsioon on lubatud vaid lugemisperioodil'
                    print mess
                    AppLog().log_error(mess)
            except:
                print 'Loendamisele minevate häälte nimekirja ' \
                    'koostamine ebaõnnestus'
                AppLog().log_exception()
        finally:
            AppLog().log(\
                'Loendamisele minevate häälte nimekirja ' \
                'koostamine (%s): LÕPP' % p_time)


def usage():
    print "Kasutamine:"
    print "    %s <valimiste-id> yleminek_tyhistusperioodi" % sys.argv[0]
    print "        - tühistab korduvad hääled ja " \
        "salvestab e-hääletanute nimekirja"
    print "    %s <valimiste-id> loendamisele_minevad_haaled" % sys.argv[0]
    print "        - koostab loendamisele minevate häälte nimekirja"
    print "    %s <valimiste-id> tyhista_ennista <failinimi>" % sys.argv[0]
    print "        - rakendab tühistus-/ennistusnimekirja"
    print "        - no: kehtivuskinnituse olemasolu pole vajalik"

    sys.exit(1)


def main_function():
    if len(sys.argv) < 3:
        usage()

    if not sys.argv[2] in ['yleminek_tyhistusperioodi',
                            'loendamisele_minevad_haaled',
                            'tyhista_ennista']:
        usage()

    if (sys.argv[2] in ['tyhista_ennista'] and len(sys.argv) < 4):
        usage()

    htsd = None

    try:
        htsd = HTSDispatcher(sys.argv[1])
        if sys.argv[2] == 'yleminek_tyhistusperioodi':
            htsd.yleminek_tyhistusperioodi()
        elif sys.argv[2] == 'loendamisele_minevad_haaled':
            htsd.loendamisele_minevad_haaled()
        elif sys.argv[2] == 'tyhista_ennista':
            htsd.tyhista_ennista(sys.argv[3])
        else:
            usage()

    except SystemExit:
        raise
    except Exception, _e:
        print _e
        sys.exit(1)
    except:
        sys.exit(1)

    finally:
        pass

    sys.exit(0)


if __name__ == '__main__':
    main_function()

# vim:set ts=4 sw=4 et fileencoding=utf8:
