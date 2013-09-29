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

from election import ElectionState
from election import Election
import os
import uiutil
import regrights
import burner
import evcommon

SCRIPT_CONFIG_HTH = "config_hth.py"
SCRIPT_CONFIG_HSM = "config_hsm.py"
SCRIPT_CHECK_CONSISTENCY = "check_consistency.py"
SCRIPT_VOTERS_FILE_HISTORY = "show_voters_files_history.py"
SCRIPT_REGRIGHTS = "regrights.py"
SCRIPT_HTS = "htsdisp.py"
SCRIPT_INIT_CONF = "init_conf.py"
SCRIPT_CONFIG_SRV = "config_common.py"
SCRIPT_INSTALL_SRV = "installer.py"
SCRIPT_CONFIG_DIGIDOC = "config_bdoc.py"
SCRIPT_APPLY_CHANGES = "apply_changes.py"
SCRIPT_REPLACE_CANDIDATES = "replace_candidates.py"
SCRIPT_CONFIG_HLR_INPUT = "config_hlr_input.py"
SCRIPT_HTSALL = "htsalldisp.py"
SCRIPT_HLR = "hlr.py"

PROGRAM_LESS = "less -fC"
PROGRAM_LS = "ls -1Xla"

# pylint: disable-msg=W0702

def do_voters_file_history():
    cmd = '%s' % (SCRIPT_VOTERS_FILE_HISTORY)
    os.system(cmd)

def do_dir_list():
    dir_name = uiutil.ask_string("Sisesta kataloog")
    if os.path.isdir(dir_name):
        cmd = "%s %s | %s" % (PROGRAM_LS, dir_name, PROGRAM_LESS)
        os.system(cmd)
    else:
        print "\"%s\" ei ole kataloog" % dir_name

def do_import_error_strings():
    import evmessage
    evstrings_file = uiutil.ask_file_name("Sisesta teadete-faili asukoht")
    evm = evmessage.EvMessage()
    evm.import_str_file(evstrings_file)

def do_check_consistency():
    cmd = "%s" % SCRIPT_CHECK_CONSISTENCY
    os.system(cmd)

def do_get_mid_conf():

    try:
        url = Election().get_mid_url()
    except:
        url = uiutil.NOT_DEFINED_STR

    try:
        name = Election().get_mid_name()
    except:
        name = uiutil.NOT_DEFINED_STR

    try:
        auth_msg, sign_msg = Election().get_mid_messages()
    except:
        auth_msg = uiutil.NOT_DEFINED_STR
        sign_msg = uiutil.NOT_DEFINED_STR

    print "DigiDocService URL: %s" % url
    print "Teenuse nimi: %s" % name
    print "Teade autentimisel: %s" % auth_msg
    print "Teade signeerimisel: %s" % sign_msg

def do_set_mid_conf():

    try:
        def_url = Election().get_mid_url()
    except:
        def_url = 'https://www.openxades.org:8443/DigiDocService'

    try:
        def_name = Election().get_mid_name()
    except:
        def_name = 'Testimine'

    try:
        def_auth_msg, def_sign_msg = Election().get_mid_messages()
    except:
        def_auth_msg = 'E-hääletus, autentimine'
        def_sign_msg = 'E-hääletus, hääle allkirjastamine'

    url = uiutil.ask_string(\
                "Sisesta DigiDocService'i URL", None, None, def_url)

    name = uiutil.ask_string(\
                "Sisesta teenuse nimi", None, None, def_name)

    auth_msg = uiutil.ask_string(\
                "Sisesta sõnum autentimisel", None, None, def_auth_msg)

    sign_msg = uiutil.ask_string(\
                "Sisesta sõnum allkirjastamisel", None, None, def_sign_msg)

    Election().set_mid_conf(url, name, auth_msg, sign_msg)

def do_get_hsm_conf():
    cmd = "%s get" % SCRIPT_CONFIG_HSM
    os.system(cmd)

def do_set_hsm_conf():

    reg = Election().get_root_reg()

    if reg.check(['common', 'hsm', 'tokenname']):
        try:
            def_tokenname = \
                reg.read_string_value(['common', 'hsm'], 'tokenname').value
        except:
            def_tokenname = "evote"
    else:
        def_tokenname = "evote"

    token_name = uiutil.ask_string(\
                "Sisesta HSM'i partitsiooni nimi", None, None, def_tokenname)

    if reg.check(['common', 'hsm', 'privkeylabel']):
        try:
            def_privkeylabel = \
                reg.read_string_value(['common', 'hsm'], 'privkeylabel').value
        except:
            def_privkeylabel = "evote_key"
    else:
        def_privkeylabel = "evote_key"

    priv_key_label = uiutil.ask_string(\
                    "Sisesta privaatvõtme nimi", None, None, def_privkeylabel)

    if reg.check(['common', 'hsm', 'pkcs11']):
        try:
            def_pkcs11 = \
                reg.read_string_value(['common', 'hsm'], 'pkcs11').value
        except:
            def_pkcs11 = "/usr/lunasa/lib/libCryptoki2_64.so"
    else:
        def_pkcs11 = "/usr/lunasa/lib/libCryptoki2_64.so"

    pkcs11_path = uiutil.ask_file_name(\
                    "Sisesta PKCS11 teegi asukoht", def_pkcs11)

    cmd = "%s set %s %s %s" % \
                (SCRIPT_CONFIG_HSM, token_name, priv_key_label, pkcs11_path)
    os.system(cmd)

def do_set_hts_conf():

    reg = Election().get_root_reg()
    if reg.check(['common', 'htsip']):
        try:
            def_ip_port = reg.read_ipaddr_value(\
                                        ['common'], 'htsip').value.split(":")
            def_ip = def_ip_port[0]
            if len(def_ip_port) > 1:
                try:
                    def_port = int(def_ip_port[-1])
                except ValueError:
                    def_port = 80
            else:
                def_port = 80
        except:
            def_ip = None
            def_port = 80
    else:
        def_ip = None
        def_port = 80

    hts_ip = uiutil.ask_string("Sisesta HTSi IP aadress", None, None, def_ip)
    hts_port = uiutil.ask_int("Sisesta HTSi port", def_port, 0, 65535)

    try:
        def_url = Election().get_hts_path()
    except:
        def_url = "/hts.cgi"
    hts_url = uiutil.ask_string("Sisesta HTSi URL", None, None, def_url)

    try:
        def_verify = Election().get_hts_verify_path()
    except:
        def_verify = "/hts-verify-vote.cgi"
    hts_verify = uiutil.ask_string("Sisesta HTSi hääle kontrolli URL", \
            None, None, def_verify)

    cmd = "%s set %s:%d %s %s" % (SCRIPT_CONFIG_HTH, hts_ip, hts_port, \
            hts_url, hts_verify)
    os.system(cmd)

def do_get_hts_conf():
    cmd = "%s get" % SCRIPT_CONFIG_HTH
    os.system(cmd)


def do_add_rights(elid):
    ik = uiutil.ask_id_num()
    right_str_list = []
    if Election().is_hes() or Election().is_hlr():
        right = uiutil.ask_int("Võimalikud volitused:\n " + \
            "\t(1) %s\n" % regrights.G_DESCS["VALIK"] + \
            "\t(2) %s\n" % regrights.G_DESCS["JAOSK"] + \
            "\t(3) Kõik volitused\n" + \
            "Vali volitus:", 3, 1, 3)
        if right == 1:
            right_str_list.append("VALIK")
        elif right == 2:
            right_str_list.append("JAOSK")
        elif right == 3:
            right_str_list.append("VALIK")
            right_str_list.append("JAOSK")
    elif Election().is_hts():
        right = uiutil.ask_int("Võimalikud volitused:\n " + \
            "\t(1) %s\n" % regrights.G_DESCS["TYHIS"] + \
            "\t(2) %s\n" % regrights.G_DESCS["JAOSK"] + \
            "\t(3) %s\n" % regrights.G_DESCS["VALIK"] + \
            "\t(4) Kõik volitused\n" + \
            "Vali volitus:", 4, 1, 4)
        if right == 1:
            right_str_list.append("TYHIS")
        elif right == 2:
            right_str_list.append("JAOSK")
        elif right == 3:
            right_str_list.append("VALIK")
        elif right == 4:
            right_str_list.append("TYHIS")
            right_str_list.append("JAOSK")
            right_str_list.append("VALIK")

    for i in right_str_list:
        cmd = "%s %s add %s %s" % (SCRIPT_REGRIGHTS, elid, ik, i)
        os.system(cmd)

def do_add_description(elid):
    ik = uiutil.ask_id_num()
    desc = uiutil.ask_string("Sisesta kirjeldus")
    cmd = "%s %s desc %s %s" % (SCRIPT_REGRIGHTS, elid, ik, desc)
    os.system(cmd)

def do_rem_rights(elid):
    ik = uiutil.ask_id_num()
    right_str = ""
    if Election().is_hes() or Election().is_hlr():
        right = uiutil.ask_int("Võimalikud volitused:\n " + \
            "\t(1) Valikute nimekirja laadija\n" + \
            "\t(2) Valimisjaoskondade nimekirja laadija\n" + \
            "Vali volitus:", 1, 1, 2)
        if right == 1:
            right_str = "VALIK"
        elif right == 2:
            right_str = "JAOSK"
    elif Election().is_hts():
        right = uiutil.ask_int("Võimalikud volitused:\n " + \
                "\t(1) Tühistus- ja ennistusnimekirja laadija\n" +
                "\t(2) Valimisjaoskondade nimekirja laadija\n" + \
                "Vali volitus:", 1, 1, 2)
        if right == 1:
            right_str = "TYHIS"
        elif right == 2:
            right_str = "JAOSK"
    if not uiutil.ask_yes_no("Kas oled kindel"):
        return
    cmd = "%s %s rem %s %s" % (SCRIPT_REGRIGHTS, elid, ik, right_str)
    os.system(cmd)

def do_rem_user_rights(elid):
    ik = uiutil.ask_id_num()
    if not uiutil.ask_yes_no("Kas oled kindel"):
        return
    cmd = "%s %s remuser %s" % (SCRIPT_REGRIGHTS, elid, ik)
    os.system(cmd)

def do_rem_all_rights(elid):
    if not uiutil.ask_yes_no("Kas oled kindel"):
        return
    cmd = "%s %s remall" % (SCRIPT_REGRIGHTS, elid)
    os.system(cmd)

def do_list_user_rights(elid):
    ik = uiutil.ask_id_num()
    cmd = "%s %s listuser %s" % (SCRIPT_REGRIGHTS, elid, ik)
    os.system(cmd)

def do_list_all_rights(elid):
    cmd = "%s %s listall" % (SCRIPT_REGRIGHTS, elid)
    os.system(cmd)

def do_check_configure():

    # pylint: disable-msg=R0912

    print 'Laetud konfiguratsiooniandmed:'
    if Election().count_questions() != 0:
        print '\tValimisidentifikaator(id) - olemas'
    else:
        print '\tValimisidentifikaator(id) - puudu'

    for elid in Election().get_questions():
        if Election().is_hes():
            if Election().is_config_server_elid_done(elid):
                print '\t"%s" jaosk., valik., häälet. failid - olemas' % elid
            else:
                print '\t"%s" jaosk., valik., häälet. failid - puudu' % elid
        elif Election().is_hts():
            if Election().is_config_server_elid_done(elid):
                print '\t"%s" jaosk., häälet. failid - olemas' % elid
            else:
                print '\t"%s" jaosk., häälet. failid - puudu' % elid
        elif Election().is_hlr():
            if Election().is_config_server_elid_done(elid):
                print '\t"%s" jaosk., valik. failid - olemas' % elid
            else:
                print '\t"%s" jaosk., valik. failid - puudu' % elid

    if Election().is_config_bdoc_done():
        print '\tSertifikaadid - olemas'
    else:
        print '\tSertifikaadid - puudu'

    if Election().is_hes():
        if Election().is_config_hth_done():
            print '\tHTSi konfiguratsioon - olemas'
        else:
            print '\tHTSi konfiguratsioon - puudu'
        if Election().is_config_mid_done():
            print '\tMobiil-ID konfiguratsioon - olemas'
        else:
            print '\tMobiil-ID konfiguratsioon - puudu'

    if Election().is_hts():
        if Election().is_config_verification_done():
            print '\tKontrollitavuse konfiguratsioon - olemas'
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

def do_pre_start_counting_hes():
    if not uiutil.ask_yes_no("Kas oled kindel"):
        return
    Election().refuse_new_voters()
    print 'Kandidaatide nimekirjade väljastamine peatatud'

def do_backup():
    """Varundame olekupuu DVD-le.
    """
    import time

    print "Varundame olekupuu. Palun oota.."
    s_time = time.time()
    cd_burner = burner.DiskBurner(evcommon.burn_buff())

    try:
        if cd_burner.backup_dir(Election().get_root_reg().root, \
                (Election().is_hes() or Election().is_hts())):

            print 'Varundamise ettevalmistamine kestis : %s' % \
                    time.strftime("%H:%M:%S", \
                    time.gmtime(long(time.time() - s_time)))
            cd_burner.burn()
    finally:
        cd_burner.delete_files()
        print '\nVarundamine kestis kokku: %s' % time.strftime("%H:%M:%S", \
                time.gmtime(long(time.time() - s_time)))

def do_revoke(elid):
    revokef = uiutil.ask_file_name_from_cd(\
            "Sisesta tühistus-/ennistusnimekirja-faili asukoht")
    cmd = "%s %s %s %s" % (SCRIPT_HTS, elid, "tyhista_ennista", revokef)
    os.system(cmd)

def do_new_election():
    elid = uiutil.ask_election_id(Election().get_questions())
    eltype = uiutil.ask_int("Võimalikud valimiste tüübid:\n " + \
            "\t(0) %s\n" % evcommon.G_TYPES[0] + \
            "\t(1) %s\n" % evcommon.G_TYPES[1] + \
            "\t(2) %s\n" % evcommon.G_TYPES[2] + \
            "\t(3) %s\n" % evcommon.G_TYPES[3] + \
            "Sisesta valimiste tüüp:", 0, 0, 3)

    if Election().is_hts():
        description = uiutil.ask_string("Sisesta valimiste kirjeldus", ".+", \
            "Valimiste kirjeldus peab sisaldama vähemalt ühte sümbolit")
    else:
        description = elid
    cmd = '%s %s %d "%s"' % (SCRIPT_INIT_CONF, elid, eltype, description)
    os.system(cmd)

def restart_apache():
    import subprocess

    prompt = "Palun sisestage veebiserveri taaskäivitamiseks parool: "
    retcode = subprocess.call(\
            ["sudo", "-p", prompt, "service", "apache2", "restart"])
    if retcode == 0:
        print "Veebiserver edukalt taaskäivitatud"
    elif retcode == 1:
        print "Probleem taaskäivitamisel, vale parool?"
    else:
        print "Probleem taaskäivitamisel, vea kood on ", retcode

def do_bdoc_conf_hes():
    do_bdoc_conf()
    restart_apache()

def do_bdoc_conf():
    bdoc_conf = uiutil.ask_dir_name(\
        "Sisesta sertifikaatide konfiguratsioonipuu asukoht")
    cmd = "%s %s" % (SCRIPT_CONFIG_DIGIDOC, bdoc_conf)
    os.system(cmd)

def do_enable_voters_list():
    Election().toggle_check_voters_list(True)
    print "Hääletajate nimekirja kontroll lubatud\n"

def do_disable_voters_list():
    Election().toggle_check_voters_list(False)
    print "Hääletajate nimekirja kontroll keelatud\n"

def do_install():

    install_file = \
        uiutil.ask_file_name_from_cd("Sisesta paigaldusfaili asukoht")

    cmd = "%s verify %s" % (SCRIPT_INSTALL_SRV, install_file)
    ret = os.system(cmd)

    if not ret == 0:
        return

    if not uiutil.ask_yes_no("Kas paigaldame valimised?"):
        return

    cmd = "%s install %s" % (SCRIPT_INSTALL_SRV, install_file)
    os.system(cmd)

def do_hlr_conf(elid):
    station_file = \
        uiutil.ask_file_name_from_cd("Sisesta jaoskondade-faili asukoht")
    choices_file = \
        uiutil.ask_file_name_from_cd("Sisesta valikute-faili asukoht")
    cmd = "%s %s %s %s %s" % (SCRIPT_CONFIG_SRV, evcommon.APPTYPE_HLR, \
                            elid, station_file, choices_file)
    os.system(cmd)

def do_import_votes(elid):
    votes_file = \
            uiutil.ask_file_name_from_cd("Sisesta häälte-faili asukoht")
    cmd = "%s %s %s" % (SCRIPT_CONFIG_HLR_INPUT, elid, votes_file)
    os.system(cmd)

def do_hes_conf(elid):
    station_file = \
        uiutil.ask_file_name_from_cd("Sisesta jaoskondade-faili asukoht")
    choices_file = \
        uiutil.ask_file_name_from_cd("Sisesta valikute-faili asukoht")
    elector_file = \
        uiutil.ask_file_name_from_cd("Sisesta valijate-faili asukoht")
    cmd = "%s %s %s %s %s %s" % (SCRIPT_CONFIG_SRV, evcommon.APPTYPE_HES, \
            elid, station_file, elector_file, choices_file)
    os.system(cmd)

def do_hts_conf(elid):
    station_file = \
        uiutil.ask_file_name_from_cd("Sisesta jaoskondade-faili asukoht")
    choices_file = \
        uiutil.ask_file_name_from_cd("Sisesta valikute-faili asukoht")
    elector_file = \
        uiutil.ask_file_name_from_cd("Sisesta valijate-faili asukoht")
    cmd = "%s %s %s %s %s %s" % (SCRIPT_CONFIG_SRV, evcommon.APPTYPE_HTS, \
                            elid, station_file, elector_file, choices_file)
    os.system(cmd)

def do_load_electors(elid):
    elec_f = uiutil.ask_file_name_from_cd("Sisesta valijate-faili asukoht")
    cmd = "%s %s %s" % (SCRIPT_APPLY_CHANGES, elid, elec_f)
    os.system(cmd)

def do_replace_candidates(elid):
    if not uiutil.ask_yes_no("Kas oled kindel"):
        return
    if not uiutil.ask_yes_no("Valikute nimekirja väljavahetamisel " + \
            "kustutakse eelmine nimekiri.\nKas jätkan"):
        return
    elec_f = uiutil.ask_file_name_from_cd("Sisesta valikute-faili asukoht")
    cmd = "%s %s %s" % (SCRIPT_REPLACE_CANDIDATES, elid, elec_f)
    os.system(cmd)

def do_view_election_description(elid):
    el_reg = Election().get_sub_reg(elid)
    try:
        description = \
                el_reg.read_string_value(['common'], 'description').value
    except IOError:
        description = uiutil.NOT_DEFINED_STR
    except LookupError:
        description = uiutil.NOT_DEFINED_STR
    print "Valimiste %s kirjeldus: %s\n" % (elid, description)

def do_create_status_report():
    print "Palun oota, genereerin aruannet.."
    cmd = "%s status" % SCRIPT_HTSALL
    os.system(cmd)

def do_create_status_report_no_verify():

    # pylint: disable-msg=C0103

    print "Palun oota, genereerin aruannet..."
    cmd = "%s statusnoverify" % SCRIPT_HTSALL
    os.system(cmd)

def do_count_votes(elid):
    import evfiles
    import evlog

    log4 = evlog.Logger()
    log4.set_logs(evfiles.log4_file(elid).path())
    if log4.lines_in_file() > 3:
        print "Log4 fail ei ole tühi. Ei saa jätkata."
        return

    log5 = evlog.Logger()
    log5.set_logs(evfiles.log5_file(elid).path())
    if log5.lines_in_file() > 3:
        print "Log5 fail ei ole tühi. Ei saa jätkata."
        return

    if not uiutil.ask_yes_no("Kas oled kindel"):
        print "Katkestame häälte lugemise"
        return
    pin = uiutil.ask_password("Sisesta partitsiooni PIN: ", \
            "Sisestatud PIN oli tühi!")
    cmd = "%s %s %s" % (SCRIPT_HLR, elid, pin)
    os.system(cmd)

def do_del_election():
    elid = uiutil.ask_del_election_id(Election().get_questions())
    Election().delete_question(elid)

def do_restore_init_status():
    if not uiutil.ask_yes_no("Kas oled kindel"):
        return

    if not uiutil.ask_yes_no("Initsialiseerimisel kustutatakse " + \
        "antud hääled.\nKas jätkan"):
        return

    Election().restore_init_status()
    ElectionState().init()

def do_restore():
    """Taastame olekupuu varukoopiast.
    """

    if not uiutil.ask_yes_no("Kas oled kindel"):
        return
    if not uiutil.ask_yes_no("Olekupuu taastamisel varukoopiast " + \
            "kustutatakse vana olekupuu.\nKas jätkan"):
        return

    import time
    s_time = time.time()

    try:
        restorer = burner.Restorer(os.path.abspath(\
                os.path.join(evcommon.EVREG_CONFIG,\
                '..', 'restore-' + time.strftime("%Y%m%d%H%M%S"))))

        while 1:
            backup_dir = uiutil.ask_dir_name(\
                    "Sisesta kataloog, kus asuvad varukoopia failid")
            restorer.add_chunks(backup_dir)

            if not uiutil.ask_yes_no(\
                    "Kas soovid veel laadida varukoopia faile"):
                break

        if restorer.chunk_count() != 0:
            print "Taastame olekupuu varukoopiast. Palun oota.."
            restorer.restore(Election().get_root_reg().root)
        else:
            print 'Pole ühtegi varukoopia faili. Loobun taastamisest.'
    finally:
        print 'Kustutan ajutisi faile. Palun oota..'
        restorer.delete_files()

        if restorer.chunk_count() != 0:
            print '\nOlekupuu taastamine kestis: %s' % \
                    time.strftime("%H:%M:%S", \
                    time.gmtime(long(time.time() - s_time)))

def do_change_election_description(elid):
    description = uiutil.ask_string("Sisesta valimiste kirjeldus")
    el_reg = Election().get_sub_reg(elid)
    el_reg.create_string_value(['common'], 'description', description)

def do_view_status_report():
    import evfiles
    report_file = evfiles.statusreport_file().path()
    cmd = "%s %s" % (PROGRAM_LESS, report_file)
    os.system(cmd)

def do_verification_conf():
    try:
        def_time = Election().get_verification_time()
    except (IOError, LookupError):
        def_time = 30

    try:
        def_count = Election().get_verification_count()
    except (IOError, LookupError):
        def_count = 3

    verif_time = uiutil.ask_int("Sisesta taimaut hääle kontrollimiseks minutites", \
            def_time, 1)
    verif_count = uiutil.ask_int("Sisesta lubatud arv kordusi hääle kontrollimiseks", \
            def_count, 1)

    Election().set_verification_time(verif_time)
    Election().set_verification_count(verif_count)


def do_get_verification_conf():
    try:
        def_time = Election().get_verification_time()
    except (IOError, LookupError):
        def_time = "puudub"

    try:
        def_count = Election().get_verification_count()
    except (IOError, LookupError):
        def_count = "puudub"

    print "Taimaut hääle kontrollimiseks minutites: %s" % def_time
    print "Lubatud arv kordusi hääle kontrollimiseks: %s" % def_count



# vim:set ts=4 sw=4 et fileencoding=utf8:
