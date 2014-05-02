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
import shutil
import inputlists
import regrights
from election import Election
from election import ElectionState
from evlog import AppLog
import exception_msg
import evcommon
import question
import time

import bdocconfig
import bdocpython
import bdocpythonutils


class ChoicesReplace:


    def __init__(self):
        self.elid = None
        self._ed = None
        self._ch = None
        self.reg = None
        self.quest = None
        self.root = None
        self.backup_dir = None

        self.conf = bdocconfig.BDocConfig()
        self.conf.load(Election().get_bdoc_conf())


    def check_choices_file(self, valik_f):

        # HES & HLR
        tmp_valik_f = None
        try:

            print 'Kontrollin valikutefaili volitusi'
            ret = regrights.kontrolli_volitusi(self.elid, valik_f, 'VALIK', \
                self.conf)
            if not ret[0]:
                print 'Valikute faili volituste kontroll '\
                    'andis negatiivse tulemuse'
                print ret[1]
                return False

            tmp_valik_f = bdocpythonutils.get_doc_content_file(valik_f)

            self._ch = self.quest.choices_list(self._ed)
            self._ch.attach_elid(self.elid)
            self._ch.attach_logger(AppLog())
            if not self._ch.check_format(tmp_valik_f, \
                'Kontrollin valikute nimekirja: '):
                print "Valikute nimekiri ei vasta nõuetele"
                return False
            print "Valikute nimekiri OK"
            return True
        finally:
            if not tmp_valik_f == None:
                os.unlink(tmp_valik_f)

    def do_it(self):
        c_choice = self._ch.create(self.quest.choices_proxy())
        print 'Paigaldatud %d valikut' % c_choice
        return True

    def _backup_old_choices(self):
        src = os.path.join(self.reg.path(), self.root, 'choices')
        backup_t = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        self.backup_dir = '/tmp/choices_%s' % backup_t
        if os.path.exists(src) and os.path.isdir(src):
            shutil.move(src, self.backup_dir)
        else:
            raise Exception('Valikute varundamine ebaõnnestus - ei leidnud '\
                                                        'kataloogi %s' % src)

    def _restore_old_choices(self):
        dst = os.path.join(self.reg.path(), self.root, 'choices')
        if os.path.exists(dst):
            shutil.rmtree(dst)

        if os.path.exists(self.backup_dir) and os.path.isdir(self.backup_dir):
            shutil.move(self.backup_dir, dst)
        else:
            raise Exception('Valikute taastamine ebaõnnestus')


    def _delete_old_choices(self):
        if self.backup_dir != None and os.path.exists(self.backup_dir) and \
                                                os.path.isdir(self.backup_dir):
            shutil.rmtree(self.backup_dir, True)


    def prepare(self, confer_name):

        if Election().is_hes():
            self.root = 'hes'
        elif Election().is_hlr():
            self.root = 'hlr'
        else:
            raise Exception('Vigane serveritüüp')

        if not ElectionState().can_replace_candidates():
            print 'Selles hääletuse faasis (%s) valikuid muuta ei saa'\
                % ElectionState().str()
            return False

        self.reg = Election().get_sub_reg(self.elid)
        AppLog().set_app(confer_name, self.elid)
        AppLog().log('Valikute nimekirja välja vahetamine: ALGUS')
        self.quest = question.Question(self.elid, self.root, self.reg)

        self._ed = inputlists.Districts()
        self._ed.load(self.root, self.reg)

        self._backup_old_choices()
        print 'Valimised: ' + self.elid
        return True

    def success(self):
        self._delete_old_choices()
        AppLog().log('Valikute nimekirja välja vahetamine: LÕPP')
        print 'Valikute nimekirja väljavahetamine oli edukas'

    def failure(self):
        self._restore_old_choices()
        AppLog().log('Valikute nimekirja välja vahetamine: LÕPP')
        print 'Valikute nimekirja väljavahetamine ebaõnnestus, '\
            'taastasin muudatuste eelse olukorra'


def replace_candidates(elid, valik_f):

    """Valikute nimekirja välja vahetamine"""

    def do_replace(cr):
        try:
            cr.elid = elid

            if not cr.prepare('REPLACE CHOICES'):
                return False

            if not cr.check_choices_file(valik_f):
                return False

            if not cr.do_it():
                return False
            return True

        except: # pylint: disable=W0702
            print 'Viga valikute nimekirja välja vahetamisel'
            print exception_msg.trace()
            return False


    bdocpython.initialize()
    try:
        my_cr = ChoicesReplace()
        if do_replace(my_cr):
            my_cr.success()
            return True
        else:
            my_cr.failure()
            return False
    finally:
        bdocpython.terminate()


def usage():

    if (len(sys.argv) != 3):
        sys.stderr.write('Kasutamine: ' + sys.argv[0] + \
            ' <valimiste-id> <valikute-fail>\n')
        sys.exit(1)

    evcommon.checkfile(sys.argv[2])

if __name__ == '__main__':
    usage()
    replace_candidates(sys.argv[1], sys.argv[2])

# vim:set ts=4 sw=4 expandtab et fileencoding=utf8:
