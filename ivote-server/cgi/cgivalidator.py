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

import evcommon
import formatutil
import election
import exception_msg
import sigvalidator

REASON_MISSING = 0
REASON_UNKNOWN = 1
REASON_NO_VALIDATOR = 2
REASON_NOT_SINGLE_VALUE = 3
REASON_NOT_VALID = 4
REASON_NOT_ZIP = 5
REASON_MISSING_ELEMENTS = 6
REASON_TOO_MANY_ELEMENTS = 7
REASON_NO_BALLOT = 8
REASON_ZIPBOMB = 9
REASON_BAD_SIGNATURE = 10

REASONS = {
    REASON_MISSING : "missing",
    REASON_UNKNOWN : "unknown",
    REASON_NO_VALIDATOR : "validator missing",
    REASON_NOT_SINGLE_VALUE : "multiple values",
    REASON_NOT_VALID : "invalid",
    REASON_NOT_ZIP : "badzip",
    REASON_MISSING_ELEMENTS : "missing elements",
    REASON_TOO_MANY_ELEMENTS : "too many elements",
    REASON_NO_BALLOT : "no ballot",
    REASON_ZIPBOMB : "zipbomb",
    REASON_BAD_SIGNATURE : "bad signature",
}

VALIDATORS = {
    evcommon.POST_EVOTE : formatutil.is_vote,
    evcommon.POST_PERSONAL_CODE: formatutil.is_isikukood,
    evcommon.POST_VOTERS_FILES_SHA256: formatutil.is_voters_file_sha256,
    evcommon.POST_SESS_ID: formatutil.is_session_id,
    evcommon.POST_PHONENO: formatutil.is_mobid_phoneno,
    evcommon.POST_MID_POLL: formatutil.is_mobid_poll,
    evcommon.POST_VERIFY_VOTE: formatutil.is_vote_verification_id
}


def is_bdoc_mimetype_file(zi):
    size = len("application/vnd.etsi.asic-e+zip")
    fn = (zi.filename == 'mimetype')
    fs = (zi.file_size == size)
    cs = (zi.compress_size == size)
    return (fn and fs and cs)


def is_bdoc_metainf_dir(zi):
    fn = (zi.filename == 'META-INF/')
    fs = (zi.file_size == 0)
    cs = (zi.compress_size == 0)
    return (fn and fs and cs)


def is_bdoc_manifest_file(zi):
    fn = (zi.filename == 'META-INF/manifest.xml')
    fs = (zi.file_size < 1024)
    cs = (zi.compress_size < 1024)
    return (fn and fs and cs)


def is_encrypted_vote(zi):
    fs = (zi.file_size == 256)
    cs = (zi.compress_size == 256)
    return (fs and cs)


def is_bdoc_signature_file(zi):
    fn = (zi.filename == 'META-INF/signatures0.xml')
    fs = (zi.file_size < 12000)
    cs = (zi.compress_size < 12000)
    return (fn and fs and cs)


ZIPFILE_VALIDATORS = {
    'mimetype' : is_bdoc_mimetype_file,
    'META-INF/' : is_bdoc_metainf_dir,
    'META-INF/manifest.xml' : is_bdoc_manifest_file,
    'META-INF/signatures0.xml' : is_bdoc_signature_file
}


def get_invalid_keys(form, required):
    invalid = []

    for key in required:
        if key not in form:
            invalid.append((key, REASON_MISSING))

    for key in form:

        values = form.getlist(key)
        extra = "%d, %s" % (len(values), values[0][:200])

        if key not in required:
            invalid.append((key, REASON_UNKNOWN, extra))
            continue

        if key not in VALIDATORS:
            invalid.append((key, REASON_NO_VALIDATOR, extra))
            continue

        if len(values) > 1:
            extra += ", %s" % values[1][:200]
            invalid.append((key, REASON_NOT_SINGLE_VALUE, extra))
            continue

        if not VALIDATORS[key](values[0]):
            invalid.append((key, REASON_NOT_VALID, extra))
            continue

    return invalid


def is_well_formed_signature(sigfile, questions):

    hdr1 = sigfile.readline()
    if hdr1 == "<Signature/>":
        hdr2 = sigfile.readline()
        if hdr2 == "":
            return True, ''

    if hdr1 == "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n":
        return sigvalidator.is_well_formed_id_signature(sigfile.read(), questions)

    return False, hdr1


def is_well_formed_vote_file(votefile, questions):

    import zipfile

    zipf = zipfile.ZipFile(votefile, "r")
    ziplist = zipf.infolist()

    if (len(ziplist) <= len(ZIPFILE_VALIDATORS)):
        return False, ('vote', REASON_MISSING_ELEMENTS)

    question_validators = {}
    for el in questions:
        question_validators["%s.evote" % el] = is_encrypted_vote

    if (len(ziplist) > ((len(ZIPFILE_VALIDATORS) + len(question_validators)))):
        return False, ('vote', REASON_TOO_MANY_ELEMENTS)

    real_questions = []
    for el in ziplist:
        if el.filename in ZIPFILE_VALIDATORS:
            if not ZIPFILE_VALIDATORS[el.filename](el):
                return False, (el.filename, REASON_NOT_VALID)

            data = zipf.open(el.filename).read(el.file_size + 1)
            if len(data) > el.file_size:
                return False, (el.filename, REASON_ZIPBOMB)

            continue

        if el.filename in question_validators:
            if not question_validators[el.filename](el):
                return False, (el.filename, REASON_NOT_VALID)
            real_questions.append(el.filename.split('.')[0])
            continue

        return False, (el.filename, REASON_UNKNOWN)

    if len(real_questions) == 0:
        return False, ('vote', REASON_NO_BALLOT)

    if zipf.testzip() is not None:
        return False, ('vote', REASON_NOT_ZIP)

    res, extra = is_well_formed_signature(
        zipf.open('META-INF/signatures0.xml'), real_questions)

    if not res:
        return False, ('vote', REASON_BAD_SIGNATURE, extra)

    return True, ()


def is_well_formed_vote(b64, questions):

    if not formatutil.is_vote(b64):
        return False, ('vote', REASON_NOT_VALID)

    import StringIO
    import base64

    votedata = base64.b64decode(b64)
    votefile = StringIO.StringIO(votedata)
    return is_well_formed_vote_file(votefile, questions)


def validate_vote(vote, questions):
    try:
        logline = ''
        res, why = is_well_formed_vote(vote, questions)
        if res:
            return True, logline

        if len(why) == 2:
            logline = ('Invalid vote: key - %s, reason - %s' %
                       (why[0], REASONS[why[1]]))
        elif len(why) == 3:
            logline = ('Invalid vote: key - %s, reason - %s, extra - %s' %
                       (why[0], REASONS[why[1]], why[2][:200]))
        else:
            logline = 'Invalid vote: internal error'

        return False, logline
    except:
        logline = ('Invalid vote: key - exception, reason - %s' %
                   exception_msg.trace())
        return False, logline


def validate_form(form, required):
    try:
        logline = ''
        invalid = get_invalid_keys(form, required)
        if len(invalid) != 0:
            logline = 'Invalid form: '
            for el in invalid:
                if len(el) == 2:
                    logline = ("%skey - %s, reason - %s;" %
                               (logline, el[0], REASONS[el[1]]))
                elif len(el) == 3:
                    logline = ("%skey - %s, reason - %s, extra - %s" %
                               (logline, el[0], REASONS[el[1]], el[2][:200]))
                else:
                    logline = "%sinternal error" % logline
            return False, logline

        if evcommon.POST_EVOTE in required:
            return validate_vote(form.getvalue(evcommon.POST_EVOTE),
                                 election.Election().get_questions())

        return True, logline
    except:
        logline = ('Invalid form: key - exception, reason - %s' %
                   exception_msg.trace())
        return False, logline


def validate_sessionid(form):

    key = evcommon.POST_SESS_ID

    if key not in form:
        return False

    if key not in VALIDATORS:
        return False

    values = form.getlist(key)
    if len(values) > 1:
        return False

    if not VALIDATORS[key](values[0]):
        return False

    return True


if __name__ == '__main__':
    pass
#    print is_well_formed_vote_file(open('debug_vote.bdoc'),
#                                   ['RH2018', 'EP2018'])
