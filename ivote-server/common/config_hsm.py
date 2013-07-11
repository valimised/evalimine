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
import exception_msg
from election import Election

NOT_DEFINED_STR = "pole määratud"

#pylint: disable-msg=W0702


def get_hsm():

    try:
        hsm_token_name = Election().get_hsm_token_name()
    except:
        hsm_token_name = NOT_DEFINED_STR

    try:
        hsm_priv_key = Election().get_hsm_priv_key()
    except:
        hsm_priv_key = NOT_DEFINED_STR

    try:
        pkcs11_path = Election().get_pkcs11_path()
    except:
        pkcs11_path = NOT_DEFINED_STR

    print "Token'i nimi: %s" % hsm_token_name
    print "Privaatvõtme nimi: %s" % hsm_priv_key
    print "PKCS11 teegi asukoht: %s" % pkcs11_path


def set_hsm(token_name, priv_key, pkcs11_path):

    try:
        Election().set_hsm_token_name(token_name)
        Election().set_hsm_priv_key(priv_key)
        Election().set_pkcs11_path(pkcs11_path)
        Election().config_hsm_done()
    except:
        Election().config_hsm_done(False)
        sys.stderr.write("HSMi konfigureerimine nurjus: %s\n"
            % exception_msg.trace())
        sys.exit(1)


def usage():
    print 'Kasutamine: ' + sys.argv[0] + \
        ' get|(set <tokenname> <privkeylabel> <pkcs11 path>)'
    sys.exit(1)


def main_function():
    if (len(sys.argv) != 2) and (len(sys.argv) != 5):
        usage()

    if (len(sys.argv) == 2) and (sys.argv[1] != 'get'):
        usage()

    if (len(sys.argv) == 5) and (sys.argv[1] != 'set'):
        usage()

    cmd = sys.argv[1]

    if cmd == 'get' or cmd == 'set':
        if cmd == 'get':
            get_hsm()
        else:
            set_hsm(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print 'Operatsioon ei ole teostatav'
        sys.exit(1)


if __name__ == '__main__':
    main_function()


# vim:set ts=4 sw=4 et fileencoding=utf8:
