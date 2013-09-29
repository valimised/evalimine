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

import os
import httplib
import urllib
from election import Election
import evlog
import regrights
import evcommon
import evmessage
import evstrings
import bdocpython
import bdocpythonutils
import exception_msg
import sessionid

HEADERS = {
    'Content-type': 'application/x-www-form-urlencoded',
    'Accept': 'text/plain',
    'PID': os.getppid(),
    'User-agent': 'HES'}


class HESResult:

    def __init__(self, logit=None):
        self.user_code = evcommon.EVOTE_ERROR
        self.user_msg = evmessage.EvMessage().\
            get_str("TEHNILINE_VIGA", evstrings.TEHNILINE_VIGA)
        self.log_msg = logit

    def pole_valija(self, ik):
        self.user_code = evcommon.EVOTE_VOTER_ERROR
        self.user_msg = evmessage.EvMessage().\
            get_str("POLE_VALIJA", evstrings.POLE_VALIJA)
        self.log_msg = \
            'Isikukood %s ei kuulu ühegi hääletuse valijate nimekirja' % ik

    def set_log_msg(self, msg):
        self.log_msg = msg


class VoteChecker:

    def __init__(self, decoded_vote, ik):
        self._decoded_vote = decoded_vote
        self._ik = ik
        self.error = HESResult()

    def check_vote(self, mobid):

        try:
            bdocpython.initialize()
            conf = bdocpythonutils.BDocConfig()
            conf.load(Election().get_bdoc_conf())

            alines = []
            elines = []
            if mobid:
                alines, elines = \
                        regrights.analyze_signature_for_log(self._decoded_vote)
            else:
                alines, elines = \
                        regrights.analyze_vote_for_log(self._decoded_vote)

            for el in alines:
                evlog.log(el)

            for el in elines:
                evlog.log_error(el)

            res = None
            if mobid:
                res = regrights.check_vote_hes_mobid(self._decoded_vote, conf)
            else:
                res = regrights.check_vote_hes(self._decoded_vote, conf)

            if not res.result:
                self.error.log_msg = res.error
                if self.error.user_msg == '':
                    self.error.user_msg = evmessage.EvMessage().\
                        get_str("TEHNILINE_VIGA_HAALE_VERIFITSEERIMISEL", \
                            evstrings.TEHNILINE_VIGA_HAALE_VERIFITSEERIMISEL)
                self.error.user_code = evcommon.EVOTE_ERROR

                if not res.cert_is_valid:
                    self.error.user_msg = evmessage.EvMessage().\
                        get_str("SERTIFIKAAT_ON_AEGUNUD", \
                            evstrings.SERTIFIKAAT_ON_AEGUNUD)
                    self.error.user_code = evcommon.EVOTE_CERT_ERROR

                return False

            ik_ver = regrights.get_personal_code(res.subject)
            if self._ik != ik_ver:
                self.error.log_msg = \
                    'Autentija (%s) ja allkirjastaja (%s) erinevad' % \
                        (self._ik, ik_ver)
                self.error.user_msg = \
                    evmessage.EvMessage().get_str("ERINEV_KASUTAJA", \
                        evstrings.ERINEV_KASUTAJA)
                self.error.user_code = evcommon.EVOTE_ERROR
                return False

            return True

        except:
            self.error.user_msg = evmessage.EvMessage().\
                get_str("TEHNILINE_VIGA_HAALE_VERIFITSEERIMISEL", \
                    evstrings.TEHNILINE_VIGA_HAALE_VERIFITSEERIMISEL)
            self.error.user_code = evcommon.EVOTE_ERROR
            self.error.log_msg = exception_msg.trace()

        finally:
            bdocpython.terminate()

        return False


class HTSConnector:

    def __init__(self, params):
        self._params = params
        self.error = HESResult()
        self.answer = []

    def work_strict(self):
        if self.work():
            if len(self.answer) == 3:
                return True
        return False

    def work(self):
        querystr = self._params.keys()
        encoded = urllib.urlencode(self._params)
        try:
            conn = httplib.HTTPConnection(Election().get_hts_ip())
            conn.request(evcommon.HTTP_POST, \
                Election().get_hts_path(), encoded, HEADERS)
            response = conn.getresponse()
            respstr = response.read()
            conn.close()

            if respstr.endswith('\n'):
                self.answer = respstr[:-1].split('\n')
            else:
                self.answer = respstr.split('\n')

        except Exception, ex:
            self.error.set_log_msg(\
                'Suhtlus HES ja HTS vahel ebaõnnestus: %s' % str(ex))
            return False

        #Teeme veateate valmis. Kui viga ei ole, siis teadet ei vaadata
        self.error.set_log_msg(\
            'Ebakorrektne vastus HTSilt. Saatsin (%s), sain (%s)' % \
                (querystr, self.answer))

        if len(self.answer) < 3:
            return False

        if evcommon.VERSION != self.answer[0]:
            return False

        if not self.answer[1] in ['0', '1', '2', '3', '4']:
            return False

        return True



class CandidateListExtractor:

    def __init__(self, ik, uid, pname):
        self._ik = ik
        self._list = []
        self._name_type = ''
        self._unique_id = uid
        self._pname = pname

    def compose_list(self):
        questions = Election().get_questions_obj('hes')
        for quest in questions:
            voter = quest.get_voter(self._ik)
            if voter == None:
                continue
            self._name_type = \
                self._name_type + quest.qname() + ':' + \
                    str(quest.get_type()) + '\t'
            kandidaadid = quest.choices_to_voter(voter)
            self._list.append(kandidaadid)

    def has_list(self):
        return (len(self._list) > 0)

    def get_list(self):
        res = self._name_type + '\n'
        res = res + self._unique_id + '\n'
        res = res + self._pname + '\t' + self._ik + '\n'
        for el in self._list:
            res = res + el
        return res[:-1]

class HES:

    def __init__(self):
        evlog.AppLog().set_app('HES')

    def __return_error(self, hes_error):
        if hes_error.log_msg:
            evlog.log_error(hes_error.log_msg)
        return hes_error.user_code, hes_error.user_msg

    def get_candidate_list(self, valid_person):
        ik = valid_person[0]
        en = valid_person[1]
        pn = valid_person[2]
        evlog.AppLog().set_person(ik)
        evlog.log('Kandidaatide nimekiri: %s %s' % (en, pn))
        cld = CandidateListExtractor(
                ik, sessionid.voting(), "%s %s" % (en, pn))
        cld.compose_list()
        if cld.has_list():
            return evcommon.EVOTE_OK, cld.get_list()

        error = HESResult()
        error.pole_valija(ik)
        return self.__return_error(error)

    def hts_vote(self, valid_person, vote):
        ik = valid_person[0]
        en = valid_person[1]
        pn = valid_person[2]

        evlog.AppLog().set_person(ik)

        import base64
        decoded_vote = base64.decodestring(vote)

        evlog.log('Hääle talletamine: %s %s' % (en, pn))
        if not Election().can_vote(ik):
            error = HESResult()
            error.pole_valija(ik)
            return self.__return_error(error)

        inspector = VoteChecker(decoded_vote, ik)
        mobid = False
        if 'MOBILE_ID_CONTEXT' in os.environ:
            mobid = True

        if not inspector.check_vote(mobid):
            return self.__return_error(inspector.error)

        params = {}
        params[evcommon.POST_EVOTE] = vote
        params[evcommon.POST_PERSONAL_CODE] = ik
        params[evcommon.POST_VOTERS_FILES_SHA1] = \
            Election().get_voters_files_sha1()
        params[evcommon.POST_SESS_ID] = sessionid.voting()

        hts_connector = HTSConnector(params)
        if not hts_connector.work_strict():
            return self.__return_error(hts_connector.error)

        return hts_connector.answer[1], hts_connector.answer[2]

    def hts_repeat_check(self, valid_person):
        ik = valid_person[0]
        evlog.AppLog().set_person(ik)
        evlog.log('Korduvhääletuse kontroll')

        params = {}
        params[evcommon.POST_PERSONAL_CODE] = ik
        params[evcommon.POST_VOTERS_FILES_SHA1] = \
            Election().get_voters_files_sha1()
        params[evcommon.POST_SESS_ID] = sessionid.voting()

        hts_connector = HTSConnector(params)
        if not hts_connector.work():
            hts_connector.error.user_code = evcommon.EVOTE_REPEAT_ERROR
            return self.__return_error(hts_connector.error)

        retcode = hts_connector.answer[1]
        ans = '<br>'.join(hts_connector.answer[2:])
        return retcode, ans

    def hts_consistency_check(self):
        sha1 = Election().get_voters_files_sha1()
        if len(sha1) > 0:
            params = {evcommon.POST_VOTERS_FILES_SHA1: sha1}
            hts_connector = HTSConnector(params)
            if not hts_connector.work_strict():
                hts_connector.error.user_code = \
                    evcommon.EVOTE_CONSISTENCY_ERROR
                return self.__return_error(hts_connector.error)
            return hts_connector.answer[1], hts_connector.answer[2]
        else:
            error = HESResult()
            error.user_code = evcommon.EVOTE_CONSISTENCY_ERROR
            error.log_msg = 'POST_VOTERS_FILES_SHA1 parameeter oli (null)'
            return self.__return_error(error)


if __name__ == '__main__':

    print 'No main'


# vim:set ts=4 sw=4 et fileencoding=utf8:
