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

import sys
from election import Election
import formatutil
import bdocpython
import bdocpythonutils
import evlogdata

G_RIGHTS = ['TYHIS',
        'VALIK',
        'JAOSK']

G_DESCS = {'TYHIS': 'Tühistus- ja ennistusnimekirja allkirjastaja',
     'VALIK': 'Valikute nimekirja allkirjastaja',
     'JAOSK': 'Jaoskondade ja ringkondade nimekirja allkirjastaja'}

def get_personal_code(subj):
    return subj.partition('CN=')[2].split(',')[2].strip()

def _proper_right(right):
    """
    Kas volitus on meile sobiv?
    """
    return right in G_RIGHTS


class VoteLog:

    def __init__(self, bdocdata):
        self.alines = []
        self.elines = []
        self.bdoc = bdocpythonutils.BDocContainer()
        self.bdoc.load_bytes(bdocdata)
        self.bdoc.validateflex()

        _doc_count = len(self.bdoc.documents)
        if _doc_count == 0:
            raise Exception, "BDoc ei sisalda ühtegi andmefaili"

    def log_signingcert(self):
        if len(self.bdoc.signatures) != 1:
           raise Exception, "BDoc sisaldab rohkem kui ühte allkirja"

        _, sig_content = self.bdoc.signatures.popitem()

        start = '<X509Certificate>'
        end = '</X509Certificate>'
        cert = sig_content.partition(start)[2].partition(end)[0].strip()

        alog, elog = evlogdata.get_cert_data_log(cert, 'signingcert', True)
        self.alines.append(alog)

        if elog:
            self.elines.append(elog)

    def log_documents(self):
        for el in self.bdoc.documents:
            self.alines.append(evlogdata.get_vote(el, self.bdoc.documents[el]))


def analyze_signature_for_log(bdocdata):
    vl = VoteLog(bdocdata)
    vl.log_signingcert()
    return vl.alines, vl.elines


def analyze_vote_for_log(bdocdata):
    vl = VoteLog(bdocdata)
    vl.log_signingcert()
    vl.log_documents()
    return vl.alines, vl.elines


def analyze_vote(bdocfile, config):

    bdoc = bdocpythonutils.BDocContainer()
    bdoc.load(bdocfile)
    profile = bdocpythonutils.ManifestProfile('TM')
    bdoc.validate(profile)

    _doc_count = len(bdoc.documents)
    if _doc_count == 0:
        raise Exception, "BDoc ei sisalda ühtegi andmefaili"

    if len(bdoc.signatures) != 1:
        raise Exception, "BDoc sisaldab rohkem kui ühte allkirja"

    verifier = bdocpython.BDocVerifier()
    config.populate(verifier)

    for el in bdoc.documents:
        verifier.setDocument(bdoc.documents[el], el)

    _, sig_content = bdoc.signatures.popitem()
    return verifier.verifyTMOffline(sig_content)

def check_vote_hes_mobid(bdocdata, config):

    bdoc = bdocpythonutils.BDocContainer()
    bdoc.load_bytes(bdocdata)
    profile = bdocpythonutils.ManifestProfile('TM')
    bdoc.validate(profile)

    _doc_count = len(bdoc.documents)
    if _doc_count == 0:
        raise Exception, "BDoc ei sisalda ühtegi andmefaili"

    if len(bdoc.signatures) != 1:
        raise Exception, "BDoc sisaldab rohkem kui ühte allkirja"

    verifier = bdocpython.BDocVerifier()
    config.populate(verifier)

    for el in bdoc.documents:
        verifier.setDocument(bdoc.documents[el], el)

    _, sig_content = bdoc.signatures.popitem()
    return verifier.verifyTMOffline(sig_content)


def check_vote_hes(bdocdata, config):

    bdoc = bdocpythonutils.BDocContainer()
    bdoc.load_bytes(bdocdata)
    profile = bdocpythonutils.ManifestProfile('BES')
    bdoc.validate(profile)

    _doc_count = len(bdoc.documents)
    if _doc_count == 0:
        raise Exception, "BDoc ei sisalda ühtegi andmefaili"

    if len(bdoc.signatures) != 1:
        raise Exception, "BDoc sisaldab rohkem kui ühte allkirja"

    verifier = bdocpython.BDocVerifier()
    config.populate(verifier)

    for el in bdoc.documents:
        verifier.setDocument(bdoc.documents[el], el)

    _, sig_content = bdoc.signatures.popitem()
    return verifier.verifyBESOffline(sig_content)


def kontrolli_volitusi(elid, bdocfile, volitus, config):

    bdoc = bdocpythonutils.BDocContainer()
    bdoc.load(bdocfile)
    profile = bdocpythonutils.ManifestProfile('TM', 'application/octet-stream')
    bdoc.validate(profile)

    _doc_count = len(bdoc.documents)
    if _doc_count == 0:
        raise Exception, "BDoc ei sisalda ühtegi andmefaili"

    if _doc_count != 1:
        raise Exception, "BDoc sisaldab %d andmefaili" % _doc_count

    if len(bdoc.signatures) != 1:
        raise Exception, "BDoc sisaldab rohkem kui ühte allkirja"

    verifier = bdocpython.BDocVerifier()
    config.populate(verifier)

    doc_fn, doc_content = bdoc.documents.popitem()
    verifier.setDocument(doc_content, doc_fn)
    _signercode = None
    _, sig_content = bdoc.signatures.popitem()

    res = verifier.verifyTMOffline(sig_content)
    if res.result:
        _signercode = get_personal_code(res.subject)
    else:
        raise Exception, "Invalid signature %s" % res.error

    _rights = Rights(elid)
    if _rights.has(_signercode, volitus):
        return True, '', _signercode

    return False, \
        "Isikul koodiga %s puuduvad volitused " \
        "antud operatsiooni sooritamiseks" \
        % _signercode, _signercode


class Rights:

    def __init__(self, elid):
        self.reg = Election().get_sub_reg(elid, ['common', 'rights'])

    def descr(self, code):
        """
        Tagastab tegelase kohta käiva kirjelduse
        """
        if not formatutil.is_isikukood(code):
            raise Exception('Vigane isikukood')

        if self.reg.check([code, 'description']):
            return self.reg.read_string_value([code], 'description').value
        else:
            return 'Andmed puuduvad'

    def listall(self):
        """
        Tagastab kõik volitused
        """
        lst = self.reg.list_keys()

        ret = ''
        for ele in lst:
            ret = ret + '\n' + self.listuser(ele)
        return ret.strip()

    def _create_user(self, code):
        """     Loome kasutaja, kui teda veel pole
        """
        if not formatutil.is_isikukood(code):
            raise Exception('Vigane isikukood')

        self.reg.ensure_key([code, 'rights'])

    def add(self, code, right):
        """
        Lisab uue volituse
        """
        new_right = right.upper()
        if not _proper_right(new_right):
            raise Exception('Vigane volitus')

        self._create_user(code)

        if not self.has(code, new_right):
            self.reg.create_value([code, 'rights'], new_right, '')
            return True

        return False

    def adddesc(self, code, desc):
        """
        Lisab kasutajale kirjelduse
        """
        self._create_user(code)
        self.reg.create_value([code], 'description', desc)
        return True

    def remove(self, code, right):
        """
        Võtab kasutajalt volituse
        """

        if not formatutil.is_isikukood(code):
            raise Exception('Vigane isikukood')

        new_right = right.upper()
        if not _proper_right(new_right):
            raise Exception('Vigane volitus')

        if self.has(code, new_right):
            self.reg.delete_value([code, 'rights'], new_right)
            return True

        return False

    def remuser(self, code):
        """
        Eemaldab ühe kasutaja volituste failist
        """
        if not formatutil.is_isikukood(code):
            raise Exception('Vigane isikukood')

        return self.reg.ensure_no_key([code])

    def remall(self):
        """
        Eemaldab kõik volitused
        """
        self.reg.reset_key([''])
        return True

    def has(self, code, right):
        """
        Kas koodil on vastav volitus
        """

        if not formatutil.is_isikukood(code):
            raise Exception('Vigane isikukood')

        new_right = right.upper()
        if not _proper_right(new_right):
            raise Exception('Vigane volitus')

        if not self.reg.check([code, 'rights', new_right]):
            return False
        return True

    def listuser(self, code):
        """
        Ainult konkreetse kasutaja õigused
        """
        if not formatutil.is_isikukood(code):
            raise Exception('Vigane isikukood')

        ret = ''
        if self.reg.check([code]):
            ret = ret + code
            ret = ret + ' (' + self.descr(code) + ')'
            sub_list = self.reg.list_keys([code, 'rights'])
            if len(sub_list) > 0:
                for _s in sub_list:
                    ret = ret + '\n\t' + G_DESCS[_s]
            else:
                ret = ret + '\n\tVolitused puuduvad'
        return ret.strip()


def usage():
    print "Kasutamine:"
    print "    %s <valimiste-id> add <isikukood> <volitus>" % sys.argv[0]
    print "        - Annab isikukoodile volituse"
    print "    %s <valimiste-id> desc <isikukood> <kirjeldus>" % sys.argv[0]
    print "        - Annab isikukoodile kirjelduse"
    print "    %s <valimiste-id> rem <isikukood> <volitus>" % sys.argv[0]
    print "        - Võtab isikukoodilt volituse"
    print "    %s <valimiste-id> remuser <isikukood>" % sys.argv[0]
    print "        - Võtab isikukoodilt kõik volitused"
    print "    %s <valimiste-id> remall" % sys.argv[0]
    print "        - Eemaldab kõik volitused"
    print "    %s <valimiste-id> has <isikukood> <volitus>" % sys.argv[0]
    print "        - Küsib isikukoodi volituse olemasolu"
    print "    %s <valimiste-id> listuser <isikukood>" % sys.argv[0]
    print "        - Kuvab isikukoodi volitused"
    print "    %s <valimiste-id> listall" % sys.argv[0]
    print "        - Kuvab kõik volitused"
    print "Võimalikud volitused:"
    print "    " + G_RIGHTS[0] + " - " + G_DESCS[G_RIGHTS[0]]
    print "    " + G_RIGHTS[1] + " - " + G_DESCS[G_RIGHTS[1]]
    print "    " + G_RIGHTS[2] + " - " + G_DESCS[G_RIGHTS[2]]
    sys.exit(1)


def main_function():

    params_one = ['listall', 'remall']
    params_two = ['add', 'desc', 'rem', 'has']
    params_three = ['remuser', 'listuser']

    if len(sys.argv) < 3:
        usage()

    if not ((sys.argv[2] in params_one) or \
        (sys.argv[2] in params_two) or \
        (sys.argv[2] in params_three)):
        usage()

    if sys.argv[2] in params_two and len(sys.argv) < 5:
        usage()

    if sys.argv[2] in params_three and len(sys.argv) < 4:
        usage()

    try:

        _rights = Rights(sys.argv[1])

        if sys.argv[2] == 'add':
            res = _rights.add(sys.argv[3], sys.argv[4])
            if not res:
                print 'Isikul %s on juba volitus "%s"' % \
                    (sys.argv[3], G_DESCS[sys.argv[4]])
            else:
                print 'Volitus "%s" antud' % G_DESCS[sys.argv[4]]
        elif sys.argv[2] == 'desc':
            # kirjeldus võib koosneda mitmest sõnast
            name = " ".join(sys.argv[4:])
            res = _rights.adddesc(sys.argv[3], name)
            print "Kirjeldus lisatud"
        elif sys.argv[2] == 'rem':
            res = _rights.remove(sys.argv[3], sys.argv[4])
            if not res:
                print 'Isikul %s pole volitust %s' % \
                    (sys.argv[3], G_DESCS[sys.argv[4]])
            else:
                print "Volitus kustutatud"
        elif sys.argv[2] == 'remuser':
            res = _rights.remuser(sys.argv[3])
            if not res:
                print "Ei leia isikut %s" % sys.argv[3]
            else:
                print "Isik kustutatud"
        elif sys.argv[2] == 'has':
            res = _rights.has(sys.argv[3], sys.argv[4])
            if not res:
                print "On"
            else:
                print "Ei ole"
        elif sys.argv[2] == 'listuser':
            res = _rights.listuser(sys.argv[3])
            print res
        elif sys.argv[2] == 'listall':
            res = _rights.listall()
            print res
        elif sys.argv[2] == 'remall':
            res = _rights.remall()
            print "Kõik volitused kustutatud"
        else:
            usage()

    except Exception, ex: # pylint: disable=W0703
        print "Viga: %s" % ex
        sys.exit(1)


if __name__ == '__main__':
    main_function()

# vim:set ts=4 sw=4 et fileencoding=utf8:
