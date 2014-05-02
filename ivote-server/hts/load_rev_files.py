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

import evlog
import sys
import time
import regrights
import os
import revocationlists
import hts
import election
import bdocconfig
import bdocpython
import bdocpythonutils


def restore_revoke(elid, rfile, operator):

    the_hts = hts.HTS(elid)
    rl = revocationlists.RevocationList()
    rl.attach_elid(elid)
    rl.attach_logger(evlog.AppLog())
    if not rl.check_format(rfile, 'Kontrollin tühistus-/ennistusnimekirja: '):
        errmsg = 'Vigase formaadiga tühistus-/ennistusnimekiri'
        raise Exception(errmsg)

    g_l = None
    b_l = None
    act = ''

    report = []

    newtime = time.localtime()
    if rl.revoke:
        act = 'tühistamine'
        evlog.log('Tühistusavalduse import')
        g_l, b_l = the_hts.load_revoke(rl.rev_list, operator)

        report.append(['------------------------------'])
        report.append(['TÜHISTAMINE (%s)' % \
                time.strftime("%Y%m%d%H%M%S", newtime)])
        report.append(['%d õnnestumist, %d ebaõnnestumist' % \
                (len(g_l), len(b_l))])
        report.append(['Operaator %s, fail %s ' % (operator, rfile)])

    else:
        act = 'ennistamine'
        evlog.log('Ennistusavalduse import')
        g_l, b_l = the_hts.load_restore(rl.rev_list, operator)

        report.append(['------------------------------'])
        report.append(['ENNISTAMINE (%s)' % \
                time.strftime("%Y%m%d%H%M%S", newtime)])
        report.append(['%d õnnestumist, %d ebaõnnestumist' % \
                (len(g_l), len(b_l))])
        report.append(['Operaator %s, fail %s ' % (operator, rfile)])


    for el in b_l:
        el.append(act + ' nurjus')
        report.append(el)

    for el in g_l:
        el.append(act + ' õnnestus')
        report.append(el)

    report.append(['------------------------------'])

    the_hts.save_revocation_report(report)
    return len(rl.rev_list), len(g_l), len(b_l)


def usage():
    print "Kasutamine:"
    print "    %s <valimiste-id> <failinimi>" % sys.argv[0]
    print "        - rakendab tühistus-/ennistusnimekirja"

    sys.exit(1)


if __name__ == '__main__':

    if len(sys.argv) < 3:
        usage()

    elid = sys.argv[1]
    infile = sys.argv[2]

    p_time = "00:00:00"
    evlog.AppLog().set_app('HTS', elid)

    tmp_f = None
    try:
        try:
            s_time = time.time()
            evlog.AppLog().log(\
                'Tühistus-/ennistusnimekirja laadimine: ALGUS')

            bdocpython.initialize()
            bconf = bdocconfig.BDocConfig()
            bconf.load(election.Election().get_bdoc_conf())
            result = regrights.kontrolli_volitusi(elid, infile, 'TYHIS', bconf)
            if not result[0]:
                errmsg = 'Tühistus-/ennistusnimekirja volituste ' \
                               'kontroll andis negatiivse tulemuse: '
                errmsg += result[1]
                raise Exception(errmsg)
            _signercode = result[2]

            tmp_f = bdocpythonutils.get_doc_content_file(infile)

            all_, res_a, res_u = restore_revoke(elid, tmp_f, _signercode)
            p_time = time.strftime("%H:%M:%S", \
                    time.gmtime(long(time.time() - s_time)))

            print 'Tühistamine/ennistamine'
            print '\tKirjeid kokku: %d' % all_
            print '\tEdukalt töödeldud kirjeid: %d' % res_a
            print '\tProbleemseid kirjeid: %d' % res_u
            print '\nAega kulus: %s' % p_time

        except:
            print 'Tühistus-/ennistusnimekirja laadimine ebaõnnestus'
            evlog.AppLog().log_exception()
            sys.exit(1)
    finally:
        if tmp_f != None:
            os.unlink(tmp_f)
        evlog.AppLog().log(\
            'Tühistus-/ennistusnimekirja laadimine (%s): LÕPP' % p_time)

    sys.exit(0)

# vim:set ts=4 sw=4 et fileencoding=utf8:
