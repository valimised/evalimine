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

import evcommon
import formatutil
import election
import exception_msg

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
    evcommon.POST_VOTERS_FILES_SHA1: formatutil.is_voters_file_sha1,
    evcommon.POST_SESS_ID: formatutil.is_session_id,
    evcommon.POST_PHONENO: formatutil.is_mobid_phoneno,
    evcommon.POST_MID_POLL: formatutil.is_mobid_poll
}

def is_bdoc_mimetype_file(zi):
    fn = (zi.filename == 'mimetype')
    fs = (zi.file_size == 24)
    cs = (zi.compress_size == 24)
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
    fn = (zi.filename == 'META-INF/signature0.xml')
    fs = (zi.file_size < 5120)
    cs = (zi.compress_size < 5120)
    return (fn and fs and cs)


ZIPFILE_VALIDATORS = {
    'mimetype' : is_bdoc_mimetype_file,
    'META-INF/' : is_bdoc_metainf_dir,
    'META-INF/manifest.xml' : is_bdoc_manifest_file,
    'META-INF/signature0.xml' : is_bdoc_signature_file
}


def get_invalid_keys(form, required):
    invalid = []

    for key in required:
        if not form.has_key(key):
            invalid.append((key, REASON_MISSING))

    for key in form:

        values = form.getlist(key)
        extra = "%d, %s" % (len(values), values[:200])

        if not key in required:
            invalid.append((key, REASON_UNKNOWN, extra))
            continue

        if not VALIDATORS.has_key(key):
            invalid.append((key, REASON_NO_VALIDATOR, extra))
            continue

        if len(values) > 1:
            invalid.append((key, REASON_NOT_SINGLE_VALUE, extra))
            continue

        if not VALIDATORS[key](values[0]):
            invalid.append((key, REASON_NOT_VALID, extra))
            continue

    return invalid


HDR_1 = \
"""<Signature Id="S0" xmlns="http://www.w3.org/2000/09/xmldsig#">
<SignedInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
<CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315">
</CanonicalizationMethod>
<SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha224">
</SignatureMethod>
"""

HDR_2 = \
"""</X509Data></KeyInfo>
<Object><QualifyingProperties xmlns="http://uri.etsi.org/01903/v1.3.2#" Target="#S0">
<SignedProperties xmlns="http://uri.etsi.org/01903/v1.3.2#" Id="S0-SignedProperties">
<SignedSignatureProperties>
"""

HDR_3 = \
"""<SigningCertificate>
<Cert>
<CertDigest>
<DigestMethod xmlns="http://www.w3.org/2000/09/xmldsig#" Algorithm="http://www.w3.org/2001/04/xmldsig-more#sha224">
</DigestMethod>
"""

HDR_4 = \
"""</IssuerSerial></Cert></SigningCertificate></SignedSignatureProperties>
<SignedDataObjectProperties>
</SignedDataObjectProperties>
</SignedProperties><UnsignedProperties xmlns="http://uri.etsi.org/01903/v1.3.2#">
</UnsignedProperties></QualifyingProperties></Object>
</Signature>
"""

HDR_5 = \
"""
<DigestMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#sha224">
</DigestMethod>
"""


def check_prefix(inp, prefix):
    if inp.startswith(prefix):
        return len(prefix)
    return -1


def check_tag(inp, tag_start, tag_end, is_good):
    if not inp.startswith(tag_start):
        return -1

    end = inp.find(tag_end)
    if end == -1:
        return -1

    start = len(tag_start)
    if is_good(inp[start:end]):
        return end + len(tag_end)

    return -1


def check_references(inp, questions):
    start = 0
    ref_count = 0
    common_start = "<Reference"
    tag_end = "</Reference>\n"
    taglist = []
    taglist.append(\
            "<Reference Type=\"http://uri.etsi.org/01903#SignedProperties\" URI=\"#S0-SignedProperties\">")
    for el in questions:
        taglist.append("<Reference URI=\"/%s.evote\">" % el)

    while inp[start:].startswith(common_start):
        for tag_start in taglist:
            ret = check_prefix(inp[start:], tag_start)
            if ret > -1:
                taglist.remove(tag_start)
                break
        if ret == -1:
            return -1
        start = start + ret

        ret = check_prefix(inp[start:], HDR_5)
        if ret == -1:
            return -1
        start = start + ret

        ret = check_tag(inp[start:], "<DigestValue>", \
                "</DigestValue>\n</Reference>\n", formatutil.is_base64)
        if ret == -1:
            return -1
        start = start + ret

        ref_count = ref_count + 1

    if ref_count < 2:
        return -1

    return start


def is_well_formed_id_signature(sigdata, questions):

    tag_s_sigval = "</SignedInfo><SignatureValue Id=\"S0-SIG\">"
    tag_e_sigval = "</SignatureValue>\n"
    tag_s_mod = "<KeyInfo>\n<KeyValue>\n<RSAKeyValue>\n<Modulus>"
    tag_e_mod = "</Modulus>\n"
    tag_s_expo = "<Exponent>"
    tag_e_expo = "</Exponent>\n"
    tag_s_x509 = "</RSAKeyValue>\n</KeyValue>\n<X509Data><X509Certificate>"
    tag_e_x509 = "</X509Certificate>"
    tag_s_stime = "<SigningTime>"
    tag_e_stime = "</SigningTime>\n"
    tag_s_digval = "<DigestValue xmlns=\"http://www.w3.org/2000/09/xmldsig#\">"
    tag_e_digval = "</DigestValue>\n"
    tag_s_issuer = "</CertDigest>\n<IssuerSerial>\n" + \
        "<X509IssuerName xmlns=\"http://www.w3.org/2000/09/xmldsig#\">"
    tag_e_issuer = "</X509IssuerName>\n"
    tag_s_serial = \
            "<X509SerialNumber xmlns=\"http://www.w3.org/2000/09/xmldsig#\">"
    tag_e_serial = "</X509SerialNumber>\n"

    item1 = {
            'validator' : check_prefix,
            'arguments' : {
                'prefix' : HDR_1
                }
            }
    item2 = {
            'validator' : check_references,
            'arguments' : {
                'questions' : questions
                }
            }
    item3 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_sigval,
                'tag_end' : tag_e_sigval,
                'is_good' : formatutil.is_base64_lines
                }
            }
    item4 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_mod,
                'tag_end' : tag_e_mod,
                'is_good' : formatutil.is_base64_lines
                }
            }
    item5 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_expo,
                'tag_end' : tag_e_expo,
                'is_good' : formatutil.is_base64
                }
            }
    item6 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_x509,
                'tag_end' : tag_e_x509,
                'is_good' : formatutil.is_base64_lines
                }
            }
    item7 = {
            'validator' : check_prefix,
            'arguments' : {
                'prefix' : HDR_2
                }
            }
    item8 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_stime,
                'tag_end' : tag_e_stime,
                'is_good' : formatutil.is_signing_time
                }
            }
    item9 = {
            'validator' : check_prefix,
            'arguments' : {
                'prefix' : HDR_3
                }
            }
    item10 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_digval,
                'tag_end' : tag_e_digval,
                'is_good' : formatutil.is_base64
                }
            }
    item11 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_issuer,
                'tag_end' : tag_e_issuer,
                'is_good' : formatutil.is_100utf8
                }
            }
    item12 = {
            'validator' : check_tag,
            'arguments' : {
                'tag_start' : tag_s_serial,
                'tag_end' : tag_e_serial,
                'is_good' : formatutil.is_number100
                }
            }
    item13 = {
            'validator' : check_prefix,
            'arguments' : {
                'prefix' : HDR_4
                }
            }

    stream = []
    stream.append(item1)
    stream.append(item2)
    stream.append(item3)
    stream.append(item4)
    stream.append(item5)
    stream.append(item6)
    stream.append(item7)
    stream.append(item8)
    stream.append(item9)
    stream.append(item10)
    stream.append(item11)
    stream.append(item12)
    stream.append(item13)

    start = 0
    for item in stream:
        validator = item['validator']
        ret = validator(sigdata[start:], **item['arguments'])
        if ret == -1:
            return False, sigdata[start:start+200]
        start = start + ret

    if start == len(sigdata):
        return True, ''

    return False, sigdata[start:start+200]


def is_well_formed_signature(sigfile, questions):

    hdr1 = sigfile.readline()
    if hdr1 == "<Signature/>":
        hdr2 = sigfile.readline()
        if hdr2 == "":
            return True, ''

    if hdr1 == "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n":
        return is_well_formed_id_signature(sigfile.read(), questions)

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

    has_enc_vote = False
    for el in ziplist:
        if ZIPFILE_VALIDATORS.has_key(el.filename):
            if not ZIPFILE_VALIDATORS[el.filename](el):
                return False, (el.filename, REASON_NOT_VALID)

            data = zipf.open(el.filename).read(el.file_size + 1)
            if len(data) > el.file_size:
                return False, (el.filename, REASON_ZIPBOMB)

            continue

        if question_validators.has_key(el.filename):
            if not question_validators[el.filename](el):
                return False, (el.filename, REASON_NOT_VALID)
            has_enc_vote = True
            continue

        return False, (el.filename, REASON_UNKNOWN)

    if not has_enc_vote:
        return False, ('vote', REASON_NO_BALLOT)

    if zipf.testzip() != None:
        return False, ('vote', REASON_NOT_ZIP)

    res, extra = is_well_formed_signature(\
            zipf.open('META-INF/signature0.xml'), questions)

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
            logline = 'Invalid vote: key - %s, reason - %s' % \
                    (why[0], REASONS[why[1]])
        elif len(why) == 3:
            logline = 'Invalid vote: key - %s, reason - %s, extra - %s' % \
                    (why[0], REASONS[why[1]], why[2][:200])
        else:
            logline = 'Invalid vote: internal error'

        return False, logline
    except:
        logline = 'Invalid vote: key - exception, reason - %s' % \
                exception_msg.trace()
        return False, logline


def validate_form(form, required):
    try:
        logline = ''
        invalid = get_invalid_keys(form, required)
        if len(invalid) <> 0:
            logline = 'Invalid form: '
            for el in invalid:
                if len(el) == 2:
                    logline = "%skey - %s, reason - %s;" % \
                            (logline, el[0], REASONS[el[1]])
                elif len(el) == 3:
                    logline = "%skey - %s, reason - %s, extra - %s" % \
                            (logline, el[0], REASONS[el[1]], el[2][:200])
                else:
                    logline = "%sinternal error" % logline
            return False, logline

        if evcommon.POST_EVOTE in required:
            return validate_vote(\
                    form.getvalue(evcommon.POST_EVOTE), \
                    election.Election().get_questions())

        return True, logline
    except:
        logline = 'Invalid form: key - exception, reason - %s' % \
                exception_msg.trace()
        return False, logline


def validate_sessionid(form):

    key = evcommon.POST_SESS_ID

    if not form.has_key(key):
        return False

    if not VALIDATORS.has_key(key):
        return False

    values = form.getlist(key)
    if len(values) > 1:
        return False

    if not VALIDATORS[key](values[0]):
        return False

    return True

