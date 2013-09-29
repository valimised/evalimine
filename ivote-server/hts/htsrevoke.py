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

import regrights
import ksum
import os
import htscommon
import revocationlists
import evcommon
import htsbase
from election import Election
import bdocpython
import bdocpythonutils
import evlog


class ActionInfo:

    def __init__(self):
        self.__old_name = ''
        self.__new_name = ''
        self.__reason_name = ''
        self.__timestamp = ''
        self.__code = ''
        self.__name = ''
        self.__reason = ''

    def set_old_name(self, oldn):
        self.__old_name = oldn

    def get_old_name(self):
        return self.__old_name

    def set_new_name(self, newn):
        self.__new_name = newn

    def get_new_name(self):
        return self.__new_name

    def set_reason_name(self, reasonn):
        self.__reason_name = reasonn

    def get_reason_name(self):
        return self.__reason_name

    def set_timestamp(self, times):
        self.__timestamp = times

    def get_timestamp(self):
        return self.__timestamp

    def set_code(self, code):
        self.__code = code

    def get_code(self):
        return self.__code

    def set_name(self, name):
        self.__name = name

    def get_name(self):
        return self.__name

    def set_reason(self, reason):
        self.__reason = reason

    def get_reason(self):
        return self.__reason


class HTSRevoke(htsbase.HTSBase):

    def __init__(self, elid):
        htsbase.HTSBase.__init__(self, elid)

    def __save_list(self, llist, filename):

        flag = os.path.exists(filename)
        outfile = htscommon.LoggedFile(filename, self)
        outfile.open('a')

        if not flag:
            outfile.write(evcommon.VERSION + "\n")
            outfile.write(self._elid + "\n")
        for el in llist:
            outfile.write("\t".join(el) + "\n")

        outfile.close()

    def __kylm_tyhistamine(self, input_list, good_list, bad_list, action_list):
        for el in input_list:
            code = el[0]
            if not self.haaletanud(code):
                bad_list.append(el)
                evlog.log_error('Isik koodiga %s ei ole hääletanud' % code)
                continue

            user_key = htscommon.get_user_key(code)
            vc = htscommon.VoteCounter()
            valid_key = ''

            for vote_file in self._reg.list_keys(user_key):
                if htscommon.VALID_VOTE_PATTERN.match(vote_file):
                    vc.inc_valid()
                    valid_key = vote_file
                elif htscommon.USERREVOKED_VOTE_PATTERN.match(vote_file):
                    vc.inc_userrevoked()
                elif htscommon.AUTOREVOKED_VOTE_PATTERN.match(vote_file):
                    pass
                elif htscommon.REVOKE_REASON_PATTERN.match(vote_file):
                    pass
                elif htscommon.VOTE_VERIFICATION_ID_FILENAME == vote_file:
                    pass
                else:
                    vc.inc_unknown()

            if (vc.valid() > 1):
                self._errmsg = 'Serveri andmestruktuurid ei ole kooskõlalised'
                raise Exception(self._errmsg)

            if ((vc.valid() == 0) or (vc.userrevoked() > 0)):
                bad_list.append(el)
                evlog.log_error(\
                    'Kasutaja isikukoodiga %s hääl on juba tühistatud' % \
                    code)

            if (vc.unknown() > 0):
                self._errmsg = 'Tundmatu viga häälte tühistamisel'
                raise Exception(self._errmsg)

            if (vc.valid() == 1):
                revoked_key = \
                    htscommon.change_votefile_name(\
                        valid_key, htscommon.BUSERREVOKED)
                act = ActionInfo()
                act.set_old_name(self._reg.path(user_key + [valid_key]))
                act.set_new_name(self._reg.path(user_key + [revoked_key]))
                act.set_reason_name(self._reg.path(user_key))
                act.set_timestamp(htscommon.get_votefile_time(valid_key))
                act.set_code(el[0])
                act.set_name(el[1])
                act.set_reason(el[2])
                good_list.append(el)
                action_list.append(act)

    def __kylm_ennistamine(self, input_list, good_list, bad_list, action_list):
        for el in input_list:
            code = el[0]
            if not self.haaletanud(code):
                bad_list.append(el)
                evlog.log_error('Isik koodiga %s ei ole hääletanud' % code)
                continue

            user_key = htscommon.get_user_key(code)
            vc = htscommon.VoteCounter()
            revoked_key = ''

            for vote_file in self._reg.list_keys(user_key):
                if htscommon.VALID_VOTE_PATTERN.match(vote_file):
                    vc.inc_valid()
                elif htscommon.USERREVOKED_VOTE_PATTERN.match(vote_file):
                    vc.inc_userrevoked()
                    revoked_key = vote_file
                elif htscommon.AUTOREVOKED_VOTE_PATTERN.match(vote_file):
                    pass
                elif htscommon.REVOKE_REASON_PATTERN.match(vote_file):
                    pass
                elif htscommon.VOTE_VERIFICATION_ID_FILENAME == vote_file:
                    pass
                else:
                    vc.inc_unknown()

            if ((vc.userrevoked() == 0) or (vc.valid() > 0)):
                bad_list.append(el)
                evlog.log_error(\
                    'Isik koodiga %s ei ole oma häält tühistanud' % code)
                continue

            if (vc.userrevoked() > 1):
                self._errmsg = 'Serveri andmestruktuurid ei ole kooskõlalised'
                raise Exception(self._errmsg)

            if (vc.unknown() > 0):
                self._errmsg = 'Tundmatu viga häälte tühistamisel'
                raise Exception(self._errmsg)

            if (vc.userrevoked() == 1):
                valid_key = \
                    htscommon.change_votefile_name(\
                        revoked_key, htscommon.BVALID)
                act = ActionInfo()
                act.set_old_name(self._reg.path(user_key + [revoked_key]))
                act.set_new_name(self._reg.path(user_key + [valid_key]))
                act.set_reason_name(self._reg.path(user_key + ['reason']))
                act.set_timestamp(htscommon.get_votefile_time(revoked_key))
                act.set_code(el[0])
                act.set_name(el[1])
                act.set_reason(el[2])
                good_list.append(el)
                action_list.append(act)

    def __kuum_tyhistamine(self, operaator, action_list):
        for el in action_list:
            os.rename(el.get_old_name(), el.get_new_name())
            # vajalik lugemisele minevate häälte nimistu koostamiseks
            self._reg.create_string_value(\
                [el.get_reason_name()], 'reason', el.get_reason())
            self._revlog.log_info(
                tegevus='tühistamine',
                isikukood=el.get_code(),
                nimi=el.get_name(),
                timestamp=el.get_timestamp(),
                operaator=operaator,
                pohjus=el.get_reason())

    def __kuum_ennistamine(self, operaator, action_list):
        for el in action_list:
            os.rename(el.get_old_name(), el.get_new_name())
            os.unlink(el.get_reason_name())
            self._revlog.log_info(
                tegevus='ennistamine',
                isikukood=el.get_code(),
                nimi=el.get_name(),
                timestamp=el.get_timestamp(),
                operaator=operaator,
                pohjus=el.get_reason())

    def __tyhista_haaled(self, input_list, operaator):
        evlog.log('Tühistusavalduse import')
        good_list = []
        bad_list = []
        action_list = []
        self.__kylm_tyhistamine(input_list, good_list, bad_list, action_list)
        self.__kuum_tyhistamine(operaator, action_list)
        return good_list, bad_list

    def __ennista_haaled(self, input_list, operaator):
        evlog.log('Ennistusavalduse import')
        action_list = []
        bad_list = []
        good_list = []
        self.__kylm_ennistamine(input_list, good_list, bad_list, action_list)
        self.__kuum_ennistamine(operaator, action_list)
        return good_list, bad_list

    def tyhista_ennista(self, filename):

        tmp_tyhis_f = None

        try:

            bdocpython.initialize()
            bconf = bdocpythonutils.BDocConfig()
            bconf.load(Election().get_bdoc_conf())

            result = regrights.kontrolli_volitusi(\
                self._elid, filename, 'TYHIS', bconf)

            if not result[0]:
                self._errmsg = \
                    'Tühistus-/ennistusnimekirja volituste ' \
                    'kontroll andis negatiivse tulemuse: '
                self._errmsg += result[1]
                raise Exception(self._errmsg)
            _signercode = result[2]

            tmp_tyhis_f = bdocpythonutils.get_doc_content_file(filename)

            rl = revocationlists.RevocationList()
            rl.attach_elid(self._elid)
            rl.attach_logger(evlog.AppLog())
            if not rl.check_format(tmp_tyhis_f, \
                'Kontrollin tühistus-/ennistusnimekirja: '):
                self._errmsg = 'Vigase formaadiga tühistus-/ennistusnimekiri'
                raise Exception(self._errmsg)

            g_l = None
            b_l = None
            act = ''

            report = []

            if rl.revoke:
                act = 'tühistamine'
                g_l, b_l = self.__tyhista_haaled(rl.rev_list, _signercode)
            else:
                act = 'ennistamine'
                g_l, b_l = self.__ennista_haaled(rl.rev_list, _signercode)

            for el in b_l:
                el.append(act + ' nurjus')
                report.append(el)

            for el in g_l:
                el.append(act + ' õnnestus')
                report.append(el)

            fn = self._reg.path(['hts', 'output', evcommon.REVREPORT_FILE])
            self.__save_list(report, fn)
            ksum.store(fn)
            return len(rl.rev_list), len(g_l), len(b_l)

        finally:

            if tmp_tyhis_f != None:
                os.unlink(tmp_tyhis_f)


if __name__ == '__main__':
    print "No main"

# vim:set ts=4 sw=4 et fileencoding=utf8:
