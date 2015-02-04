#!/usr/bin/python
# -*- coding: utf-8 -*-

import bdocconfig
import bdocpython
import bdocpythonutils
import os
import sys

etc = '../../etc'
conf_dir = '../../bdocconf'

method = sys.argv[1]
if len(sys.argv) == 3:
    contentType = 'application/octet-stream'
elif len(sys.argv) == 4:
    contentType = sys.argv[3]
else:
    print "bdoctool mode file [content-type]"
    exit(1)

print 'Expecting content type:', contentType

with file(sys.argv[2]) as f:
    zipbytes = f.read()

bdocpython.initialize()

config = bdocconfig.BDocConfig()

bdoc = bdocpythonutils.BDocContainer()
bdoc.load_bytes(zipbytes)
profile_type = 'TM' if method == 'tm' else 'BES'
bdoc.validate(bdocpythonutils.ManifestProfile(profile_type,
                                              datatype = contentType))

sigfiles = bdoc.signatures.keys()
if len(sigfiles) == 0:
    raise Exception("BDoc ei sisalda ühtegi allkirja")

sigfiles = bdoc.signatures.keys()
if len(sigfiles) != 1:
    raise Exception("BDoc sisaldab rohkem kui ühte allkirja")

config.load(conf_dir)

verifier = bdocpython.BDocVerifier()
config.populate(verifier)
verifier.setSchemaDir(etc + '/schema')
certDir = etc + '/certs'
for el in os.listdir(certDir):
    print 'Adding certificate:', el
    verifier.addCertToStore(os.path.join(certDir, el))

if method == 'online' or method == 'tm':
    #verifier.addOCSPConf(issuer, url, cert, skew, maxAge)
    pass

for el in bdoc.documents:
    verifier.setDocument(bdoc.documents[el], el)

sig_fn = sigfiles[0]
sig_content = bdoc.signatures[sig_fn]

if method == 'online':
    print "Verify method: verifyInHTS"
    res = verifier.verifyInHTS(sig_content)
elif method == 'tm':
    print "Verify method: verifyTMOffline"
    res = verifier.verifyTMOffline(sig_content)
else:
    print "Verify method: verifyBESOffline"
    res = verifier.verifyBESOffline(sig_content)

print 'Result:', res.result
print 'Subject:', res.subject
print 'OCSP:', res.ocsp_time
print 'Error:', res.error

if method == 'online':
    bdoc.addTM(sig_fn, res.signature)
    bytes = bdoc.get_bytes()
    outf = open('tmp.tm.bdoc', 'w')
    outf.write(bytes)
    outf.close()

print 'Cert is valid:', res.cert_is_valid
print 'OCSP is good:', res.ocsp_is_good

