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

import htsall
from election import ElectionState
from evlog import AppLog
import evreg
import sys
import evcommon
import evstrings
from evmessage import EvMessage
from evmessage import EV_ERRORS
import time


def __return_message(result, message):
    return evcommon.VERSION + '\n' + result + '\n' + message


def consistency(sha_in):
    _htsd = HTSAllDispatcher()
    ret = _htsd.kooskolaline(sha_in)
    return __return_message(ret, '')


def check_repeat(sha_in, code_in):
    _htsd = HTSAllDispatcher()
    ret = evcommon.EVOTE_REPEAT_ERROR
    msg = EV_ERRORS.TEHNILINE_VIGA

    AppLog().set_person(code_in)
    ret_cons = _htsd.kooskolaline(sha_in)

    if ret_cons == evcommon.EVOTE_CONSISTENCY_NO:
        ret = evcommon.EVOTE_REPEAT_NOT_CONSISTENT
        msg = EV_ERRORS.HOOLDUS
    elif ret_cons == evcommon.EVOTE_CONSISTENCY_YES:
        ok, ret_rep, msg_rep = _htsd.haaletanud(code_in)
        if ok:
            if ret_rep:
                ret = evcommon.EVOTE_REPEAT_YES
            else:
                ret = evcommon.EVOTE_REPEAT_NO
        msg = msg_rep

    return __return_message(ret, msg)


def store_vote(sha_in, code_in, vote_in):

    _htsd = HTSAllDispatcher()
    ret = evcommon.EVOTE_ERROR
    msg = EV_ERRORS.TEHNILINE_VIGA

    ret_cons = _htsd.kooskolaline(sha_in)
    if ret_cons == evcommon.EVOTE_CONSISTENCY_NO:
        ret = evcommon.EVOTE_ERROR
        msg = EV_ERRORS.HOOLDUS
    elif ret_cons == evcommon.EVOTE_CONSISTENCY_YES:
        AppLog().set_person(code_in)
        ret, msg = _htsd.talleta_base64(vote_in)
    else:
        ret = evcommon.EVOTE_ERROR
        msg = EV_ERRORS.TEHNILINE_VIGA
    return __return_message(ret, msg)


def verify_vote(vote_id):
    _htsd = HTSAllDispatcher()
    ret, msg = _htsd.verify(vote_id)
    return __return_message(ret, msg)


class HTSAllDispatcher:

    def __init__(self):
        AppLog().set_app('HTS-ALL')
        self.__all = htsall.HTSAll()

    def kooskolaline(self, voters_files_sha256):
        try:
            try:
                #AppLog().log('HES ja HTS kooskõlalisuse kontroll: ALGUS')
                if self.__all.kooskolaline(voters_files_sha256):
                    return evcommon.EVOTE_CONSISTENCY_YES
                else:
                    AppLog().log_error('HES ja HTS ei ole kooskõlalised')
                    return evcommon.EVOTE_CONSISTENCY_NO
            except:
                AppLog().log_exception()
                return evcommon.EVOTE_CONSISTENCY_ERROR
        finally:
            pass
            #AppLog().log('HES ja HTS kooskõlalisuse kontroll: LõPP')

    def haaletanud(self, ik):
        try:
            try:
                AppLog().log('Korduvhääletuse kontroll: ALGUS')
                if ElectionState().election_on():
                    ok, msg = self.__all.haaletanud(ik)
                    return True, ok, msg

                r1, msg = ElectionState().election_off_msg()
                AppLog().log_error(msg)
                return False, False, msg
            except:
                AppLog().log_exception()
                return False, False, EV_ERRORS.TEHNILINE_VIGA
        finally:
            AppLog().log('Korduvhääletuse kontroll: LõPP')

    def talleta_base64(self, data):
        try:
            try:
                AppLog().log('Hääle talletamine: ALGUS')
                if ElectionState().election_on():
                    return self.__all.talleta_base64(data)

                r1, msg = ElectionState().election_off_msg()
                AppLog().log_error(msg)
                return evcommon.EVOTE_ERROR, msg
            except:
                AppLog().log_exception()
                return evcommon.EVOTE_ERROR, EV_ERRORS.TEHNILINE_VIGA
        finally:
            AppLog().log('Hääle talletamine: LõPP')

    def status(self, fo, verify=True):
        p_time = "00:00:00"

        try:
            try:
                s_time = time.time()
                AppLog().log('Vaheauditi aruanne: ALGUS')
                self.__all.status(fo, verify)
                p_time = time.strftime("%H:%M:%S",
                        time.gmtime(long(time.time() - s_time)))

                return 'Vaheauditi aruanne koostatud. Aega kulus %s.' % p_time
            except:
                AppLog().log_exception()
                return 'Tehniline viga vaheauditi aruande koostamisel'
        finally:
            AppLog().log('Vaheauditi aruanne (%s): LõPP' % p_time)

    def verify(self, vote_id):
        try:
            AppLog().log("Vote verification: START")
            if ElectionState().election_on():
                return self.__all.verify(vote_id)

            ret, msg = ElectionState().election_off_msg()
            AppLog().log_error(msg)
            return evcommon.VERIFY_ERROR, msg
        except:
            AppLog().log_exception()
            return evcommon.VERIFY_ERROR, EvMessage().get_str(
                    "TECHNICAL_ERROR_VOTE_VERIFICATION",
                    evstrings.TECHNICAL_ERROR_VOTE_VERIFICATION)
        finally:
            AppLog().log("Vote verification: END")


def talleta(base64_fail, htsd):
    try:
        _if = file(base64_fail, "rb")
        data = _if.read()
        return htsd.talleta_base64(data)
    finally:
        _if.close()


def usage():
    print "Kasutamine:"
    print "    %s haaletanud <isikukood>" % sys.argv[0]
    print \
        "        - kontrollib isikukoodi järgi, kas isik on juba hääletanud"
    print "    %s talleta <failinimi>" % sys.argv[0]
    print "        - talletab ddoc e-haale"
    print "    %s status" % sys.argv[0]
    print "        - kuvab infot e-hääletuste staatuse kohta"

    sys.exit(1)


def main_function():
    if len(sys.argv) < 2:
        usage()

    if not sys.argv[1] in \
        ['haaletanud', 'talleta', 'status', 'statusnoverify']:
        usage()

    if sys.argv[1] in ['haaletanud', 'talleta'] and len(sys.argv) < 3:
        usage()

    htsd = None

    try:
        htsd = HTSAllDispatcher()

        if sys.argv[1] == 'haaletanud':
            res, _ok, _msg = htsd.haaletanud(sys.argv[2])
            if not res:
                print 'Viga korduvhääletuse kontrollimisel'
            print _msg
            if _ok:
                sys.exit(0)
            sys.exit(1)
        elif sys.argv[1] == 'talleta':
            res, _msg = talleta(sys.argv[2], htsd)
            print _msg
            if res:
                sys.exit(0)
            sys.exit(1)
        elif sys.argv[1] == 'status':
            reg = evreg.Registry(root=evcommon.EVREG_CONFIG)
            status_file = reg.path(['common', evcommon.STATUSREPORT_FILE])
            _ff = file(status_file, 'w')
            try:
                res = htsd.status(_ff)
                _ff.write(res + "\n")
            finally:
                _ff.close()
        elif sys.argv[1] == 'statusnoverify':
            reg = evreg.Registry(root=evcommon.EVREG_CONFIG)
            status_file = reg.path(['common', evcommon.STATUSREPORT_FILE])
            _ff = file(status_file, 'w')
            try:
                res = htsd.status(_ff, False)
                _ff.write(res + "\n")
            finally:
                _ff.close()
        else:
            usage()

    except SystemExit:
        raise
    except Exception as _e:
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
