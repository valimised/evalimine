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

import os
import sys
import inputlists
import regrights
from election import Election
from election import ElectionState
from evlog import AppLog
import exception_msg
import evcommon
import sigverify
import question

import bdocconfig
import bdocpython
import bdocpythonutils


def checkfile(filename):
    if not os.access(filename, os.F_OK):
        print 'Faili ' + filename + ' pole olemas\n'
        return False
    if not os.access(filename, os.R_OK):
        print 'Faili ' + filename + ' pole võimalik lugeda\n'
        return False

    return True


class ConfCreator:

    def __init__(self):
        self.elid = None
        self._vl = None
        self._ed = None
        self._ch = None
        self.reg = None
        self.quest = None
        self.root = None
        self.jaosk_f = None
        self.voter_f = None
        self.valik_f = None
        self.voter_public_key_f = None

        self.conf = bdocconfig.BDocConfig()
        self.conf.load(Election().get_bdoc_conf())

    def __del__(self):
        if self._vl is not None:
            self._vl.close()

    def check_districts_file(self):
        tmp_jaosk_f = None
        try:
            if not checkfile(self.jaosk_f):
                return False

            print 'Kontrollin jaoskondade faili volitusi'
            ret = regrights.kontrolli_volitusi(
                self.elid, self.jaosk_f, 'JAOSK', self.conf)
            if not ret[0]:
                print 'Jaoskondade faili volituste '\
                    'kontroll andis negatiivse tulemuse'
                print ret[1]
                return False

            tmp_jaosk_f = bdocpythonutils.get_doc_content_file(self.jaosk_f)

            self._ed = inputlists.Districts()
            self._ed.attach_elid(self.elid)
            self._ed.attach_logger(AppLog())
            if not self._ed.check_format(
                    tmp_jaosk_f, 'Kontrollin jaoskondade nimekirja: '):
                print "Jaoskondade nimekiri ei vasta nõuetele"
                return False
            print "Jaoskondade nimekiri OK"
            return True
        finally:
            if tmp_jaosk_f is not None:
                os.unlink(tmp_jaosk_f)

    def check_choices_file(self):

        tmp_valik_f = None
        try:
            if not checkfile(self.valik_f):
                return False

            print 'Kontrollin valikutefaili volitusi'
            ret = regrights.kontrolli_volitusi(
                self.elid, self.valik_f, 'VALIK', self.conf)
            if not ret[0]:
                print 'Valikute faili volituste kontroll '\
                    'andis negatiivse tulemuse'
                print ret[1]
                return False

            tmp_valik_f = bdocpythonutils.get_doc_content_file(self.valik_f)

            self._ch = self.quest.choices_list(self._ed)
            self._ch.attach_elid(self.elid)
            self._ch.attach_logger(AppLog())
            if not self._ch.check_format(
                    tmp_valik_f, 'Kontrollin valikute nimekirja: '):
                print "Valikute nimekiri ei vasta nõuetele"
                return False
            print "Valikute nimekiri OK"
            return True
        finally:
            if tmp_valik_f is not None:
                os.unlink(tmp_valik_f)

    def check_voters_file(self):

        # HES & HTS

        if not checkfile(self.voter_f):
            return False
        if not checkfile(self.voter_public_key_f):
            return False

        print "Kontrollin valijate faili avalikku võtit"
        if not sigverify.check_sig_file(self.voter_public_key_f):
            return False

        print "Kontrollin valijate faili terviklikkust"
        checkResult = sigverify.check_initial(
            self.voter_f, self.voter_public_key_f)
        if not checkResult[0]:
            print 'Kontrollimisel tekkis viga: %s\n' % checkResult[1]
            return False

        self._vl = inputlists.VotersList(self.root, self.reg, self._ed)
        self._vl.attach_elid(self.elid)
        self._vl.attach_logger(AppLog())
        if not self._vl.check_format(
                self.voter_f, 'Kontrollin valijate nimekirja: '):
            print "Valijate nimekiri ei vasta nõuetele"
            return False

        if not self._vl.algne:
            print "Valijate nimekirja tüüp ei ole 'algne'"
            return False

        print "Valijate nimekiri OK"
        return True

    def do_it(self):

        c_ring, c_dist = self._ed.create(self.root, self.reg)
        Election().copy_config_file(
            self.elid, self.root, self.jaosk_f, evcommon.DISTRICT_FILES)
        print 'Paigaldatud %d ringkonda ja %d jaoskonda' % (c_ring, c_dist)

        c_choice = self._ch.create(self.quest.choices_proxy())
        Election().copy_config_file(
            self.elid, self.root, self.valik_f, evcommon.CANDIDATE_FILES)
        print 'Paigaldatud %d valikut' % c_choice

        if self.root in ['hes', 'hts']:

            print 'Paigaldan valijate faili võtit'
            Election().copy_voter_public_key_file(
                self.elid, self.voter_public_key_f)
            print 'Võti on paigaldatud'

            c_add, c_del = self._vl.create('Paigaldan valijaid: ')
            print 'Valijad on paigaldatud. '\
                'Teostati %d lisamist ja %d eemaldamist'\
                % (c_add, c_del)
            Election().copy_config_file(
                self.elid, self.root, self.voter_f, evcommon.VOTERS_FILES)
            Election().add_voters_file_hash(self.voter_f)

        return True

    def prepare(self, confer_name, server_root):

        self.root = server_root

        if not ElectionState().can_load_conf():
            print('Selles hääletuse faasis (%s) pole võimalik valimisinfot '
                  'laadida' % ElectionState().str())
            return False

        self.reg = Election().get_sub_reg(self.elid)
        AppLog().set_app(confer_name, self.elid)
        AppLog().log('Valimiste failide laadimine: ALGUS')
        self.quest = question.Question(self.elid, self.root, self.reg)
        self.quest.reset_data()

        print 'Valimised: ' + self.elid
        return True

    def success(self):
        Election().config_server_elid_done(self.elid)
        AppLog().log('Valimiste failide laadimine: LÕPP')
        print 'Valimiste failide laadimine oli edukas'

    def failure(self):
        self.quest.reset_data()
        Election().config_server_elid_done(self.elid, False)
        AppLog().log('Valimiste failide laadimine: LÕPP')
        print 'Valimiste failide laadimine ebaõnnestus'


def do_configure(apptype,
                 elid,
                 jaosk_f=None,
                 voter_f=None,
                 valik_f=None,
                 voter_public_key_f=None):

    def do_conf(cc):
        # pylint: disable-msg=W0702
        try:
            cc.elid = elid
            cc.jaosk_f = jaosk_f
            cc.voter_f = voter_f
            cc.valik_f = valik_f
            cc.voter_public_key_f = voter_public_key_f

            if not cc.prepare('CONFIGURATOR', apptype):
                return False

            if jaosk_f:
                if not cc.check_districts_file():
                    return False

            if valik_f:
                if not cc.check_choices_file():
                    return False

            if voter_f and voter_public_key_f:
                if not cc.check_voters_file():
                    return False

            if not cc.do_it():
                return False
            return True

        except:
            print 'Viga valimiste failide laadimisel'
            print exception_msg.trace()
            return False

    bdocpython.initialize()

    try:
        my_cc = ConfCreator()
        if do_conf(my_cc):
            my_cc.success()
            return True
        else:
            my_cc.failure()
            return False
    finally:
        bdocpython.terminate()


def config_hts(elid, jaosk_f, voter_f, valik_f, voterkey_f):
    return do_configure(evcommon.APPTYPE_HTS,
                        elid, jaosk_f, voter_f, valik_f, voterkey_f)


def config_hes(elid, jaosk_f, voter_f, valik_f, voterkey_f):
    return do_configure(evcommon.APPTYPE_HES,
                        elid, jaosk_f, voter_f, valik_f, voterkey_f)


def config_hlr(elid, jaosk_f, valik_f):
    return do_configure(evcommon.APPTYPE_HLR, elid, jaosk_f, None, valik_f)


def usage_print():
    sys.stderr.write('Kasutamine: ' + sys.argv[0] + ' <parameetrid>\n')
    sys.stderr.write('\t' + evcommon.APPTYPE_HES +
        ' <elid> <jaoskondade-fail> <valijate-fail> <valikute-fail> <võtme-fail>\n')
    sys.stderr.write('\t' + evcommon.APPTYPE_HTS +
        ' <elid> <jaoskondade-fail> <valijate-fail> <valikute-fail> <võtme-fail>\n')
    sys.stderr.write('\t' + evcommon.APPTYPE_HLR +
        ' <elid> <jaoskondade-fail> <valikute-fail>\n')
    sys.exit(1)


def usage():

    if len(sys.argv) < 2:
        usage_print()

    if not sys.argv[1] in evcommon.APPTYPES:
        usage_print()

    if sys.argv[1] in [evcommon.APPTYPE_HES, evcommon.APPTYPE_HTS]:
        if len(sys.argv) != 7:
            usage_print()
        evcommon.checkfile(sys.argv[3])
        evcommon.checkfile(sys.argv[4])
        evcommon.checkfile(sys.argv[5])
        evcommon.checkfile(sys.argv[6])

    if sys.argv[1] == evcommon.APPTYPE_HLR:
        if len(sys.argv) != 5:
            usage_print()
        evcommon.checkfile(sys.argv[3])
        evcommon.checkfile(sys.argv[4])


def main_function():
    usage()
    res = False
    if sys.argv[1] == evcommon.APPTYPE_HES:
        res = config_hes(sys.argv[2], sys.argv[3],
                         sys.argv[4], sys.argv[5], sys.argv[6])

    if sys.argv[1] == evcommon.APPTYPE_HTS:
        res = config_hts(sys.argv[2], sys.argv[3],
                         sys.argv[4], sys.argv[5], sys.argv[6])

    if sys.argv[1] == evcommon.APPTYPE_HLR:
        res = config_hlr(sys.argv[2], sys.argv[3], sys.argv[4])

    return res

if __name__ == "__main__":
    main_function()

# vim:set ts=4 sw=4 et fileencoding=utf8:
