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

"""
Häälteedastusserveri dispetsher (HESDispatch)

Hääleedastusserveri dispetsher on klass
läbi mille saab kasutada HES protokollis
määratud funktsionaalsust.

Kandidaatide nimekirja tõmbamine (VR <> HES <> HTS)
Hääle talletamisele saatmine (VR <> HES <> HTS)
HTS kooskõlalisuse kontroll (HES <> HTS)

Kogu VR suunast tulevasse infosse tuleb suhtuda kriitiliselt!
Pole võimalik eeldada, et kui kandidaatide nimekiri tõmmati,
siis on hääle talletamiseks kontrollid tehtud.

Kogu VR suunas minevasse infosse tuleb suhtuda kriitiliselt.
"""

import os
from election import Election
from election import ElectionState
import evlog
import evcommon
import evmessage
import protocol
import hes
import subprocess
import birthday
import sessionid
import time

TASK_CAND = 'cand'
TASK_VOTE = 'vote'

STR_CAND = 'Kandidaatide nimekiri'
STR_VOTE = 'Hääle edastamine talletamiseks'

LOGSIG = {TASK_CAND: STR_CAND, TASK_VOTE: STR_VOTE}


def client_cert():
    return os.environ[evcommon.HTTP_CERT]


def is_valid_id_cert():
    """Verifitseerib hääletaja sertifkaadi vastavust (ahelat) süsteemi
    laaditud sertifikaatidega.

    @return True kui sertifikaat verifitseerub, vastasel korral False
    @throws Exception kui viga sertifikaadi lugemisel
    """

    proc = subprocess.Popen(
        ['openssl', 'verify', '-CApath', Election().get_bdoc_ca()],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        close_fds=True)

    proc.stdin.write(client_cert())
    proc.stdin.close()
    errlst = proc.stderr.readlines()
    reslst = proc.stdout.readlines()
    proc.stderr.close()
    proc.stdout.close()
    if errlst:
        err_data = ''
        if client_cert():
            err_data = client_cert()[:100]
        raise Exception('Viga autentimissertifikaadi verifitseerimisel: '
                        '%s, INPUT: %s' % (errlst, err_data))

    if len(reslst) != 1 and reslst[0].strip()[-2:].upper() != "OK":
        return False, ''.join(reslst)
    return True, ''


def cert_info():
    """Tagastab autentimissertifikaadist kasutaja info.

    @returns sertifikaadile vastav ik, en, pn
    @throws Exception kui viga sertifikaadi lugemisel
    """
    # See tagastab kogu kraami utf8 kodeeringus

    proc = subprocess.Popen(
        ['openssl', 'x509', '-subject', '-noout',
         '-nameopt', 'sep_multiline', '-nameopt', 'utf8'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        close_fds=True)

    proc.stdin.write(client_cert())
    proc.stdin.close()
    errlst = proc.stderr.readlines()
    reslst = proc.stdout.readlines()
    proc.stderr.close()
    proc.stdout.close()

    if errlst:
        raise Exception(
            'Viga autentimissertifikaadist info lugemisel: %s' % errlst)

    pn = None
    en = None
    ik = None
    org = None

    for el in reslst:
        tmp = el.strip().split('=')
        if len(tmp) != 2:
            raise Exception('Sobimatu autentimissertifikaat A')

        if tmp[0] == 'CN':
            lst = tmp[1].split(',')
            if len(lst) != 3:
                raise Exception('Sobimatu autentimissertifikaat B')

            # Kõik openssl'i poolt tagastatav info on juba õiges
            # kodeeringus
            pn = lst[0].strip()
            en = lst[1].strip()
            ik = lst[2].strip()

        if tmp[0] == 'O':
            if not tmp[1] in ['ESTEID',
                              'ESTEID (DIGI-ID)',
                              'ESTEID (MOBIIL-ID)',
                              'ESTEID (DIGI-ID E-RESIDENT)',
                              'ESTEID (MOBIIL-ID E-RESIDENT)']:
                raise Exception('Sobimatu autentimissertifikaat C')

            org = tmp[1]

    if ik is None or en is None or pn is None or org is None:
        raise Exception('Sobimatu autentimissertifikaat D')

    return ik, en, pn, org


class CertAnalyzer:

    """
    Turvamees peab töötama nii get_candidate_list kui ka hts_vote ees,
    sest muidu pole võimalik garanteerida, et kõik valijarakendused protokolli
    järgivad. Turvamehe errmsg peab sobima tavakasutajale saatmiseks.
    Exceptionid lendavad läbi ja logitakse kasutavas klassis
    """

    def __init__(self):
        self._ik = ''
        self._en = ''
        self._pn = ''
        self.errcode = evcommon.EVOTE_ERROR
        self.errmsg = ''
        self.logmsg = ''

    def work(self):

        valid, msg = is_valid_id_cert()
        if not valid:
            self.logmsg = msg
            self.errcode = evcommon.EVOTE_CERT_ERROR
            self.errmsg = evmessage.EV_ERRORS.EBASOBIV_SERTIFIKAAT
            return False

        self._ik, self._en, self._pn, org = cert_info()
        if not birthday.is_18(self._ik):
            self.errcode = evcommon.EVOTE_ERROR
            self.errmsg = evmessage.EV_ERRORS.POLE_18
            self.logmsg = self.errmsg
            return False

        if org in ['ESTEID (DIGI-ID E-RESIDENT)',
                   'ESTEID (MOBIIL-ID E-RESIDENT)']:
            self.errcode = evcommon.EVOTE_ERROR
            self.errmsg = evmessage.EV_ERRORS.E_RESIDENT
            self.logmsg = self.errmsg
            return False

        return True

    def valid_person(self):
        return self._ik, self._en, self._pn


class SessionContext:

    def __init__(self, sessid):
        if not sessid:
            raise ValueError("Missing sessid")
        self.__key = [evcommon.IDSPOOL, sessid]
        self.__reg = Election().get_root_reg()

    def store_session(self, cert):
        self.__reg.ensure_key(self.__key)
        self.__reg.create_value(self.__key, "cert", cert)
        self.__reg.create_integer_value(self.__key, "start", int(time.time()))

    def check_session(self, cert):
        if not self.__reg.check(self.__key):
            return evcommon.EVOTE_ERROR, evmessage.EV_ERRORS.SEANSS_PUUDUB

        start = self.__reg.read_integer_value(self.__key, "start").value
        length = Election().get_session_length() * 60
        if start + length < int(time.time()):
            return evcommon.EVOTE_ERROR, evmessage.EV_ERRORS.SEANSS_PUUDUB

        if self.__reg.read_value(self.__key, "cert").value != cert:
            evlog.log_error('Sertifikaat muutus')
            return evcommon.EVOTE_CERT_ERROR, evmessage.EV_ERRORS.TEHNILINE_VIGA

        return evcommon.EVOTE_OK, None

    def kill(self):
        self.__reg.ensure_no_key(self.__key)


class HESVoterDispatcher:

    def __init__(self, use_ctx=True):
        self.__hes = hes.HES()
        self.__task = TASK_CAND
        self.__use_ctx = use_ctx
        self.__ctx = None

    def ctx(self):
        # Can't be initialized in __init__, because sessionid.voting() is
        # subject to change before the first time ctx is used.
        if self.__use_ctx and not self.__ctx:
            self.__ctx = SessionContext(sessionid.voting())
        return self.__ctx

    def __return_exception(self):
        evlog.log_exception()
        r1, r2 = protocol.plain_error_technical(evcommon.EVOTE_ERROR)
        return self.__return_error(r1, r2)

    def __return_error(self, errcode, msg):
        evlog.log_error('Viga operatsioonil "%s", teade "%s"' %
                        (self.__task, msg))
        if self.__ctx:
            self.__ctx.kill()
        return protocol.msg_error(errcode, msg)

    def __get_candidate_list(self, valid_person):
        cand_ok, cand_msg = self.__hes.get_candidate_list(valid_person)

        if not cand_ok == evcommon.EVOTE_OK:
            return self.__return_error(cand_ok, cand_msg)

        korduv_ret, korduv_msg = self.__hes.hts_repeat_check(valid_person)

        if korduv_ret == evcommon.EVOTE_REPEAT_NO:
            evlog.log('Kandidaatide nimekiri väljastati A')
            if self.__use_ctx:
                self.ctx().store_session(client_cert())
            return protocol.msg_ok(cand_msg)
        elif korduv_ret == evcommon.EVOTE_REPEAT_YES:
            evlog.log('Kandidaatide nimekiri väljastati B')
            if self.__use_ctx:
                self.ctx().store_session(client_cert())
            return protocol.msg_repeat(cand_msg, korduv_msg)
        elif korduv_ret == evcommon.EVOTE_REPEAT_NOT_CONSISTENT:
            r1, r2 = protocol.plain_error_maintainance()
            return self.__return_error(r1, r2)
        else:
            return self.__return_error(evcommon.EVOTE_ERROR, korduv_msg)

    def __hts_vote(self, valid_person, vote, votebox):
        if self.__use_ctx:
            sess_ok, sess_msg = self.ctx().check_session(client_cert())
            if not sess_ok == evcommon.EVOTE_OK:
                return self.__return_error(sess_ok, sess_msg)

        import vote_analyzer
        ik = valid_person[0]
        evlog.log_integrity(vote_analyzer.analyze(ik, vote, votebox))
        res_ok, res = self.__hes.hts_vote(valid_person, vote)
        if res_ok == evcommon.EVOTE_OK:
            if self.__use_ctx:
                self.ctx().kill()
            return protocol.msg_ok(res)
        else:
            return self.__return_error(res_ok, res)

    def __proxy(self, vote=None, votebox=None):
        try:
            evlog.log(LOGSIG[self.__task] + ': ALGUS')
            if ElectionState().election_on():
                security = CertAnalyzer()
                if security.work():
                    if self.__task == TASK_CAND:
                        return \
                            self.__get_candidate_list(security.valid_person())
                    elif self.__task == TASK_VOTE:
                        return self.__hts_vote(
                            security.valid_person(), vote, votebox)
                    else:
                        r1, r2 = protocol.msg_error_technical()
                        return self.__return_error(r1, r2)
                else:
                    evlog.log_error('Viga: "%s"' % security.logmsg)
                    return \
                        self.__return_error(security.errcode, security.errmsg)
            else:
                r1, r2 = ElectionState().election_off_msg()
                return self.__return_error(r1, r2)
        except:
            return self.__return_exception()
        finally:
            evlog.log(LOGSIG[self.__task] + ': LõPP')

    def get_candidate_list(self):
        self.__task = TASK_CAND
        return self.__proxy()

    def hts_vote(self, vote, votebox=None):
        self.__task = TASK_VOTE
        return self.__proxy(vote, votebox)


class HESDispatcher:

    def __init__(self):
        self.__hes = hes.HES()

    def __return_exception(self, errcode):
        evlog.log_exception()
        return protocol.plain_error_technical(errcode)

    def hts_consistency_check(self):
        try:
            evlog.log('HES ja HTS kooskõlalisuse kontroll: ALGUS')
            return self.__hes.hts_consistency_check()
        except:
            return self.__return_exception(evcommon.EVOTE_CONSISTENCY_ERROR)
        finally:
            evlog.log('HTS kooskõlalisuse kontroll: LõPP')


if __name__ == '__main__':
    print 'No main'

# vim:set ts=4 sw=4 et fileencoding=utf8:
