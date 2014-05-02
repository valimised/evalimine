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

import os
import zipfile
import exception_msg

REF_MIMETYPE = 'application/vnd.etsi.asic-e+zip'
REF_FILE_MANIFEST = 'META-INF/manifest.xml'
REF_FILE_MIMETYPE = 'mimetype'

REF_MANIFEST_TMPL_1 = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>'
REF_MANIFEST_TMPL_2 = \
    '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmln' \
    's:manifest:1.0">'
REF_MANIFEST_TMPL_3 = \
    '<manifest:file-entry manifest:full-path="/" manifest:media-type="applic' \
    'ation/vnd.etsi.asic-e+zip"/>'
REF_MANIFEST_TMPL_4 = '</manifest:manifest>'

REF_MANIFEST_LINES = [ \
    REF_MANIFEST_TMPL_1,
    REF_MANIFEST_TMPL_2,
    REF_MANIFEST_TMPL_3,
    REF_MANIFEST_TMPL_4]

# DigiDocService's manifest is formatted differently than qdigidocclient's and
# ours, so it needs a separate reference.
REF_MANIFEST_DDS_TMPL_1 = '<?xml version="1.0" encoding="utf-8"?>'
REF_MANIFEST_DDS_TMPL_3 = \
        '<manifest:file-entry manifest:media-type='\
        '"application/vnd.etsi.asic-e+zip" manifest:full-path="/" />'

REF_MANIFEST_DDS_LINES = [ \
    REF_MANIFEST_DDS_TMPL_1,
    REF_MANIFEST_TMPL_2,
    REF_MANIFEST_DDS_TMPL_3,
    REF_MANIFEST_TMPL_4]


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

    def sigtype(self):
        return self.__sigtype


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
            zip.writestr(REF_FILE_MIMETYPE, REF_MIMETYPE)
            for el in self.documents:
                zip.writestr(el, self.documents[el])

            for el in self.signatures:
                zip.writestr(el, self.signatures[el])

            zip.writestr(REF_FILE_MANIFEST, self.__manifest)
            zip.close()
            return dfile.getvalue()
        finally:
            dfile.close()


    def addTM(self, filename, signature):
        self.signatures[filename] = signature
        self.prof = 'TM'


    def _validate_mimetype(self, contents):

        if not REF_FILE_MIMETYPE in contents:
            return False

        del contents[REF_FILE_MIMETYPE]

        mimetype = self.__bdoc.read(REF_FILE_MIMETYPE)
        if REF_MIMETYPE == mimetype:
            return True
        return False

    def _acquire_manifest(self, contents):
        if not REF_FILE_MANIFEST in contents:
            return False

        del contents[REF_FILE_MANIFEST]
        self.__manifest = self.__bdoc.read(REF_FILE_MANIFEST)
        return True

    def validateflex(self):
        def is_dds_profile(idx):
            return idx == 2
        profile_b = ManifestProfile('BES')
        profile_t = ManifestProfile('TM')
        self.validateimpl([profile_b, profile_t, profile_t], is_dds_profile)

    def validate(self, profile):
        def is_dds_profile(idx):
            return idx == 1
        self.validateimpl([profile, profile], is_dds_profile)

    def validateimpl(self, profiles, is_dds_profile):
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

        _reference_sets = []
        for _i in range(len(profiles)):
            if is_dds_profile(_i):
                _reference_sets.append(set(REF_MANIFEST_DDS_LINES))
            else:
                _reference_sets.append(set(REF_MANIFEST_LINES))

        for _el in _contents:
            if _el != 'META-INF/' and \
                    not profiles[0].is_signature(_el):
                for _i, _profile in enumerate(profiles):
                    _reference_sets[_i].add(_profile.file_entry(_el, is_dds_profile(_i)))

        _profile = None
        for _i, _reference_set in enumerate(_reference_sets):
            if _reference_set == _input_set:
                _profile = profiles[_i]
                break
        else:
            print _reference_sets
            print _input_set
            raise Exception, 'Invalid manifest: not equal to reference set'

        self.prof = _profile.sigtype()
        for _el in _contents:
            if (_el != 'META-INF/'):
                if _profile.is_signature(_el):
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
