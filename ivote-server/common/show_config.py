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

import sys
import exception_msg
from election import Election

NOT_DEFINED_STR = "Pole määratud"

def usage():
    print 'Kasutamine: ' + sys.argv[0]
    sys.exit(1)


def display_mid_conf():
     try:
         url = Election().get_mid_url()
     except:
         url = NOT_DEFINED_STR

     try:
         name = Election().get_mid_name()
     except:
         name = NOT_DEFINED_STR

     try:
         auth_msg, sign_msg = Election().get_mid_messages()
     except:
         auth_msg = NOT_DEFINED_STR
         sign_msg = NOT_DEFINED_STR

     print "\t\tDigiDocService URL: %s" % url
     print "\t\tTeenuse nimi: %s" % name
     print "\t\tTeade autentimisel: %s" % auth_msg
     print "\t\tTeade signeerimisel: %s" % sign_msg


def display_hth_conf():
    try:
        hts_ip = Election().get_hts_ip()
    except:
        hts_ip = NOT_DEFINED_STR

    try:
        hts_path = Election().get_hts_path()
    except:
        hts_path = NOT_DEFINED_STR

    try:
        hts_verify = Election().get_hts_verify_path()
    except:
        hts_verify = NOT_DEFINED_STR

    print "\t\tHTSi IP aadress: %s" % hts_ip
    print "\t\tHTSi URL: %s" % hts_path
    print "\t\tHTSi hääle kontrolli URL: %s" % hts_verify


def display_session_conf():
    try:
        sess_len = Election().get_session_length()
    except:
        sess_len = NOT_DEFINED_STR

    print "\t\tValimisseansi kehtivusaeg minutites: %s" % sess_len


def display_verification_conf():
     try:
         def_time = Election().get_verification_time()
     except:
         def_time = NOT_DEFINED_STR

     try:
         def_count = Election().get_verification_count()
     except:
         def_count = NOT_DEFINED_STR

     print "\t\tTaimaut hääle kontrollimiseks minutites: %s" % def_time
     print "\t\tLubatud arv kordusi hääle kontrollimiseks: %s" % def_count





if __name__ == '__main__':
    if len(sys.argv) != 1:
        usage()

    try:


         print 'Laaditud konfiguratsiooniandmed:'
         if Election().count_questions() != 0:
             print '\tValimisidentifikaator(id) - olemas'
         else:
             print '\tValimisidentifikaator(id) - puudu'

         for elid in Election().get_questions():
             if Election().is_hes():
                 if Election().is_config_server_elid_done(elid):
                     print '\t\t"%s" jaosk., valik., häälet. failid - olemas' % elid
                 else:
                     print '\t\t"%s" jaosk., valik., häälet. failid - puudu' % elid
             elif Election().is_hts():
                 if Election().is_config_server_elid_done(elid):
                     print '\t\t"%s" jaosk., valik., häälet. failid - olemas' % elid
                 else:
                     print '\t\t"%s" jaosk., valik., häälet. failid - puudu' % elid
             elif Election().is_hlr():
                 if Election().is_config_server_elid_done(elid):
                     print '\t\t"%s" jaosk., valik. failid - olemas' % elid
                 else:
                     print '\t\t"%s" jaosk., valik. failid - puudu' % elid

         if Election().is_config_bdoc_done():
             print '\tSertifikaadid - olemas'
         else:
             print '\tSertifikaadid - puudu'

         if Election().is_hes():
             if Election().is_config_hth_done():
                 print '\tHTSi konfiguratsioon - olemas'
                 display_hth_conf()
             else:
                 print '\tHTSi konfiguratsioon - puudu'
             if Election().is_config_mid_done():
                 print '\tMobiil-ID konfiguratsioon - olemas'
                 display_mid_conf()
             else:
                 print '\tMobiil-ID konfiguratsioon - puudu'
             if Election().is_config_session_done():
                 print '\tSeansi konfiguratsioon - olemas'
                 display_session_conf()
             else:
                 print '\tSeansi konfiguratsioon - puudu'

         if Election().is_hts():
             if Election().is_config_verification_done():
                 print '\tKontrollitavuse konfiguratsioon - olemas'
                 display_verification_conf()
             else:
                 print '\tKontrollitavuse konfiguratsioon - puudu'

         if Election().is_hlr():
             if Election().is_config_hsm_done():
                 print '\tHSMi konfiguratsioon - olemas'
             else:
                 print '\tHSMi konfiguratsioon - puudu'
             for elid in Election().get_questions():
                 if Election().is_config_hlr_input_elid_done(elid):
                     print '\t"%s" imporditud häälte fail - olemas' % elid
                 else:
                     print '\t"%s" imporditud häälte fail - puudu' % elid



    except:
        sys.stderr.write("Sätete kuvamine nurjus: %s\n"
            % exception_msg.trace())
        sys.exit(1)


# vim:set ts=4 sw=4 et fileencoding=utf8:
