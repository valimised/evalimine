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
import os.path
import xml.etree.ElementTree
import shutil

CONF_KNOWN_PARAMS = [
    'digest.uri']

CONF_NECESSARY_ELEMS = [
    'bdoc.conf',
    'ca',
    'ocsp',
    'schema',
    'schema/datatypes.dtd',
    'schema/XAdES.xsd',
    'schema/xmldsig-core-schema.xsd',
    'schema/XMLSchema.dtd']


class BDocConfig:

    def __init__(self):
        self.__root = None
        self.__ocsp = {}
        self.__param = {}

    def __del__(self):
        pass

    def _handle_ocsp(self, elems):
        for _el in elems:
            if len(_el) != 4:
                raise Exception('Invalid OCSP configuration')

            if (_el[0].tag != 'url') or (_el[1].tag != 'cert'):
                raise Exception('Invalid OCSP configuration - tag')

            if (_el[2].tag != 'skew') or (_el[3].tag != 'maxAge'):
                raise Exception('Invalid OCSP configuration - tag')

            if (not 'issuer' in _el.attrib) or (len(_el.attrib) != 1):
                raise Exception('Invalid OCSP configuration - issuer')

            _certf = os.path.join(self.__root, 'ocsp', _el[1].text)

            if not os.access(_certf, os.F_OK):
                raise Exception('Invalid OCSP configuration - cert %s' % _certf)

            if not os.access(_certf, os.R_OK):
                raise Exception('Invalid OCSP configuration - cert')

            self.__ocsp[_el.attrib['issuer']] = {'url': _el[0].text,
                                                'cert': _el[1].text,
                                                'skew': long(_el[2].text),
                                                'maxAge': long(_el[3].text)}

    def _handle_param(self, elems):
        for _el in elems:
            if (not 'name' in _el.attrib) or (len(_el.attrib) != 1):
                raise Exception('Invalid parameter configuration')

            if not _el.attrib['name'] in CONF_KNOWN_PARAMS:
                raise Exception('Invalid parameter configuration')

            self.__param[_el.attrib['name']] = _el.text

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
                raise Exception("Missing conf item \"%s\"" % _el)

            if not os.access(_path, os.R_OK):
                raise Exception("Missing conf item \"%s\"" % _el)

        _tree = xml.etree.ElementTree.ElementTree()
        _tree.parse(os.path.join(self.__root, 'bdoc.conf'))

        _ocsp_elems = _tree.getiterator('ocsp')
        self._handle_ocsp(_ocsp_elems)

        _param_elems = _tree.getiterator('param')
        self._handle_param(_param_elems)

    def _ocsp_cert_path(self, el):
        return os.path.join(self.__root, 'ocsp', self.__ocsp[el]['cert'])

    def populate(self, ver):
        for el in self.__ocsp:
            ver.addOCSPConf(el, self.__ocsp[el]['url'],
                self._ocsp_cert_path(el),
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


if __name__ == '__main__':
    pass

# vim:set ts=4 sw=4 et fileencoding=utf8:
