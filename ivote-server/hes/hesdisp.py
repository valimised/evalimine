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

"""
Häälteedastusserveri dispetsher (HESDispatch)

Hääleedastusserveri dispetsher on klass
läbi mille saab kasutada HES protokollis
määratud funktsionaalsust.

Kandidaatide nimekirja tõmbamine (VR <> HES <> HTS)
Hääle talletamisele saatmine (VR <> HES <> HTS)
HTS kooskõlalisuse kontroll (HES <> HTS)

Kogu VR suunast tulevasse infosse tuleb suhtuda kriitiliselt!
Ei saa eeldada, et kui kandidaatide nimekiri tõmmati,
siis on hääle talletamiseks kontrollid tehtud.

Kogu VR suunas minevasse infosse tuleb suhtuda kriitiliselt.
"""

import os
from election import Election
from election import ElectionState
import evlog
import evcommon
import evmessage
import evstrings
import protocol
import hes
import subprocess
import birthday

TASK_CAND = 'cand'
TASK_VOTE = 'vote'

STR_CAND = 'Kandidaatide nimekiri'
STR_VOTE = 'Hääle edastamine talletamiseks'

LOGSIG = {TASK_CAND : STR_CAND, TASK_VOTE : STR_VOTE}

def is_valid_id_cert():
    """Verifitseerib hääletaja sertifkaadi vastavust (ahelat) süsteemi
    laetud sertifikaatidega.

    @return True kui sertifikaat verifitseerub, vastasel korral False
    @throws Exception kui viga sertifikaadi lugemisel
    """

    proc = subprocess.Popen(\
        ['openssl', 'verify', '-CApath', Election().get_bdoc_ca()],\
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\
        close_fds=True)

    proc.stdin.write(os.environ[evcommon.HTTP_CERT])
    proc.stdin.close()
    errlst = proc.stderr.readlines()
    reslst = proc.stdout.readlines()
    proc.stderr.close()
    proc.stdout.close()
    if len(errlst) > 0:
        err_data = ''
        if (len(os.environ[evcommon.HTTP_CERT]) > 0):
            err_data = os.environ[evcommon.HTTP_CERT][:100]
        raise Exception('Viga autentimissertifikaadi verifitseerimisel: '\
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

    proc = subprocess.Popen(\
        ['openssl', 'x509', '-subject', '-noout', \
        '-nameopt', 'sep_multiline', '-nameopt', 'utf8'], \
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\
        close_fds=True)

    proc.stdin.write(os.environ[evcommon.HTTP_CERT])
    proc.stdin.close()
    errlst = proc.stderr.readlines()
    reslst = proc.stdout.readlines()
    proc.stderr.close()
    proc.stdout.close()

    if len(errlst) > 0:
        raise Exception(\
            'Viga autentimissertifikaadist info lugemisel: %s' % errlst)

    for el in reslst:
        tmp = el.strip().split('=')
        if len(tmp) != 2:
            raise Exception('Sobimatu autentimissertifikaat')

        if tmp[0] != 'CN':
            continue

        lst = tmp[1].split(',')
        if len(lst) != 3:
            raise Exception('Sobimatu autentimissertifikaat')

        # Kõik openssl'i poolt tagastatav info on juba õiges
        # kodeeringus
        pn = lst[0].strip()
        en = lst[1].strip()
        ik = lst[2].strip()

        return ik, en, pn


class CertAnalyzer:

    """
    Turvamees peab töötama nii get_candidate_list kui ka hts_vote ees,
    sest ei saa garanteerida, et kõik valijarakendused protokolli järgivad.
    Turvamehe errmsg peab sobima tavakasutajale saatmiseks.
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
            self.errmsg = evmessage.EvMessage().\
                get_str("SERTIFIKAAT_POLE_SELLE_CA_POOLT_VALJA_ANTUD", \
                    evstrings.SERTIFIKAAT_POLE_SELLE_CA_POOLT_VALJA_ANTUD)
            return False

        self._ik, self._en, self._pn = cert_info()
        if not birthday.is_18(self._ik):
            self.errcode = evcommon.EVOTE_ERROR
            self.errmsg = evmessage.EvMessage().\
                get_str("POLE_18", evstrings.POLE_18)
            self.logmsg = self.errmsg
            return False

        return True

    def valid_person(self):
        return self._ik, self._en, self._pn


class HESVoterDispatcher:

    def __init__(self):
        self.__hes = hes.HES()
        self.__task = TASK_CAND

    def __return_exception(self):
        evlog.log_exception()
        r1, r2 = protocol.plain_error_technical(evcommon.EVOTE_ERROR)
        return self.__return_error(r1, r2)

    def __return_error(self, errcode, msg):
        evlog.log_error('Viga operatsioonil "%s", teade "%s"' %\
                (self.__task, msg))
        return protocol.msg_error(errcode, msg)

    def __get_candidate_list(self, valid_person):
        cand_ok, cand_msg = self.__hes.get_candidate_list(valid_person)

        if not cand_ok == evcommon.EVOTE_OK:
            return self.__return_error(cand_ok, cand_msg)

        korduv_ret, korduv_msg = self.__hes.hts_repeat_check(valid_person)

        if korduv_ret == evcommon.EVOTE_REPEAT_NO:
            evlog.log('Kandidaatide nimekiri väljastati A')
            return protocol.msg_ok(cand_msg)
        elif korduv_ret == evcommon.EVOTE_REPEAT_YES:
            evlog.log('Kandidaatide nimekiri väljastati B')
            return protocol.msg_repeat(cand_msg, korduv_msg)
        elif korduv_ret == evcommon.EVOTE_REPEAT_NOT_CONSISTENT:
            r1, r2 = protocol.plain_error_maintainance()
            return self.__return_error(r1, r2)
        else:
            return self.__return_error(evcommon.EVOTE_ERROR, korduv_msg)

    def __hts_vote(self, valid_person, vote, votebox):
        import vote_analyzer
        ik = valid_person[0]
        evlog.log_integrity(vote_analyzer.analyze(ik, vote, votebox))
        res_ok, res = self.__hes.hts_vote(valid_person, vote)
        if res_ok == evcommon.EVOTE_OK:
            return protocol.msg_ok(res)
        else:
            return self.__return_error(res_ok, res)

    def __proxy(self, vote = None, votebox = None):
        try:
            evlog.log(LOGSIG[self.__task] + ': ALGUS')
            if ElectionState().election_on():
                security = CertAnalyzer()
                if security.work():
                    if self.__task == TASK_CAND:
                        return \
                            self.__get_candidate_list(security.valid_person())
                    elif self.__task == TASK_VOTE:
                        return self.__hts_vote(\
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

    def hts_vote(self, vote, votebox = None):
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
