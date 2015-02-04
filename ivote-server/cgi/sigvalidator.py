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

import formatutil

TAG_XADES_SIGNATURES = \
"""<asic:XAdESSignatures xmlns:asic="http://uri.etsi.org/02918/v1.2.1#" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#">
<ds:Signature Id="S0">
<ds:SignedInfo """

TAG_NAMESPACE = \
"""xmlns:asic="http://uri.etsi.org/02918/v1.2.1#" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" """

TAG_CANONICALIZATION_METHOD = \
"""Id="S0-SignedInfo">
<ds:CanonicalizationMethod Algorithm="http://www.w3.org/2006/12/xml-c14n11">
</ds:CanonicalizationMethod>
"""

TAG_OBJECT = \
'<ds:Object Id="S0-object-xades"><xades:QualifyingProperties Id="S0-QualifyingProperties" Target="#S0"'

TAG_OBJECT_NAMESPACE = \
' xmlns:xades="http://uri.etsi.org/01903/v1.3.2#"'

TAG_SIGNED_PROPERTIES = \
"""><xades:SignedProperties """

TAG_SIGNED_SIGNATURE_PROPERTIES = \
"""Id="S0-SignedProperties">
<xades:SignedSignatureProperties Id="S0-SignedSignatureProperties">
"""

TAG_SIGNING_CERT = \
"""<xades:SigningCertificate>
<xades:Cert>
<xades:CertDigest>
"""

TAG_SIGNED_DATA_OBJECTS = \
"""</xades:Cert>
</xades:SigningCertificate>
<xades:SignaturePolicyIdentifier>
<xades:SignaturePolicyId>
<xades:SigPolicyId>
<xades:Identifier Qualifier="OIDAsURN">
urn:oid:1.3.6.1.4.1.10015.1000.3.2.1</xades:Identifier>
</xades:SigPolicyId>
<xades:SigPolicyHash>
<ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256">
</ds:DigestMethod>
<ds:DigestValue>3Tl1oILSvOAWomdI9VeWV6IA/32eSXRUri9kPEz1IVs=</ds:DigestValue>
</xades:SigPolicyHash>
<xades:SigPolicyQualifiers>
<xades:SigPolicyQualifier>
<xades:SPURI>
https://www.sk.ee/repository/bdoc-spec21.pdf</xades:SPURI>
</xades:SigPolicyQualifier>
</xades:SigPolicyQualifiers>
</xades:SignaturePolicyId>
</xades:SignaturePolicyIdentifier>

<xades:SignatureProductionPlace>
</xades:SignatureProductionPlace>
</xades:SignedSignatureProperties>
<xades:SignedDataObjectProperties>
"""

TAG_END = \
"""</xades:QualifyingProperties></ds:Object>
</ds:Signature>
</asic:XAdESSignatures>"""

SIGNATURE_URIS = (
        "http://www.w3.org/2001/04/xmldsig-more#rsa-sha224",
        "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
        "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha256"
    )

DIGEST_URIS = (
        "http://www.w3.org/2001/04/xmldsig-more#sha224",
        "http://www.w3.org/2001/04/xmlenc#sha256"
    )


def check_prefix(inp, prefix):
    if inp.startswith(prefix):
        return len(prefix)
    return -1


def check_optional(inp, prefix):
    ret = check_prefix(inp, prefix)
    if ret == -1:
        return 0
    return ret


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


def check_either(inp, a, b):
    validator, arguments = a
    ret = validator(inp, **arguments)
    if ret == -1:
        validator, arguments = b
        ret = validator(inp, **arguments)
        if ret == -1:
            return -1
    return ret


def check_dataobjects(inp, questions):
    data_object = "<xades:DataObjectFormat ObjectReference=\"#S0-ref-%d\">\n" + \
                  "<xades:MimeType>application/octet-stream</xades:MimeType>\n" + \
                  "</xades:DataObjectFormat>\n"
    offset = 0
    for i in range(len(questions)):
        ret = check_prefix(inp[offset:], data_object % i)
        if ret == -1:
            return -1
        offset += ret

    return offset


def check_references(inp, questions):

    taglist = ["<ds:Reference Id=\"S0-ref-%d\" URI=\"/%s.evote\">\n" % (i, questions[i])
                for i in range(len(questions))]
    taglist.append("<ds:Reference Id=\"S0-ref-sp\" Type=\"http://uri.etsi.org/01903#SignedProperties\" URI=\"#S0-SignedProperties\">\n")

    offset = 0
    for tag_reference in taglist:
        ret = check_prefix(inp[offset:], tag_reference)
        if ret == -1:
            return -1
        offset += ret

        ret = check_tag(inp[offset:], "<ds:DigestMethod Algorithm=\"",
                "\">\n</ds:DigestMethod>\n",
                lambda x: x in DIGEST_URIS)
        if ret == -1:
            return -1
        offset += ret

        ret = check_tag(inp[offset:], "<ds:DigestValue>",
                "</ds:DigestValue>\n</ds:Reference>\n",
                formatutil.is_base64)
        if ret == -1:
            return -1
        offset += ret

    return offset


def check_unsigned(inp):
    from election import Election
    if not Election().is_hts():
        return -1

    offset = 0

    ret = check_prefix(inp[offset:],
            "<xades:UnsignedProperties Id=\"S0-UnsigedProperties\">\n" +
            "<xades:UnsignedSignatureProperties Id=\"S0-UnsigedSignatureProperties\">\n" +
            "<xades:CertificateValues Id=\"S0-CertificateValues\">\n")
    if ret == -1:
        return -1
    offset += ret

    for cert_id in ("S0-CA_CERT1", "S0-RESPONDER_CERT", "N0-CA_CERT3"):
        ret = check_tag(inp[offset:],
                "<xades:EncapsulatedX509Certificate Id=\"%s\">\n" % cert_id,
                "</xades:EncapsulatedX509Certificate>\n", formatutil.is_base64_lines)
        if ret == -1:
            return -1
        offset += ret

    ret = check_prefix(inp[offset:], "</xades:CertificateValues>\n" +
            "<xades:RevocationValues Id=\"S0-RevocationValues\">\n" +
            "<xades:OCSPValues>")
    if ret == -1:
        return -1
    offset += ret

    ret = check_tag(inp[offset:], "<xades:EncapsulatedOCSPValue Id=\"N0\">\n",
            "</xades:EncapsulatedOCSPValue>\n" +
            "</xades:OCSPValues></xades:RevocationValues></xades:UnsignedSignatureProperties>\n" +
            "</xades:UnsignedProperties>",
            formatutil.is_base64_lines)
    if ret == -1:
        return -1
    offset += ret

    return offset


def is_well_formed_id_signature(sigdata, questions):

    validators = (
            (check_prefix, { "prefix": TAG_XADES_SIGNATURES }),

            (check_optional, { "prefix": TAG_NAMESPACE }),

            (check_prefix, { "prefix": TAG_CANONICALIZATION_METHOD }),

            (check_tag, { "tag_start": "<ds:SignatureMethod Algorithm=\"",
                          "is_good": lambda x: x in SIGNATURE_URIS,
                          "tag_end": "\">\n</ds:SignatureMethod>\n" }),

            (check_references, { "questions": questions }),

            (check_tag, { "tag_start": "</ds:SignedInfo><ds:SignatureValue Id=\"S0-SIG\">\n",
                          "is_good": formatutil.is_base64_lines,
                          "tag_end": "</ds:SignatureValue>\n" }),

            (check_tag, { "tag_start": "<ds:KeyInfo Id=\"S0-KeyInfo\">\n<ds:X509Data><ds:X509Certificate>",
                          "is_good": formatutil.is_base64_lines,
                          "tag_end": "</ds:X509Certificate></ds:X509Data></ds:KeyInfo>\n"}),

            (check_prefix, { "prefix": TAG_OBJECT }),

            (check_optional, { "prefix": TAG_OBJECT_NAMESPACE }),

            (check_prefix, { "prefix": TAG_SIGNED_PROPERTIES }),

            (check_optional, { "prefix": TAG_NAMESPACE }),

            (check_prefix, { "prefix": TAG_SIGNED_SIGNATURE_PROPERTIES }),

            (check_tag, { "tag_start": "<xades:SigningTime>",
                          "is_good": formatutil.is_signing_time,
                          "tag_end": "</xades:SigningTime>\n"}),

            (check_prefix, { "prefix": TAG_SIGNING_CERT }),

            (check_tag, { "tag_start": "<ds:DigestMethod Algorithm=\"",
                          "is_good": lambda x: x in DIGEST_URIS,
                          "tag_end": "\">\n</ds:DigestMethod>\n" }),

            (check_tag, { "tag_start": "<ds:DigestValue>",
                          "is_good": formatutil.is_base64,
                          "tag_end": "</ds:DigestValue>\n</xades:CertDigest>\n" }),

            (check_tag, { "tag_start": "<xades:IssuerSerial>\n<ds:X509IssuerName>",
                          "is_good": formatutil.is_200utf8,
                          "tag_end": "</ds:X509IssuerName>\n"}),

            (check_tag, { "tag_start": "<ds:X509SerialNumber>",
                          "is_good": formatutil.is_number100,
                          "tag_end": "</ds:X509SerialNumber>\n</xades:IssuerSerial>\n"}),

            (check_prefix, { "prefix": TAG_SIGNED_DATA_OBJECTS }),

            (check_dataobjects, { "questions": questions }),

            (check_prefix, { "prefix": "</xades:SignedDataObjectProperties>\n</xades:SignedProperties>" }),

            (check_either, { "a": (check_prefix, { "prefix": "\n<xades:UnsignedProperties></xades:UnsignedProperties>" }),
                             "b": (check_unsigned, {}) }),

            (check_prefix, { "prefix": TAG_END })
        )

    offset = 0
    for validator, arguments in validators:
        ret = validator(sigdata[offset:], **arguments)
        if ret == -1:
            return False, sigdata[offset:offset + 200]
        offset += ret

    if offset == len(sigdata.strip()):
        return True, ""

    return False, sigdata[offset:offset + 200]

# vim:set ts=4 sw=4 et fileencoding=utf8:
