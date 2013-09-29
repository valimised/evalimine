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
import os
import os.path
import zipfile
import bdocpython
import xml.etree.ElementTree
import exception_msg
import shutil

REF_MIMETYPE = 'application/vnd.bdoc-1.0'
REF_FILE_MANIFEST = 'META-INF/manifest.xml'
REF_FILE_MIMETYPE = 'mimetype'

REF_MANIFEST_TMPL_1 = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>'
REF_MANIFEST_TMPL_2 = \
    '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmln' \
    's:manifest:1.0">'
REF_MANIFEST_TMPL_3 = \
    '<manifest:file-entry manifest:full-path="/" manifest:media-type="applic' \
    'ation/vnd.bdoc-1.0"/>'
REF_MANIFEST_TMPL_4 = '</manifest:manifest>'

REF_MANIFEST_LINES = [ \
    REF_MANIFEST_TMPL_1,
    REF_MANIFEST_TMPL_2,
    REF_MANIFEST_TMPL_3,
    REF_MANIFEST_TMPL_4]

# DigiDocService's manifest is formatted differently than qdigidocclient's and
# ours, so it needs a separate reference.
REF_MANIFEST_DDS_TMPL_1 = '<?xml version="1.0" encoding="UTF-8"?>'
REF_MANIFEST_DDS_TMPL_3 = \
    '<manifest:file-entry manifest:media-type="application/vnd.bdoc-1.0" man' \
    'ifest:full-path="/" />'

REF_MANIFEST_DDS_LINES = [ \
    REF_MANIFEST_DDS_TMPL_1,
    REF_MANIFEST_TMPL_2,
    REF_MANIFEST_DDS_TMPL_3,
    REF_MANIFEST_TMPL_4]

CONF_KNOWN_PARAMS = [ \
    'digest.uri']

CONF_NECESSARY_ELEMS = [ \
    'bdoc.conf',
    'ca',
    'ocsp',
    'schema',
    'schema/datatypes.dtd',
    'schema/XAdES.xsd',
    'schema/XAdES111.xsd',
    'schema/xmldsig-core-schema.xsd',
    'schema/XMLSchema.dtd']

class BDocConfig:

    def __init__(self):
        self.__root = None
        self.__ocsp = {}
        self.__param = {}
        self.__oids = []

    def __del__(self):
        pass

    def _handle_ocsp(self, elems):
        for _el in elems:
            if len(_el) != 4:
                raise Exception, 'Invalid OCSP configuration'

            if (_el[0].tag != 'url') or (_el[1].tag != 'cert'):
                raise Exception, 'Invalid OCSP configuration - tag'

            if (_el[2].tag != 'skew') or (_el[3].tag != 'maxAge'):
                raise Exception, 'Invalid OCSP configuration - tag'

            if (not 'issuer' in _el.attrib) or (len(_el.attrib) != 1):
                raise Exception, 'Invalid OCSP configuration - issuer'

            _certf = os.path.join(self.__root, 'ocsp', _el[1].text)

            if not os.access(_certf, os.F_OK):
                raise Exception, 'Invalid OCSP configuration - cert %s' % _certf

            if not os.access(_certf, os.R_OK):
                raise Exception, 'Invalid OCSP configuration - cert'

            self.__ocsp[_el.attrib['issuer']] = {'url': _el[0].text, \
                                                'cert': _el[1].text, \
                                                'skew': long(_el[2].text), \
                                                'maxAge': long(_el[3].text)}

    def _handle_param(self, elems):
        for _el in elems:
            if (not 'name' in _el.attrib) or (len(_el.attrib) != 1):
                raise Exception, 'Invalid parameter configuration'

            if not _el.attrib['name'] in CONF_KNOWN_PARAMS:
                raise Exception, 'Invalid parameter configuration'

            self.__param[_el.attrib['name']] = _el.text

    def _handle_policies(self, elem):
        for oids in elem:
            for oid in oids:
                self.__oids.append(oid.text.strip())

    def save(self, dirname):
        import stat
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
        shutil.copytree(self.__root, dirname)
        fmode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP
        dmode = stat.S_IRWXU | stat.S_IRWXG
        os.chmod(dirname, dmode)
        for root, dirs, files in os.walk(dirname):
            for name in files:
                os.chmod(os.path.join(root, name), fmode)
            for name in dirs:
                os.chmod(os.path.join(root, name), dmode)


    def load(self, dirname):
        self.__root = dirname

        for _el in CONF_NECESSARY_ELEMS:
            _path = os.path.join(self.__root, _el)
            if not os.access(_path, os.F_OK):
                raise Exception, "Missing conf item \"%s\"" % _el

            if not os.access(_path, os.R_OK):
                raise Exception, "Missing conf item \"%s\"" % _el

        _tree = xml.etree.ElementTree.ElementTree()
        _tree.parse(os.path.join(self.__root, 'bdoc.conf'))

        _ocsp_elems = _tree.getiterator('ocsp')
        self._handle_ocsp(_ocsp_elems)

        _param_elems = _tree.getiterator('param')
        self._handle_param(_param_elems)

        _policies_elems = _tree.getiterator('policies')
        self._handle_policies(_policies_elems)


    def _ocsp_cert_path(self, el):
        return os.path.join(self.__root, 'ocsp', self.__ocsp[el]['cert'])

    def populate(self, ver):
        for el in self.__ocsp:
            ver.addOCSPConf(el, self.__ocsp[el]['url'], \
                self._ocsp_cert_path(el), \
                self.__ocsp[el]['skew'], self.__ocsp[el]['maxAge'])

        ver.setSchemaDir(os.path.join(self.__root, 'schema'))
        ver.setDigestURI(self.__param['digest.uri'])

        cadir = os.path.join(self.__root, 'ca')

        for el in os.listdir(cadir):
            ver.addCertToStore(os.path.join(cadir, el))

    def get_ocsp_responders(self):
        # NB! One URL gets into dict only once
        ret = {}
        for el in self.__ocsp:
            url = self.__ocsp[el]['url']
            path = self._ocsp_cert_path(el)
            ret[url] = path
        return ret

    def have_oid(self, oid):
        return oid in self.__oids

    def is_good_mid_cert(self, b64cert):
        import base64
        cert = base64.b64decode(b64cert)

        if cert == None:
            raise Exception, 'Invalid certificate'

        cd = bdocpython.CertificateData()
        cd.decode(cert)

        for pol in bdocpython.list_policies(cert):
            if self.have_oid(pol):
                return False, 'Reject: policy %s' % pol

        return True, None


class ManifestProfile:

    def __init__(self, sigtype, datatype = None):
        self.__sigtype = sigtype
        self.__datatype = "application/x-encrypted-vote"
        if datatype:
            self.__datatype = datatype

    def __del__(self):
        pass

    def is_signature(self, filename):
        return ((filename.count('signature') > 0) and
            (filename.startswith('META-INF/')))

    def file_entry(self, filename, dds = False, sigtype = None):
        mimetype = self.__datatype
        if self.is_signature(filename):
            mimetype = "signature/bdoc-1.0/%s" % (sigtype or self.__sigtype)

        lst = ["<manifest:file-entry",
               " manifest:full-path=\"%s\"" % filename,
               " manifest:media-type=\"%s\"" % mimetype,
               "/>"]
        if dds:
            # DigiDocService has media-type and full-path swapped...
            lst[1], lst[2] = lst[2], lst[1]
            # ...and a space before the closing bracket.
            lst[3] = " " + lst[3]
        return "".join(lst)

    def file_entry_dds(self, filename, sigtype = None):
        return self.file_entry(filename, True, sigtype)

    def tm_sig_entry(self, filename, dds = False):
        return self.file_entry(filename, dds, "TM")


class BDocContainer:

    def __init__(self):
        self.__bdoc = None
        self.__manifest = None
        self.documents = {}
        self.signatures = {}
        self.prof = 'BES'


    def __del__(self):
        if self.__bdoc:
            self.__bdoc.close()

    def count_data_files(self):
        return len(self.documents)

    def count_signatures(self):
        return len(self.signatures)

    def load(self, bdocfile):
        self.__bdoc = zipfile.ZipFile(bdocfile)
        if self.__bdoc.testzip() != None:
            raise Exception, 'Invalid zipfile'

    def load_bytes(self, data):
        import StringIO
        dfile = StringIO.StringIO(data)
        self.load(dfile)

    def get_bytes(self):
        import StringIO
        dfile = StringIO.StringIO()
        try:
            dfile = StringIO.StringIO()
            zip = zipfile.ZipFile(dfile, 'w')
            for el in self.documents:
                zip.writestr(el, self.documents[el])

            for el in self.signatures:
                zip.writestr(el, self.signatures[el])

            zip.writestr(REF_FILE_MIMETYPE, REF_MIMETYPE)
            zip.writestr(REF_FILE_MANIFEST, self.__manifest)
            zip.close()
            return dfile.getvalue()
        finally:
            dfile.close()


    def addTM(self, filename, signature):
        _lst = self.__manifest.rstrip().split('\n')
        besprofile = ManifestProfile('BES')
        idx = _lst.index(besprofile.file_entry(filename))
        _lst.pop(idx)
        _lst.insert(idx, besprofile.tm_sig_entry(filename))
        self.signatures[filename] = signature
        self.__manifest = '\n'.join(_lst)
        self.prof = 'TM'


    def _validate_mimetype(self, contents):

        if not REF_FILE_MIMETYPE in contents:
            return False

        del contents[REF_FILE_MIMETYPE]

        return REF_MIMETYPE == self.__bdoc.read(REF_FILE_MIMETYPE)

    def _acquire_manifest(self, contents):
        if not REF_FILE_MANIFEST in contents:
            return False

        del contents[REF_FILE_MANIFEST]
        self.__manifest = self.__bdoc.read(REF_FILE_MANIFEST)
        return True

    def validateflex(self):

        profile_b = ManifestProfile('BES')
        profile_t = ManifestProfile('TM')

        _infos = self.__bdoc.infolist()
        _contents = {}
        for _el in _infos:
            _contents[_el.filename.encode("utf8")] = None

        if not self._validate_mimetype(_contents):
            raise Exception, 'Invalid or missing MIME type'

        if not self._acquire_manifest(_contents):
            raise Exception, 'Could not load manifest'

        _lst = self.__manifest.rstrip().split('\n')
        _lst = filter(None, map(str.strip, _lst))
        _len1 = len(_lst)
        _input_set = set(_lst)
        _len2 = len(_input_set)

        if _len1 != _len2:
            raise Exception, 'Invalid manifest: input contains equal lines'

        _reference_set_b = set(REF_MANIFEST_LINES)
        _reference_set_t = set(REF_MANIFEST_LINES)
        _reference_set_dds = set(REF_MANIFEST_DDS_LINES)

        for _el in _contents:
            if _el != 'META-INF/':
                _reference_set_b.add(profile_b.file_entry(_el))
                _reference_set_t.add(profile_t.file_entry(_el))
                _reference_set_dds.add(profile_t.file_entry_dds(_el))

        profile = None
        if _reference_set_b == _input_set:
            self.prof = 'BES'
            profile = profile_b
        elif _reference_set_t == _input_set or _reference_set_dds == _input_set:
            self.prof = 'TM'
            profile = profile_t
        else:
            raise Exception, 'Invalid manifest: not equal to reference set'

        for _el in _contents:
            if (_el != 'META-INF/'):
                if profile.is_signature(_el):
                    self.signatures[_el] = self.__bdoc.read(_el)
                else:
                    self.documents[_el] = self.__bdoc.read(_el)


    def validate(self, profile):

        _infos = self.__bdoc.infolist()
        _contents = {}
        for _el in _infos:
            _contents[_el.filename.encode("utf8")] = None

        if not self._validate_mimetype(_contents):
            raise Exception, 'Invalid or missing MIME type'

        if not self._acquire_manifest(_contents):
            raise Exception, 'Could not load manifest'

        _lst = self.__manifest.rstrip().split('\n')
        _lst = filter(None, map(str.strip, _lst))
        _len1 = len(_lst)
        _input_set = set(_lst)
        _len2 = len(_input_set)

        if _len1 != _len2:
            raise Exception, 'Invalid manifest: input contains equal lines'

        _reference_set = set(REF_MANIFEST_LINES)
        _reference_set_dds = set(REF_MANIFEST_DDS_LINES)

        for _el in _contents:
            if _el != 'META-INF/':
                _reference_set.add(profile.file_entry(_el))
                _reference_set_dds.add(profile.file_entry_dds(_el))

        if _reference_set != _input_set and _reference_set_dds != _input_set:
            raise Exception, 'Invalid manifest: not equal to reference set'

        for _el in _contents:
            if (_el != 'META-INF/'):
                if profile.is_signature(_el):
                    self.signatures[_el] = self.__bdoc.read(_el)
                else:
                    self.documents[_el] = self.__bdoc.read(_el)


def save_temporary(data):
    import fcntl
    import tempfile

    tmp_fd = None
    tmp_fn = None
    tmp_file = None
    try:
        tmp_fd, tmp_fn = tempfile.mkstemp()
        tmp_file = os.fdopen(tmp_fd, 'w')
        tmp_fd = None
        fcntl.lockf(tmp_file, fcntl.LOCK_EX)
        tmp_file.write(data)
        tmp_file.close()
        tmp_file = None
    finally:
        if tmp_fd:
            os.close(tmp_fd)
        if tmp_file:
            tmp_file.close()
    return tmp_fn


def get_doc_content_file(filename, datatype = 'application/octet-stream'):
    bdoc = BDocContainer()
    bdoc.load(filename)
    profile = ManifestProfile('TM', datatype)
    bdoc.validate(profile)

    if not len(bdoc.documents) == 1:
        raise Exception("Invalid document count in BDOC")

    doc_fn, doc_content = bdoc.documents.popitem()
    return save_temporary(doc_content)


if __name__ == '__main__':
    pass

# vim:set ts=4 sw=4 et fileencoding=utf8:
