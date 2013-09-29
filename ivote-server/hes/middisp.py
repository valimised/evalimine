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
import binascii
import httplib
import base64
import StringIO

from DigiDocService_client import *

from election import Election
from election import ElectionState
import evlog
import evlogdata
import sessionid
import evcommon
import protocol
import hesdisp

def get_mid_text(status):
    import evmessage
    import evstrings

    if status == 'MID_NOT_READY':
        return evmessage.EvMessage(). \
                 get_str("MID_NOT_READY", evstrings.MID_NOT_READY)

    elif status == 'USER_CANCEL':
        return evmessage.EvMessage(). \
                 get_str("MID_USER_CANCEL", evstrings.MID_USER_CANCEL)

    elif status == 'PHONE_ABSENT':
        return evmessage.EvMessage(). \
                 get_str("MID_PHONE_ABSENT", evstrings.MID_PHONE_ABSENT)

    elif status == 'SENDING_ERROR':
        return evmessage.EvMessage(). \
                 get_str("MID_SENDING_ERROR", evstrings.MID_SENDING_ERROR)

    elif status == 'SIM_ERROR':
        return evmessage.EvMessage(). \
                 get_str("MID_SIM_ERROR", evstrings.MID_SIM_ERROR)

    elif status == 'INTERNAL_ERROR':
        return evmessage.EvMessage(). \
                 get_str("MID_INTERNAL_ERROR", evstrings.MID_INTERNAL_ERROR)

    elif status == 'MID_ERROR_301':
        return evmessage.EvMessage(). \
                 get_str("MID_ERROR_301", evstrings.MID_ERROR_301)

    elif status in ['MID_ERROR_302', 'REVOKED', 'SUSPENDED']:
        return evmessage.EvMessage(). \
                 get_str("MID_ERROR_302", evstrings.MID_ERROR_302)

    elif status in ['MID_ERROR_303', 'NOT_ACTIVATED']:
        return evmessage.EvMessage(). \
                 get_str("MID_ERROR_303", evstrings.MID_ERROR_303)

    elif status == 'MID_POLICY':
        return evmessage.EvMessage(). \
                 get_str("MID_POLICY", evstrings.MID_POLICY)

    return evmessage.EvMessage(). \
                 get_str("MID_UNKNOWN_ERROR", evstrings.MID_UNKNOWN_ERROR)



def mobid_vote_data(b64vote):

    import bdocpythonutils

    bdocdata = base64.b64decode(b64vote)
    bdocfile = None

    try:
        bdocfile = StringIO.StringIO(bdocdata)
        bdoc = bdocpythonutils.BDocContainer()
        bdoc.load(bdocfile)
        bdoc.validateflex()
        _doc_count = len(bdoc.documents)
        if _doc_count == 0:
            raise Exception, "BDoc ei sisalda ühtegi andmefaili"
        ret = {}
        for el in bdoc.documents:
            evlog.log(evlogdata.get_vote(el, bdoc.documents[el]))
            ret[el] = base64.b64encode(bdoc.documents[el])

        return ret

    finally:
        if bdocfile != None:
            bdocfile.close()


def challenge_ok(b64cert, mychal, ourchal, signature):

    import bdocpython
    if not signature:
        return False, 'DDS did not return signed challenge'

    bmychal = binascii.a2b_hex(mychal)
    bchal = binascii.a2b_hex(ourchal)

    if (bmychal != bchal[0:10]):
        return False, 'My challenge not present in our challenge'

    bcert = binascii.a2b_base64(b64cert)
    bsign = binascii.a2b_base64(signature)

    cv = bdocpython.ChallengeVerifier()
    cv.setCertificate(bcert)
    cv.setChallenge(bchal)
    cv.setSignature(bsign)
    res = cv.isChallengeOk()

    if not res:
        return False, cv.error

    return True, None


def cert_ok(incert):
    import bdocpythonutils
    conf = bdocpythonutils.BDocConfig()
    conf.load(Election().get_bdoc_conf())

    b64cert = incert.replace('-----BEGIN CERTIFICATE-----', '').\
        replace('-----END CERTIFICATE-----', '')

    return conf.is_good_mid_cert(b64cert)


class MobileIDContext:

    phoneno = None
    lang = None
    challenge = None
    midsess = None
    origvote = None
    votefiles = {}
    __sessid = None
    __reg = None

    def __init__(self, sessid):
        if sessid == None:
            raise Exception('Puuduv sessiooniidentifikaator')
        self.__sessid = sessid
        self.__reg = Election().get_root_reg()
        self.lang = 'EST'

    def sessid(self):
        return self.__sessid

    def kill(self):
        self.__reg.ensure_no_key([evcommon.MIDSPOOL, self.__sessid])

    def set_phone(self, phone):
        self.phoneno = phone

    def set_origvote(self, hv):
        self.origvote = hv

    def get_origvote(self):
        self.origvote = self.__reg.read_value(\
                            [evcommon.MIDSPOOL, self.__sessid], \
                                                    'origvote').value
        return self.origvote

    def add_votefile(self, filename, data):
        self.votefiles[filename] = data

    def get_votefiles(self):
        for key in self.__reg.list_keys([evcommon.MIDSPOOL, self.__sessid, \
                'votefiles']):
            self.votefiles[key] = self.__reg.read_value(\
                    [evcommon.MIDSPOOL, self.__sessid, 'votefiles'], key).value
        return self.votefiles

    def generate_challenge(self):
        self.challenge = binascii.b2a_hex(os.urandom(10))

    def verify_challenge(self, signature):
        return challenge_ok(self.certificate(), self.mychallenge(), \
                            self.ourchallenge(), signature)

    def mychallenge(self):
        return self.__reg.read_value(\
                            [evcommon.MIDSPOOL, self.__sessid], \
                                    'mychallenge').value

    def ourchallenge(self):
        return self.__reg.read_value(\
                            [evcommon.MIDSPOOL, self.__sessid], \
                                    'ourchallenge').value

    def certificate(self):
        return self.__reg.read_value(\
                            [evcommon.MIDSPOOL, self.__sessid], \
                                    'cert').value

    def set_auth_succ(self):
        self.__reg.ensure_key([evcommon.MIDSPOOL, self.__sessid, 'authsucc'])

    def auth_succ(self):
        return self.__reg.check(\
                [evcommon.MIDSPOOL, self.__sessid, 'authsucc'])

    def save_post_auth(self, rsp):

        self.__reg.reset_key([evcommon.MIDSPOOL, self.__sessid])
        self.__reg.create_value([evcommon.MIDSPOOL, self.__sessid], \
                        'cert', rsp._CertificateData)

        self.__reg.create_value([evcommon.MIDSPOOL, self.__sessid], \
                        'phone', self.phoneno)

        self.__reg.create_value([evcommon.MIDSPOOL, self.__sessid], \
                        'midsess', rsp._Sesscode)

        self.__reg.create_value([evcommon.MIDSPOOL, self.__sessid], \
                        'mychallenge', self.challenge)

        self.__reg.create_value([evcommon.MIDSPOOL, self.__sessid], \
                        'ourchallenge', rsp._Challenge)

    def load_pre_sign(self):
        self.phoneno = self.__reg.read_value(\
                [evcommon.MIDSPOOL, self.__sessid], 'phone').value

    def save_post_sign(self, midsess):
        self.__reg.create_value([evcommon.MIDSPOOL, self.__sessid], \
                        'midsess', midsess)

        self.__reg.create_value([evcommon.MIDSPOOL, self.__sessid], \
                        'origvote', self.origvote)

        self.__reg.ensure_key([evcommon.MIDSPOOL, self.__sessid, 'votefiles'])
        for el in self.votefiles:
            self.__reg.create_value(\
                    [evcommon.MIDSPOOL, self.__sessid, 'votefiles'],\
                    el, self.votefiles[el])

    def load_pre_poll(self):
        self.midsess = int(self.__reg.read_value(\
                [evcommon.MIDSPOOL, self.__sessid], 'midsess').value)


class MobileIDService:

    url = None
    name = None
    auth_msg = None
    sign_msg = None
    srv = None
    dfs = {}

    def __init__(self):
        os.environ['MOBILE_ID_CONTEXT'] = '1'
        self.url = Election().get_mid_url()
        self.name = Election().get_mid_name()
        self.auth_msg, self.sign_msg = Election().get_mid_messages()
        loc = DigiDocServiceLocator()
        # self.fp = open('/tmp/debug.out', 'a')
        # kw = { 'tracefile': self.fp }
        kw = { }
        self.srv = loc.getDigiDocService(self.url, **kw)

    def add_file(self, name, data):
        self.dfs[name] = data

    def files(self):
        return len(self.dfs)

    def get_cert(self, ctx):
        request = GetMobileCertificate(\
            PhoneNo = ctx.phoneno, \
            ReturnCertData = 'auth')

        return self.srv.GetMobileCertificate(request)

    def init_auth(self, ctx):
        request = MobileAuthenticate(\
                PhoneNo = ctx.phoneno, \
                Language = ctx.lang, \
                ServiceName = self.name, MessageToDisplay = self.auth_msg, \
                SPChallenge = ctx.challenge, \
                MessagingMode = 'asynchClientServer', ReturnCertData = True, \
                ReturnRevocationData = True)

        return self.srv.MobileAuthenticate(request)

    def init_sign(self, ctx):
        import hashlib

        req = StartSession(\
            SigningProfile = '', SigDocXML = None, bHoldSession = True)
        rsp = self.srv.StartSession(req)
        if rsp._Status != 'OK':
            return False, rsp._Status, None

        req2 = CreateSignedDoc(Sesscode = rsp._Sesscode, Format = 'BDOC', \
            Version = '1.0')
        rsp2 = self.srv.CreateSignedDoc(req2)
        if rsp2._Status != 'OK':
            return False, rsp2._Status, None

        for el in self.dfs:
            digest = hashlib.sha256(self.dfs[el]) # pylint: disable=E1101
            req_i = AddDataFile(Sesscode = rsp._Sesscode, FileName = el, \
                MimeType = "application/x-encrypted-vote", Size = 256, \
                DigestType = "sha256", \
                DigestValue = base64.b64encode(digest.digest()), \
                ContentType = "HASHCODE")
            rsp_i = self.srv.AddDataFile(req_i)
            if rsp_i._Status != 'OK':
                return False, rsp_i._Status, None

        req_3 = MobileSign(\
            Sesscode = rsp._Sesscode, \
            SignerPhoneNo = ctx.phoneno, \
            Language = ctx.lang, \
            ServiceName = self.name, SigningProfile = '', \
            AdditionalDataToBeDisplayed = self.sign_msg, \
            MessagingMode = 'asynchClientServer')
        rsp_3 = self.srv.MobileSign(req_3)

        if rsp_3._Status != 'OK':
            return False, rsp_3._Status, None

        return True, rsp._Sesscode, rsp_3._ChallengeID


    def poll_auth(self, ctx):
        request = GetMobileAuthenticateStatus(\
            Sesscode = ctx.midsess, WaitSignature = False)
        return self.srv.GetMobileAuthenticateStatus(request)

    def poll_sign(self, ctx):

        req = GetStatusInfo(Sesscode = ctx.midsess, WaitSignature = False)
        rsp = self.srv.GetStatusInfo(req)

        if rsp._Status != 'OK':
            return rsp._Status, None

        if rsp._StatusCode == 'OUTSTANDING_TRANSACTION':
            return rsp._StatusCode, None

        if rsp._StatusCode != 'SIGNATURE':
            return rsp._StatusCode, None

        req2 = GetSignedDoc(Sesscode = ctx.midsess)
        rsp2 = self.srv.GetSignedDoc(req2)

        req3 = CloseSession(Sesscode = ctx.midsess)
        rsp3 = self.srv.CloseSession(req3)

        if rsp2._Status != 'OK':
            return rsp2._Status, None

        if rsp3._Status != 'OK':
            return rsp3._Status, None

        return rsp._StatusCode, rsp2._SignedDocData


class MIDDispatcher:

    def __init__(self):
        evlog.AppLog().set_app('MID')
        self.__ctx = None

    def ctx(self):
        if not self.__ctx:
            self.__ctx = MobileIDContext(sessionid.voting())
        return self.__ctx

    def __return_exception(self):
        evlog.log_exception()
        r1, r2 = protocol.plain_error_technical(evcommon.EVOTE_MID_ERROR)
        return self.__return_error(r1, r2)

    def __return_error(self, errcode, msg):
        evlog.log_error('Teade Valija rakendusele: "%s"' % msg)
        if self.__ctx:
            self.__ctx.kill()
        return protocol.msg_error(errcode, msg)

    def __return_zsi_error(self, exc):

        fault = "%s" % exc

        evlog.log_error("Exception: %s" % fault)

        # 301 comes from MobileAuthenticate
        # 201 comes from GetMobileCertificate
        # both mean that the user is not MID client
        if fault.startswith('301') or fault.startswith('201'):
            return self.__return_error(evcommon.EVOTE_MID_ERROR, \
                                            get_mid_text('MID_ERROR_301'))

        elif fault.startswith('302'):
            return self.__return_error(evcommon.EVOTE_MID_ERROR, \
                                            get_mid_text('MID_ERROR_302'))

        elif fault.startswith('303'):
            return self.__return_error(evcommon.EVOTE_MID_ERROR, \
                                            get_mid_text('MID_ERROR_303'))

        return self.__return_error(evcommon.EVOTE_MID_ERROR, \
                                            get_mid_text('MID_UNKNOWN_ERROR'))

    def __return_mid_error(self, status):
        return self.__return_error(evcommon.EVOTE_MID_ERROR, \
                                            get_mid_text(status))

    def __return_mid_policy_error(self):
        return self.__return_error(evcommon.EVOTE_MID_POLICY_ERROR, \
                                            get_mid_text('MID_POLICY'))

    def __return_badstatusline_error(self, exc):
        evlog.log_error('Vigane HTTP status-line: "%s"' % exc.line)
        return self.__return_mid_error('MID_UNKNOWN_ERROR')

    def init_sign(self, form):
        try:
            evlog.log('Signeerimispäring: ALGUS')
            if not self.ctx().auth_succ():
                raise Exception('Autentimata sessioon')

            self.ctx().load_pre_sign()
            service = MobileIDService()

            for el in form:
                if el == evcommon.POST_SESS_ID:
                    pass
                elif el == evcommon.POST_EVOTE:
                    b64 = form.getvalue(el)
                    votes = mobid_vote_data(b64)
                    for el in votes:
                        vote = base64.b64decode(votes[el])
                        service.add_file(el, vote)
                        self.ctx().add_votefile(el, vote)
                    self.ctx().set_origvote(b64)
                else:
                    raise Exception('Vigane päringuparameeter %s' % el)

            if service.files() < 1:
                raise Exception('Ei ole hääli, mida signeerida')

            r1, r2, r3 = service.init_sign(self.ctx())

            if r1:
                self.ctx().save_post_sign(r2)
                evlog.log('Signeerimispäring (%s)' % r2)
                return protocol.msg_mobid_sign_init_ok(r3)

            return self.__return_mid_error(r2)

        except httplib.BadStatusLine, exc:
            return self.__return_badstatusline_error(exc)
        except ZSI.FaultException, exc:
            return self.__return_zsi_error(exc)
        except:
            return self.__return_exception()
        finally:
            evlog.log('Signeerimispäring: LÕPP')


    def init_auth(self, phone):

        try:
            evlog.log("Autentimispäring: ALGUS %s" % (phone))
            if not ElectionState().election_on():
                r1, r2 = ElectionState().election_off_msg()
                return protocol.msg_error(r1, r2)

            self.ctx().set_phone(phone)
            self.ctx().generate_challenge()
            service = MobileIDService()

            rsp_cert = service.get_cert(self.ctx())
            if not (rsp_cert._SignCertStatus == 'OK'):
                return self.__return_mid_error(rsp_cert._SignCertStatus)

            if rsp_cert._AuthCertStatus == 'OK':
                res, err = cert_ok(rsp_cert._AuthCertData)
                if not res:
                    evlog.log_error(err)
                    return self.__return_mid_policy_error()
            else:
                return self.__return_mid_error(rsp_cert._AuthCertStatus)

            rsp = service.init_auth(self.ctx())
            if rsp._Status == 'OK':
                self.ctx().save_post_auth(rsp)

                alog, elog = evlogdata.get_cert_data_log(
                        rsp._CertificateData, 'cand/auth', True)

                evlog.log('Autentimispäring (%s, %s, %s, %s)' % \
                    (rsp._UserIDCode, rsp._UserGivenname, \
                    rsp._UserSurname, rsp._Challenge))

                evlog.log(alog)
                if elog:
                    evlog.log_error(elog)

                return protocol.msg_mobid_auth_init_ok(\
                    self.ctx().sessid(), rsp._ChallengeID)

            return self.__return_mid_error(rsp._Status)

        except httplib.BadStatusLine, exc:
            return self.__return_badstatusline_error(exc)
        except ZSI.FaultException, exc:
            return self.__return_zsi_error(exc)
        except:
            return self.__return_exception()
        finally:
            evlog.log('Autentimispäring: LÕPP')

    def __export_certificate(self):
        cert = '-----BEGIN CERTIFICATE-----\n' + \
            self.ctx().certificate() + '\n-----END CERTIFICATE-----\n'
        os.environ[evcommon.HTTP_CERT] = cert

    def __get_candidate_list(self):
        self.__export_certificate()
        hesd = hesdisp.HESVoterDispatcher()
        self.ctx().set_auth_succ()
        return hesd.get_candidate_list()

    def __get_with_votefiles(self, vote):
        import zipfile

        bdocdata = StringIO.StringIO(base64.b64decode(vote))
        bdoczip = zipfile.ZipFile(bdocdata, "a")
        votefiles = self.ctx().get_votefiles()
        for filename in votefiles:
            bdoczip.writestr(filename, votefiles[filename])
        bdoczip.close()
        return base64.b64encode(bdocdata.getvalue())

    def __hts_vote(self, vote):
        vote = self.__get_with_votefiles(vote)
        self.__export_certificate()
        hesd = hesdisp.HESVoterDispatcher()
        hv = self.ctx().get_origvote()
        self.ctx().kill()
        return hesd.hts_vote(vote, hv)

    def __poll_auth(self):
        service = MobileIDService()
        rsp = service.poll_auth(self.ctx())

        if rsp._Status == 'OUTSTANDING_TRANSACTION':
            return protocol.msg_mobid_poll()

        if rsp._Status == 'USER_AUTHENTICATED':
            evlog.log('Received USER_AUTHENTICATED from DDS')
            c1, c2 = self.ctx().verify_challenge(rsp._Signature)
            if not c1:
                evlog.log_error(c2)
                return self.__return_mid_error('Autentimine ebaõnnestus')

            return self.__get_candidate_list()

        return self.__return_mid_error(rsp._Status)

    def __poll_sign(self):
        service = MobileIDService()
        r1, r2 = service.poll_sign(self.ctx())

        if r1 == 'OUTSTANDING_TRANSACTION':
            return protocol.msg_mobid_poll()

        if r1 == 'SIGNATURE':
            evlog.log('Received SIGNATURE from DDS')
            return self.__hts_vote(r2)

        return self.__return_mid_error(r1)


    def poll(self):

        try:
            evlog.log('Poll: ALGUS')
            self.ctx().load_pre_poll()

            if self.ctx().auth_succ():
                return self.__poll_sign()
            return self.__poll_auth()

        except httplib.BadStatusLine, exc:
            return self.__return_badstatusline_error(exc)
        except ZSI.FaultException, exc:
            return self.__return_zsi_error(exc)
        except:
            return self.__return_exception()
        finally:
            evlog.log('Poll: LÕPP')


if __name__ == "__main__":
    pass

# vim:set ts=4 sw=4 et fileencoding=utf8:
