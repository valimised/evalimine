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
from election import Election
from election import ElectionState
import evlog
import ksum
import sigverify
import inputlists
import time
import uiutil
import evcommon


class BufferedLog:

    def __init__(self, log_file, app, elid):
        self.__logger = evlog.Logger(Election().get_server_str())
        self.__logger.set_logs(log_file)
        self.__logger.set_format(evlog.ChangesLogFormat(app))
        self.__buffer = []

    def log_error(self, msg):
        self.__buffer.append(msg)
        self.__logger.log_err(message=msg)

    def empty(self):
        return len(self.__buffer) == 0

    def output_errors(self):
        for elem in self.__buffer:
            sys.stderr.write(' %s\n' % elem)


def create_tokend_file(tokend, reg, elid):

    outf = None

    try:
        import hts
        hh = hts.HTS(elid)

        fn = 'tokend.'
        fn += time.strftime('%Y%m%d%H%M%S')

        out = ''

        for el in tokend:
            if hh.haaletanud(el):
                out += el
                out += '\t'
                out += '\t'.join(tokend[el])
                out += '\n'

        if out:
            out = elid + '\n' + out
            out = '1\n' + out
            filename = reg.path(['hts', 'output', fn])
            outf = file(filename, 'w')
            outf.write(out)
            outf.close()
            ksum.store(filename)
            outf = None

    finally:
        if outf is not None:
            outf.close()


def apply_changes(elid, voter_f):
    """Muudatuste rakendamine"""

    vl = None
    tokend = {}

    def check_state():
        if not ElectionState().can_apply_changes():
            sys.stderr.write('Selles hääletuse faasis (%s) pole võimalik '
                'nimekirju uuendada\n'
                % ElectionState().str())
            sys.exit(1)

    try:

        buflog = None

        if Election().is_hes():
            root = 'hes'
        elif Election().is_hts():
            root = 'hts'
        else:
            raise Exception('Vigane serveritüüp')

        buflog = BufferedLog(Election().
                get_path(evcommon.VOTER_LIST_LOG_FILE),
                'APPLY-CHANGES', elid)

        check_state()
        reg = Election().get_sub_reg(elid)
        ed = inputlists.Districts()
        ed.load(root, reg)
        vl = inputlists.VotersList(root, reg, ed)
        vl.attach_elid(elid)
        vl.ignore_errors()
        evlog.AppLog().set_app('APPLY-CHANGES')
        vl.attach_logger(evlog.AppLog())

        print "Kontrollin valijate faili terviklikkust"
        checkResult = sigverify.check_existent(voter_f, elid)
        if not checkResult[0]:
            raise Exception('Kontrollimisel tekkis viga: %s\n' % checkResult[1])
        else:
            print "Valijate faili terviklikkus OK"

        voters_file_sha256 = ksum.compute(voter_f)
        if Election().get_root_reg().check(
            ['common', 'voters_file_hashes', voters_file_sha256]):
            raise Exception('Kontrollsummaga %s fail on juba laaditud\n'
                % voters_file_sha256)

        if not vl.check_format(voter_f, 'Kontrollin valijate nimekirja: '):
            print "Valijate nimekiri ei vasta vormingunõuetele"
            sys.exit(1)
        else:
            print 'Valijate nimekiri OK'

        vl.attach_logger(buflog)
        if not vl.check_muudatus(
            'Kontrollin muudatuste kooskõlalisust: ',
            ElectionState().election_on(), tokend):
            print "Sisend ei ole kooskõlas olemasoleva konfiguratsiooniga"
        else:
            print "Muudatuste kooskõlalisus OK"

        _apply = 1
        if not buflog.empty():
            print 'Muudatuste sisselaadimisel esines vigu'
            buflog.output_errors()
            _apply = uiutil.ask_yes_no(
            'Kas rakendan kooskõlalised muudatused?')

        if not _apply:
            buflog.log_error('Muudatusi ei rakendatud')
            print 'Muudatusi ei rakendatud'
        else:
            if ElectionState().election_on() and root == 'hts':
                create_tokend_file(tokend, reg, elid)
            a_count, d_count = vl.create('Paigaldan valijaid: ')
            print 'Teostasin %d lisamist ja %d eemaldamist' \
                % (a_count, d_count)
            Election().copy_config_file(
                elid, root, voter_f, evcommon.VOTERS_FILES)
            Election().add_voters_file_hash(voter_f)
            print 'Muudatuste rakendamine lõppes edukalt'

    except SystemExit:
        sys.stderr.write('Viga muudatuste laadimisel\n')
        if buflog:
            buflog.output_errors()
        raise

    except Exception as ex:
        sys.stderr.write('Viga muudatuste laadimisel: ' + str(ex) + '\n')
        if buflog:
            buflog.output_errors()
        sys.exit(1)

    finally:
        if vl is not None:
            vl.close()


def usage():

    if len(sys.argv) != 3:
        sys.stderr.write('Kasutamine: ' + sys.argv[0] +
            ' <valimiste-id> <valijate-fail>\n')
        sys.exit(1)

    evcommon.checkfile(sys.argv[2])

if __name__ == '__main__':
    usage()
    apply_changes(sys.argv[1], sys.argv[2])

# vim:set ts=4 sw=4 expandtab et fileencoding=utf8:
