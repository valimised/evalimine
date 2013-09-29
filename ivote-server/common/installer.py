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
import config_common
import init_conf
import regrights
import tempfile
import shutil

import bdocpython
import bdocpythonutils

required = ["*.mobidurl", "*.mobidservice", "*.mobidauthmsg", \
        "*.mobidsignmsg", "*.hts", "*.verifytimeout", "*.verifymaxtries", \
        "*.elections"]

election_required= ["voters", "choices", "districts", "type", "description"]
election_optional= ["ALL", "VALIK", "JAOSK", "TYHIS"]

def add_right(rr, right, persons):
    for person in persons.split():
        rr.add(person, right)


def manage_rights(el, conf):
    rr = regrights.Rights(el)
    for right in ["TYHIS", "VALIK", "JAOSK"]:
        if conf.has_key(right):
            add_right(rr, right, conf[right])
    if conf.has_key("ALL"):
        add_right(rr, "TYHIS", conf["ALL"])
        add_right(rr, "VALIK", conf["ALL"])
        add_right(rr, "JAOSK", conf["ALL"])


def read_config(lines):
    tmp = {}
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split(':', 1)
            if key in tmp:
                raise Exception('Error: Key (%s) already in config' % key)
            tmp[key] = value.strip()

    ret_gen = {}
    for key in required:
        if not key in tmp:
            raise Exception('Required key (%s) missing' % key)
        ret_gen[key] = tmp[key]
        del tmp[key]

    elections = ret_gen['*.elections'].split()

    ret_el = {}
    for el in elections:
        ret_el[el] = {}
        for key in election_required:
            elkey = "%s.%s" % (el, key)
            if not elkey in tmp:
                raise Exception('Required key (%s) missing' % elkey)
            ret_el[el][key] = tmp[elkey]
            del tmp[elkey]

        for key in election_optional:
            elkey = "%s.%s" % (el, key)
            if elkey in tmp:
                ret_el[el][key] = tmp[elkey]
                del tmp[elkey]

    if len(tmp.keys()) > 0:
        raise Exception('Unknown keys (%s)' % tmp.keys())

    return ret_gen, ret_el




class ElectionInstaller:


    def __init__(self):
        self.__dir = None
        self.__deldir = None
        self.__bdoc = None


    def __del__(self):
        if self.__deldir:
            shutil.rmtree(self.__deldir)


    def set_dir(self, ndir):
        if not ndir == None:
            self.__dir = ndir
        else:
            self.__dir = tempfile.mkdtemp()
            self.__deldir = self.__dir


    def process_bdoc(self, bdocfile):
        config = bdocpythonutils.BDocConfig()
        config.load(Election().get_bdoc_conf())
        self.__bdoc = bdocpythonutils.BDocContainer()
        self.__bdoc.load(bdocfile)
        profile = bdocpythonutils.ManifestProfile('TM', \
                'application/octet-stream')
        self.__bdoc.validate(profile)

        if len(self.__bdoc.signatures) != 1:
            return False, "BDoc sisaldab rohkem kui ühte allkirja"

        verifier = bdocpython.BDocVerifier()
        config.populate(verifier)

        for el in self.__bdoc.documents:
            verifier.setDocument(self.__bdoc.documents[el], el)

        _, sig_content = self.__bdoc.signatures.popitem()

        res = verifier.verifyTMOffline(sig_content)

        if res.result:
            return True, res.subject
        return False, res.error


    def print_contents(self):
        for el in self.__bdoc.documents:
            print el


    def extract(self):
        for el in self.__bdoc.documents:
            ff = open("%s/%s" % (self.__dir, el), "wb")
            ff.write(self.__bdoc.documents[el])
            ff.close()


    def setup(self):
        g_config = None
        e_config = None

        configfile = open("%s/config" % self.__dir, "r")
        g_config, e_config = read_config(configfile.readlines())
        configfile.close()

        if Election().is_hes():
            Election().set_hts_ip(g_config['*.hts'])
            Election().set_hts_path("/hts.cgi")
            Election().set_hts_verify_path("/hts-verify-vote.cgi")
            Election().config_hth_done()
            Election().set_mid_conf(
                    g_config["*.mobidurl"], \
                    g_config["*.mobidservice"], \
                    g_config["*.mobidauthmsg"], \
                    g_config["*.mobidsignmsg"])

            for el in e_config:
                init_conf.execute(el, e_config[el]['type'], \
                        e_config[el]['description'])

                manage_rights(el, e_config[el])
                config_common.config_hes(el, \
                        "%s/%s" % (self.__dir, e_config[el]['districts']), \
                        "%s/%s" % (self.__dir, e_config[el]['voters']), \
                        "%s/%s" % (self.__dir, e_config[el]['choices']))

        if Election().is_hts():
            Election().set_verification_time(g_config["*.verifytimeout"])
            Election().set_verification_count(g_config["*.verifymaxtries"])

            for el in e_config:
                init_conf.execute(el, e_config[el]['type'], \
                        e_config[el]['description'])

                manage_rights(el, e_config[el])
                config_common.config_hts(el, \
                        "%s/%s" % (self.__dir, e_config[el]['districts']), \
                        "%s/%s" % (self.__dir, e_config[el]['voters']), \
                        "%s/%s" % (self.__dir, e_config[el]['choices']))


        if Election().is_hlr():
            for el in e_config:
                init_conf.execute(el, e_config[el]['type'], \
                        e_config[el]['description'])

                manage_rights(el, e_config[el])
                config_common.config_hlr(el, \
                        "%s/%s" % (self.__dir, e_config[el]['districts']), \
                        "%s/%s" % (self.__dir, e_config[el]['choices']))



def usage():
    print "Invalid arguments"
    print "%s verify <bdoc>" % sys.argv[0]
    print "%s install <bdoc>" % sys.argv[0]


if __name__ == "__main__":

    bdocpython.initialize()
    if len(sys.argv) != 3:
        usage()

    typ = sys.argv[1]
    if not typ in ['install', 'verify']:
        usage()
        sys.exit(1)

    inst = ElectionInstaller()
    ret = 1

    if typ == 'verify':
        res, name = inst.process_bdoc(sys.argv[2])
        if res:
            ret = 0
            print 'Allkiri korrektne'
            inst.print_contents()
            print 'Allkirjastaja: %s' % name
    else:
        inst.set_dir(None)
        res, name = inst.process_bdoc(sys.argv[2])
        if res:
            inst.extract()
            inst.setup()

    del inst
    bdocpython.terminate()
    sys.exit(ret)


# vim:set ts=4 sw=4 et fileencoding=utf8:
