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

import bdocpython
import bdocpythonutils
from election import Election
import base64
import hts
import htsrevoke
import evstrings
import evcommon
from evmessage import EvMessage
import evlog
import htsstatus
import htscommon
import formatutil
import question
import ksum
import time
import random
import os

def _generate_vote_id():
    return os.urandom(20).encode('hex')

def _delete_vote_id(vote_id):
    return Election().get_root_reg().ensure_no_key(\
            htscommon.get_verification_key(vote_id))

def _revoke_vote_id(voter_code):
    elec = Election()
    otps = set()
    for quest in elec.get_questions():
        reg = elec.get_sub_reg(quest)
        key = htscommon.get_user_key(voter_code)
        if reg.check(key + [htscommon.VOTE_VERIFICATION_ID_FILENAME]):
            otp = reg.read_string_value(key, \
                    htscommon.VOTE_VERIFICATION_ID_FILENAME)
            otps.add(otp.value)
            evlog.log("Revoking vote ID %s" % otp)
            if not _delete_vote_id(otp.value):
                evlog.log_error("No such vote-ID: %s" % otp)
            otp.delete()

    if len(otps) > 1:
        evlog.log_error("The voter %s had multiple vote ID-s: %s" % \
                (voter_code, ", ".join(otps)))

class HTSStoreException(Exception):
    def __init__(self, ret):
        self.ret = ret

class HTSStore:

    def __init__(self):
        self.user_msg = ''
        self.log_msg = ''
        self.signercode = None
        self.ocsp_time = None
        self.signed_vote = None
        self.bdoc = None
        self.questions = []
        self.actions = []

    def __check_incoming_vote(self, config):

        _doc_count = len(self.bdoc.documents)
        if _doc_count == 0:
            raise Exception, "BDoc ei sisalda ühtegi andmefaili"

        sigfiles = self.bdoc.signatures.keys()
        if len(sigfiles) != 1:
            raise Exception, "BDoc sisaldab rohkem kui ühte allkirja"

        verifier = bdocpython.BDocVerifier()
        config.populate(verifier)
        for el in self.bdoc.documents:
            verifier.setDocument(self.bdoc.documents[el], el)

        sig_fn = sigfiles[0]
        sig_content = self.bdoc.signatures[sig_fn]
        if self.bdoc.prof == 'BES':
            res = verifier.verifyBESOnline(sig_content)
            if res.result:
                self.bdoc.addTM(sig_fn, res.signature)
            return res

        return verifier.verifyTMOffline(sig_content)


    def verify_vote(self, votedata):
        import regrights
        self.user_msg = \
            EvMessage().get_str("TEHNILINE_VIGA_HAALE_VERIFITSEERIMISEL", \
            evstrings.TEHNILINE_VIGA_HAALE_VERIFITSEERIMISEL)

        conf = bdocpythonutils.BDocConfig()
        conf.load(Election().get_bdoc_conf())

        self.bdoc = bdocpythonutils.BDocContainer()
        self.bdoc.load_bytes(votedata)
        self.bdoc.validateflex()
        res = self.__check_incoming_vote(conf)

        if not res.result:
            self.log_msg = res.error
            if self.user_msg == '':
                self.user_msg = EvMessage().\
                    get_str("TEHNILINE_VIGA_HAALE_VERIFITSEERIMISEL", \
                        evstrings.TEHNILINE_VIGA_HAALE_VERIFITSEERIMISEL)

            if not res.ocsp_is_good:
                self.user_msg = EvMessage().\
                    get_str("SERTIFIKAAT_ON_TYHISTATUD_VOI_PEATATUD", \
                        evstrings.SERTIFIKAAT_ON_TYHISTATUD_VOI_PEATATUD)
                raise HTSStoreException, evcommon.EVOTE_CERT_ERROR

            raise HTSStoreException, evcommon.EVOTE_ERROR

        self.signercode = regrights.get_personal_code(res.subject)

        self.ocsp_time = res.ocsp_time
        self.signed_vote = self.bdoc.get_bytes()

    def extract_questions(self):

        self.log_msg = \
            "Allkirjastatud hääl '%s' ei vasta formaadinõuetele" % \
            self.signercode
        self.user_msg = EvMessage().get_str(\
            "TEHNILINE_VIGA_HAALE_TALLETAMISEL", \
            evstrings.TEHNILINE_VIGA_HAALE_TALLETAMISEL)

        for dfn in self.bdoc.documents:
            quest = dfn.split('.')
            if len(quest) != 2:
                raise HTSStoreException, evcommon.EVOTE_ERROR

            if quest[1] != 'evote':
                raise HTSStoreException, evcommon.EVOTE_ERROR

            if not quest[0] in Election().get_questions():
                raise HTSStoreException, evcommon.EVOTE_ERROR

            vote = self.bdoc.documents[dfn]

            self.questions.append([quest[0], vote])

    def _count_votes(self, elid):
        user_key = htscommon.get_user_key(self.signercode)
        if Election().get_sub_reg(elid).check(user_key):
            keys = Election().get_sub_reg(elid).list_keys(user_key)
            try:
                keys.remove(htscommon.VOTE_VERIFICATION_ID_FILENAME)
            except ValueError:
                pass # No "otp" file
            return len(keys)
        return 0

    def create_actions(self):
        max_votes_per_voter = None
        if Election().get_root_reg().check(['common', 'max_votes_per_voter']):
            max_votes_per_voter = \
                Election().get_root_reg().read_integer_value(\
                    ['common'], 'max_votes_per_voter').value

        for el in self.questions:
            _hts = hts.HTS(el[0])
            voter = _hts.talletaja(self.signercode)
            dsc = ''
            try:
                dsc = Election().get_sub_reg(\
                    el[0]).read_string_value(['common'], 'description').value
            except:
                dsc = el[0]
            if voter == None:
                self.user_msg = EvMessage().get_str("POLE_LUBATUD_HAALETADA", \
                    evstrings.POLE_LUBATUD_HAALETADA) % (self.signercode, dsc)
                self.log_msg = self.user_msg
                raise HTSStoreException, evcommon.EVOTE_ERROR
            if max_votes_per_voter:
                if self._count_votes(el[0]) >= max_votes_per_voter:
                    self.user_msg = EvMessage().get_str(\
            "TEHNILINE_VIGA_MAX_HAALTE_ARV_PER_HAALETAJA_ON_ULETATUD", \
            evstrings.TEHNILINE_VIGA_MAX_HAALTE_ARV_PER_HAALETAJA_ON_ULETATUD)

                    self.log_msg = self.user_msg
                    raise HTSStoreException, evcommon.EVOTE_ERROR

            self.actions.append([_hts, voter, el[1]])

    def revoke_vote_id(self):
        _revoke_vote_id(self.signercode)

    def __create_vote_key(self):
        reg = Election().get_root_reg()
        while True:
            vote_id = _generate_vote_id()
            key = htscommon.get_verification_key(vote_id)
            if not reg.check(key):
                reg.create_key(key)
                return vote_id

    def issue_vote_id(self):
        vote_id = self.__create_vote_key()
        rreg = Election().get_root_reg()
        key = htscommon.get_verification_key(vote_id)

        rreg.create_string_value(key, "voter", self.signercode)
        rreg.create_integer_value(key, "timestamp", int(time.time()))
        rreg.create_integer_value(key, "count", \
                Election().get_verification_count())

        # Store the election IDs and include a backreference in the
        # corresponding questions' subregistries.
        elids = ""
        for elid in [quest[0] for quest in self.questions]:
            elids += elid + "\t"

            sreg = Election().get_sub_reg(elid)
            skey = htscommon.get_user_key(self.signercode)
            sreg.ensure_key(skey)
            sreg.create_string_value(skey, \
                    htscommon.VOTE_VERIFICATION_ID_FILENAME, vote_id)

        rreg.create_string_value(key, "elids", elids)
        return vote_id

    def store_votes(self):

        for el in self.actions:
            el[0].talleta_haal(
                signercode=self.signercode,
                signedvote=self.signed_vote,
                vote=el[2],
                timestamp=self.ocsp_time,
                valija=el[1])

            if not el[0].haaletanud(self.signercode):
                self.user_msg = EvMessage().get_str(\
                    "TEHNILINE_VIGA_HAALE_TALLETAMISEL", \
                    evstrings.TEHNILINE_VIGA_HAALE_TALLETAMISEL)
                self.log_msg = \
                    'Hääle talletamisjärgne kontroll andis '\
                    'vigase tulemuse (%s)' % self.signercode
                raise HTSStoreException, evcommon.EVOTE_ERROR


class HTSVerifyException(Exception):
    def __init__(self, ret):
        self.ret = ret

class HTSVerify:

    def __init__(self):
        self._rreg = Election().get_root_reg()
        self._vote_id = None
        self._voter_code = None
        self._voter = None

    def __revoke_vote_id(self):
        _revoke_vote_id(self._voter_code)

    def verify_id(self, vote_id):
        # check if valid vote ID
        if not formatutil.is_vote_verification_id(vote_id):
            # We don't know how large vote_id is, so don't write to disk
            evlog.log_error("Malformed vote ID")
            raise HTSVerifyException, evcommon.VERIFY_ERROR

        vote_id = vote_id.lower()
        otp_key = htscommon.get_verification_key(vote_id)

        # check if corresponding OTP exists
        if not self._rreg.check(otp_key):
            evlog.log_error("No such vote ID: %s" % vote_id)
            raise HTSVerifyException, evcommon.VERIFY_ERROR

        self._voter_code = self._rreg.read_string_value(\
                otp_key, "voter").value.rstrip()

        # check if timestamp is OK
        current = int(time.time())
        created = self._rreg.read_integer_value(otp_key, "timestamp").value
        timeout = Election().get_verification_time() * 60
        if created + timeout < current:
            evlog.log("Vote ID %s has expired" % vote_id)
            self.__revoke_vote_id()
            raise HTSVerifyException, evcommon.VERIFY_ERROR

        # check if count is OK
        count = self._rreg.read_integer_value(otp_key, "count").value
        if count <= 0:
            evlog.log_error("Vote ID %s count is zero, but had not been revoked")
            self.__revoke_vote_id()
            raise HTSVerifyException, evcommon.VERIFY_ERROR

        self._vote_id = vote_id

    def __load_bdoc(self, elid):
        voter_key = htscommon.get_user_key(self._voter_code)
        sreg = Election().get_sub_reg(elid)
        for votefile in sreg.list_keys(voter_key):
            if htscommon.VALID_VOTE_PATTERN.match(votefile):
                bdoc = bdocpythonutils.BDocContainer()
                bdoc.load(sreg.path(voter_key + [votefile]))
                bdoc.validate(bdocpythonutils.ManifestProfile("TM"))

                self._voter = htscommon.get_votefile_voter(votefile)
                break

        if not bdoc:
            evlog.log_error("No valid BDOC found for voter %s using vote ID %s" % \
                    (self._voter, self._vote_id))
            raise HTSVerifyException, evcommon.VERIFY_ERROR

        return bdoc

    def __decrease_count(self):
        otp_key = htscommon.get_verification_key(self._vote_id)
        count = self._rreg.read_integer_value(otp_key, "count").value - 1
        if count > 0:
            self._rreg.create_integer_value(otp_key, "count", count)
        else:
            self.__revoke_vote_id()

    def get_response(self):
        import binascii

        # load a random BDOC from the ones available
        otp_key = htscommon.get_verification_key(self._vote_id)
        elids = self._rreg.read_string_value(otp_key, "elids")\
                .value.rstrip().split("\t")
        bdoc = self.__load_bdoc(random.choice(elids))
        evlog.log("Sending BDOC %s with vote ID %s for verification" %\
                (ksum.votehash(bdoc.get_bytes()), self._vote_id))

        # check consistency
        bdoc_set = set([doc.split(".")[0] for doc in bdoc.documents])
        elids_set = set(elids)
        if bdoc_set != elids_set:
            evlog.log_error("Votes in BDOC for vote ID %s are inconsistent " \
                    "with registry: %s, %s" % (self._vote_id, bdoc_set, elids_set))
            raise HTSVerifyException, evcommon.VERIFY_ERROR

        # create question objects
        questions = []
        for elid in elids:
            questions.append(question.Question(\
                    elid, "hts", Election().get_sub_reg(elid)))

        # start assembling the response
        ret = ""

        # append questions
        for quest in questions:
            ret += quest.qname() + ":" + str(quest.get_type()) + "\t"
        ret += "\n"

        # append election IDs and votes
        for votefile in bdoc.documents:
            elid = votefile.split(".")[0]
            ret += elid + "\t" + binascii.b2a_hex(bdoc.documents[votefile]) + "\n"
        ret += "\n"

        # append choices list
        for quest in questions:
            tv = quest.get_voter(self._voter_code)
            if tv:
                ret += quest.choices_to_voter(tv)
            else:
                evlog.log_error("Voter not found")

        self.__decrease_count()
        return ret

class HTSAll:

    def __init__(self):
        bdocpython.initialize()

    def __del__(self):
        bdocpython.terminate()

    def status(self, fo, verify):
        fo.write('HTS vaheauditi aruanne\n\n')
        if (not verify):
            fo.write('NB! Hääli ei verifitseeritud\n\n')
        fo.write('Käimasolevad hääletused:\n')
        for el in Election().get_questions():
            fo.write('\t%s\n' % el)

        fo.write('\nAnalüüs hääletuste kaupa:\n\n')
        for el in Election().get_questions():
            _h = htsstatus.HTSStatus(el)
            _h.calculate(verify)
            _h.output(fo)
            fo.write('\n')

    def kooskolaline(self, voters_files_sha1):
        if Election().get_root_reg().check(['common', 'voters_files_sha1']):
            hts_voters_files_sha1 = \
                Election().get_root_reg().read_string_value(
                    ['common'], 'voters_files_sha1').value
        else:
            hts_voters_files_sha1 = ''
        if hts_voters_files_sha1 != voters_files_sha1:
            return False
        return True

    def haaletanud(self, ik):
        votes = []
        lst = Election().get_questions()
        for el in lst:
            _h = htsrevoke.HTSRevoke(el)
            if _h.haaletanud(ik):
                votes.append(\
                    Election().get_sub_reg(el).\
                        read_string_value(['common'], 'electionid').value)

        if len(votes) > 0:
            ret = ''
            for el in votes:
                ret += el
                ret += '\n'
            return True, ret.rstrip()

        return False, \
            'Isikukoodi %s kohta ei ole talletatud ühtegi häält' % ik

    def __haaletanud(self, ik):
        lst = Election().get_questions()
        for el in lst:
            _h = htsrevoke.HTSRevoke(el)
            if _h.haaletanud(ik):
                return True
        return False

    def __questions_with_valid_vote(self, ik):
        questions = []
        lst = Election().get_questions()
        for el in lst:
            _h = htsrevoke.HTSRevoke(el)
            if _h.haaletanud(ik):
                questions.append(el)
        return questions

    def __talleta(self, binvote):

        store = HTSStore()
        new_otp = False
        try:
            store.verify_vote(binvote)
            evlog.log('Hääle allkirjastaja: %s' % store.signercode)
            store.extract_questions()
            store.create_actions()
            store.revoke_vote_id()
            vote_id = store.issue_vote_id()
            new_otp = True
            store.store_votes()
        except HTSStoreException as e:
            evlog.log_error(store.log_msg)
            if new_otp:
                store.revoke_vote_id()
            return e.ret, store.user_msg

        evlog.log("Issued vote ID %s to %s for BDOC %s" % \
                (vote_id, store.signercode, ksum.votehash(store.signed_vote)))
        return evcommon.EVOTE_OK, vote_id

    def talleta_base64(self, data):

        try:
            decoded_vote = base64.decodestring(data)
            return self.__talleta(decoded_vote)
        except:
            evlog.log_exception()
            return evcommon.EVOTE_ERROR, \
                    EvMessage().get_str(\
                    "TEHNILINE_VIGA_HAALE_TALLETAMISEL",\
                    evstrings.TEHNILINE_VIGA_HAALE_TALLETAMISEL)

    def verify(self, vote_id):
        verifier = HTSVerify()
        try:
            verifier.verify_id(vote_id)
        except HTSVerifyException as e:
            return e.ret, EvMessage().get_str(\
                    "INVALID_VOTE_ID", evstrings.INVALID_VOTE_ID)

        evlog.log("Verifying vote with ID %s" % vote_id)
        try:
            return evcommon.VERIFY_OK, verifier.get_response()
        except HTSVerifyException as e:
            return e.ret, EvMessage().get_str(\
                    "TECHNICAL_ERROR_VOTE_VERIFICATION", \
                    evstrings.TECHNICAL_ERROR_VOTE_VERIFICATION)


if __name__ == '__main__':

    print 'No main'

# vim:set ts=4 sw=4 et fileencoding=utf8:
