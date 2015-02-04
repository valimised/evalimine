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

from election import ElectionState
from election import Election
import os
import uiutil
import regrights
import burner
import evcommon
import autocmd
import subprocess
import sigverify

SCRIPT_CONFIG_HTH = "config_hth.py"
SCRIPT_CONFIG_HSM = "config_hsm.py"
SCRIPT_CHECK_CONSISTENCY = "check_consistency.py"
SCRIPT_CONFIG_FILES_HISTORY = "show_config_files_history.py"
SCRIPT_REGRIGHTS = "regrights.py"
SCRIPT_HTS = "load_rev_files.py"
SCRIPT_INIT_CONF = "init_conf.py"
SCRIPT_CONFIG_SRV = "config_common.py"
SCRIPT_INSTALL_SRV = "installer.py"
SCRIPT_CONFIG_DIGIDOC = "config_bdoc.py"
SCRIPT_APPLY_CHANGES = "apply_changes.py"
SCRIPT_CONFIG_HLR_INPUT = "config_hlr_input.py"
SCRIPT_HTSALL = "htsalldisp.py"
SCRIPT_HLR = "hlr.py"
SCRIPT_SHOW_CONFIG = "show_config.py"

PROGRAM_LESS = "less"
PROGRAM_LESS_ARGS = "-fC"
PROGRAM_LS = "ls"
PROGRAM_LS_ARGS = "-1Xla"

# pylint: disable-msg=W0702


def do_config_files_history():
    subprocess.call(SCRIPT_CONFIG_FILES_HISTORY)


def do_dir_list():
    dir_name = uiutil.ask_string("Sisesta kataloog")
    if os.path.isdir(dir_name):
        ls = subprocess.Popen([PROGRAM_LS, PROGRAM_LS_ARGS, dir_name],
                              stdout=subprocess.PIPE)
        less = subprocess.Popen([PROGRAM_LESS, PROGRAM_LESS_ARGS],
                                stdin=ls.stdout)
        less.communicate()
        ls.stdout.close()
    else:
        print "\"%s\" ei ole kataloog" % dir_name


def do_import_error_strings():
    import evmessage
    evstrings_file = uiutil.ask_file_name("Sisesta teadete-faili asukoht")
    evm = evmessage.EvMessage()
    evm.import_str_file(evstrings_file)


def do_check_consistency():
    subprocess.call(SCRIPT_CHECK_CONSISTENCY)


def do_set_voter_public_key(elid):
    key_path = uiutil.ask_string("Sisesta avaliku võtme asukoht")
    if os.path.isfile(key_path):
        if sigverify.check_sig_file(key_path):
            Election().copy_voter_public_key_file(elid, key_path)
            print "Võti lisatud"
    else:
        print "\"%s\" on kaust" % key_path


def do_get_voter_public_key(elid):
    key_path = Election().get_sub_reg(elid, ['common']).path()
    key_file = open(key_path + evcommon.VOTER_PUBLIC_KEY, 'rb')
    key = key_file.read()
    key_file.close()
    print("Valijate faili signatuuri avalik võti:")
    print(key.decode('utf-8'))


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

    url = uiutil.ask_string(
        "Sisesta DigiDocService'i URL", None, None, def_url)

    name = uiutil.ask_string(
        "Sisesta teenuse nimi", None, None, def_name)

    auth_msg = uiutil.ask_string(
        "Sisesta sõnum autentimisel", None, None, def_auth_msg)

    sign_msg = uiutil.ask_string(
        "Sisesta sõnum allkirjastamisel", None, None, def_sign_msg)

    Election().set_mid_conf(url, name, auth_msg, sign_msg)


def do_get_hsm_conf():
    subprocess.call([SCRIPT_CONFIG_HSM, "get"])


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

    token_name = uiutil.ask_string(
        "Sisesta HSM'i partitsiooni nimi", None, None, def_tokenname)

    if reg.check(['common', 'hsm', 'privkeylabel']):
        try:
            def_privkeylabel = \
                reg.read_string_value(['common', 'hsm'], 'privkeylabel').value
        except:
            def_privkeylabel = "evote_key"
    else:
        def_privkeylabel = "evote_key"

    priv_key_label = uiutil.ask_string(
        "Sisesta privaatvõtme nimi", None, None, def_privkeylabel)

    if reg.check(['common', 'hsm', 'pkcs11']):
        try:
            def_pkcs11 = \
                reg.read_string_value(['common', 'hsm'], 'pkcs11').value
        except:
            def_pkcs11 = "/usr/lunasa/lib/libCryptoki2_64.so"
    else:
        def_pkcs11 = "/usr/lunasa/lib/libCryptoki2_64.so"

    pkcs11_path = uiutil.ask_file_name(
        "Sisesta PKCS11 teegi asukoht", def_pkcs11)

    subprocess.call([SCRIPT_CONFIG_HSM, "set",
                     token_name, priv_key_label, pkcs11_path])


def do_set_hts_conf():

    reg = Election().get_root_reg()
    if reg.check(['common', 'htsip']):
        try:
            def_ip_port = reg.read_ipaddr_value(
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
    hts_verify = uiutil.ask_string(
        "Sisesta HTSi hääle kontrolli URL", None, None, def_verify)

    subprocess.call([SCRIPT_CONFIG_HTH, "%s:%d" %
                     (hts_ip, hts_port), hts_url, hts_verify])


def do_add_rights(elid):
    ik = uiutil.ask_id_num()
    right_str_list = []
    if Election().is_hes() or Election().is_hlr():
        right = uiutil.ask_int(
            "Võimalikud volitused:\n " +
            "\t(1) %s\n" % regrights.G_DESCS["VALIK"] +
            "\t(2) %s\n" % regrights.G_DESCS["JAOSK"] +
            "\t(3) Kõik volitused\n" +
            "Vali volitus:", 3, 1, 3)
        if right == 1:
            right_str_list.append("VALIK")
        elif right == 2:
            right_str_list.append("JAOSK")
        elif right == 3:
            right_str_list.append("VALIK")
            right_str_list.append("JAOSK")
    elif Election().is_hts():
        right = uiutil.ask_int(
            "Võimalikud volitused:\n " +
            "\t(1) %s\n" % regrights.G_DESCS["TYHIS"] +
            "\t(2) %s\n" % regrights.G_DESCS["JAOSK"] +
            "\t(3) %s\n" % regrights.G_DESCS["VALIK"] +
            "\t(4) Kõik volitused\n" +
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
        subprocess.call([SCRIPT_REGRIGHTS, elid, "add", ik, i])


def do_add_description(elid):
    ik = uiutil.ask_id_num()
    desc = uiutil.ask_string("Sisesta kirjeldus")
    subprocess.call([SCRIPT_REGRIGHTS, elid, "desc", ik, desc])


def do_rem_rights(elid):
    ik = uiutil.ask_id_num()
    right_str = ""
    if Election().is_hes() or Election().is_hlr():
        right = uiutil.ask_int(
            "Võimalikud volitused:\n " +
            "\t(1) Valikute nimekirja laadija\n" +
            "\t(2) Valimisjaoskondade nimekirja laadija\n" +
            "Vali volitus:", 1, 1, 2)
        if right == 1:
            right_str = "VALIK"
        elif right == 2:
            right_str = "JAOSK"
    elif Election().is_hts():
        right = uiutil.ask_int(
            "Võimalikud volitused:\n " +
            "\t(1) Tühistus- ja ennistusnimekirja laadija\n" +
            "\t(2) Valimisjaoskondade nimekirja laadija\n" +
            "Vali volitus:", 1, 1, 2)
        if right == 1:
            right_str = "TYHIS"
        elif right == 2:
            right_str = "JAOSK"
    if not uiutil.ask_yes_no("Kas soovid eemaldada volituse"):
        return
    subprocess.call([SCRIPT_REGRIGHTS, elid, "rem", ik, right_str])


def do_rem_user_rights(elid):
    ik = uiutil.ask_id_num()
    if not uiutil.ask_yes_no("Kas soovid eemaldada volitatud isiku"):
        return
    subprocess.call([SCRIPT_REGRIGHTS, elid, "remuser", ik])


def do_rem_all_rights(elid):
    if not uiutil.ask_yes_no("Kas soovid eemaldada isiku kõik volitused"):
        return
    subprocess.call([SCRIPT_REGRIGHTS, elid, "remall"])


def do_list_user_rights(elid):
    ik = uiutil.ask_id_num()
    subprocess.call([SCRIPT_REGRIGHTS, elid, "listuser", ik])


def do_list_all_rights(elid):
    subprocess.call([SCRIPT_REGRIGHTS, elid, "listall"])


def do_check_configure():
    subprocess.call([SCRIPT_SHOW_CONFIG])


def do_pre_start_counting_hes():
    if not uiutil.ask_yes_no("Kas soovid peatada kandidaatide nimekirja"
                             " väljastamise"):
        return
    Election().refuse_new_voters()
    print 'Kandidaatide nimekirjade väljastamine peatatud'


def do_cancel_pre_start_counting_hes():
    if not uiutil.ask_yes_no("Kas soovid taastada kandidaatide nimekirja"
                             " väljastamise"):
        return
    Election().restore_new_voters()
    print 'Kandidaatide nimekirjade väljastamine taastatud'


def do_backup():
    """Olekupuu varundamine DVD-le.
    """
    import time

    print "Olekupuu varundamine. Palun oota.."
    s_time = time.time()
    cd_burner = burner.DiskBurner(evcommon.burn_buff())

    try:
        if cd_burner.backup_dir(
                Election().get_root_reg().root,
                (Election().is_hes() or Election().is_hts())):

            print 'Varundamise ettevalmistamine kestis : %s' % \
                  time.strftime("%H:%M:%S",
                                time.gmtime(long(time.time() - s_time)))
            cd_burner.burn()
    finally:
        cd_burner.delete_files()
        print '\nVarundamine kestis kokku: %s' %\
            time.strftime("%H:%M:%S", time.gmtime(long(time.time() - s_time)))


def do_revoke(elid):
    revokef = uiutil.ask_file_name_from_cd(
        "Sisesta tühistus-/ennistusnimekirja-faili asukoht")
    subprocess.call([SCRIPT_HTS, elid, revokef])


def do_new_election():
    elid = uiutil.ask_election_id(Election().get_questions())
    eltype = uiutil.ask_int(
        "Võimalikud valimiste tüübid:\n " +
        "\t(0) %s\n" % evcommon.G_TYPES[0] +
        "\t(1) %s\n" % evcommon.G_TYPES[1] +
        "\t(2) %s\n" % evcommon.G_TYPES[2] +
        "\t(3) %s\n" % evcommon.G_TYPES[3] +
        "Sisesta valimiste tüüp:", 0, 0, 3)

    if Election().is_hts():
        description = uiutil.ask_string(
            "Sisesta valimiste kirjeldus", ".+",
            "Valimiste kirjeldus peab sisaldama vähemalt ühte sümbolit")
    else:
        description = elid
    subprocess.call([SCRIPT_INIT_CONF, elid, str(eltype), description])


def restart_apache():
    import subprocess

    prompt = "Palun sisestage veebiserveri taaskäivitamiseks parool: "
    retcode = subprocess.call(
        ["sudo", "-p", prompt, "service", "apache2", "restart"])
    if retcode == 0:
        print "Veebiserver edukalt taaskäivitatud"
    elif retcode == 1:
        print "Probleem taaskäivitamisel, vale parool?"
    else:
        print "Probleem taaskäivitamisel, vea kood on ", retcode


def do_bdoc_conf_hes():
    if do_bdoc_conf():
        restart_apache()


def do_bdoc_conf():
    bdoc_conf = uiutil.ask_dir_name(
        "Sisesta sertifikaatide konfiguratsioonipuu asukoht")
    ret = subprocess.call([SCRIPT_CONFIG_DIGIDOC, bdoc_conf])
    return ret == 0


def do_enable_voters_list():
    Election().toggle_check_voters_list(True)
    print "Hääletajate nimekirja kontroll lubatud\n"


def do_disable_voters_list():
    Election().toggle_check_voters_list(False)
    print "Hääletajate nimekirja kontroll keelatud\n"


def do_install():

    install_file = \
        uiutil.ask_file_name_from_cd("Sisesta paigaldusfaili asukoht")

    if not subprocess.call([SCRIPT_INSTALL_SRV, "verify", install_file]) == 0:
        return

    if not uiutil.ask_yes_no("Kas paigaldame valimised?"):
        return

    subprocess.call([SCRIPT_INSTALL_SRV, "install", install_file])


def do_hlr_conf(elid):
    station_file = \
        uiutil.ask_file_name_from_cd("Sisesta jaoskondade-faili asukoht")
    choices_file = \
        uiutil.ask_file_name_from_cd("Sisesta valikute-faili asukoht")
    subprocess.call(
        [SCRIPT_CONFIG_SRV, evcommon.APPTYPE_HLR,
         elid, station_file, choices_file])


def do_import_votes(elid):
    votes_file = \
        uiutil.ask_file_name_from_cd("Sisesta häälte-faili asukoht")
    subprocess.call([SCRIPT_CONFIG_HLR_INPUT, elid, votes_file])


def do_hes_conf(elid):
    station_file = \
        uiutil.ask_file_name_from_cd("Sisesta jaoskondade-faili asukoht")
    choices_file = \
        uiutil.ask_file_name_from_cd("Sisesta valikute-faili asukoht")
    elector_file = \
        uiutil.ask_file_name_from_cd("Sisesta valijate-faili asukoht")
    elector_key_file = \
        uiutil.ask_file_name_from_cd(
            "Sisesta valijate-faili signatuuri avaliku võtme asukoht")
    subprocess.call([SCRIPT_CONFIG_SRV, evcommon.APPTYPE_HES,
                     elid, station_file, elector_file,
                     choices_file, elector_key_file])


def do_hts_conf(elid):
    station_file = \
        uiutil.ask_file_name_from_cd("Sisesta jaoskondade-faili asukoht")
    choices_file = \
        uiutil.ask_file_name_from_cd("Sisesta valikute-faili asukoht")
    elector_file = \
        uiutil.ask_file_name_from_cd("Sisesta valijate-faili asukoht")
    elector_key_file = \
        uiutil.ask_file_name_from_cd(
            "Sisesta valijate-faili signatuuri avaliku võtme asukoht")
    subprocess.call([SCRIPT_CONFIG_SRV, evcommon.APPTYPE_HTS, elid,
                     station_file, elector_file,
                     choices_file, elector_key_file])


def do_load_electors(elid):
    elec_f = uiutil.ask_file_name_from_cd("Sisesta valijate-faili asukoht")
    subprocess.call([SCRIPT_APPLY_CHANGES, elid, elec_f])


def do_view_election_description(elid):
    el_reg = Election().get_sub_reg(elid)
    try:
        description = el_reg.read_string_value(['common'], 'description').value
    except IOError:
        description = uiutil.NOT_DEFINED_STR
    except LookupError:
        description = uiutil.NOT_DEFINED_STR
    print "Valimiste %s kirjeldus: %s\n" % (elid, description)


def do_create_status_report():
    print "Palun oota, genereerin aruannet.."
    subprocess.call([SCRIPT_HTSALL, "status"])


def do_create_status_report_no_verify():

    # pylint: disable-msg=C0103

    print "Palun oota, genereerin aruannet..."
    subprocess.call([SCRIPT_HTSALL, "statusnoverify"])


def do_count_votes(elid):
    import evfiles
    import evlog

    log4 = evlog.Logger()
    log4.set_logs(evfiles.log4_file(elid).path())
    if log4.lines_in_file() > 3:
        print "Log4 fail ei ole tühi. Jätkamine pole võimalik."
        return

    log5 = evlog.Logger()
    log5.set_logs(evfiles.log5_file(elid).path())
    if log5.lines_in_file() > 3:
        print "Log5 fail ei ole tühi. Jätkamine pole võimalik."
        return

    if not uiutil.ask_yes_no("Kas soovid hääled kokku lugeda"):
        print "Katkestame häälte lugemise"
        return
    pin = uiutil.ask_password(
        "Sisesta partitsiooni PIN: ",
        "Sisestatud PIN oli tühi!")
    subprocess.call([SCRIPT_HLR, elid, pin])


def do_del_election():
    elid = uiutil.ask_del_election_id(Election().get_questions())
    Election().delete_question(elid)


def do_restore_init_status():
    if not uiutil.ask_yes_no("Kas oled kindel"):
        return

    if not uiutil.ask_yes_no(
            "Initsialiseerimisel kustutatakse " +
            "antud hääled.\nKas jätkan"):
        return

    Election().restore_init_status()
    ElectionState().init()


def do_restore():
    """Taastame olekupuu varukoopiast.
    """

    if not uiutil.ask_yes_no("Kas soovid olekupuu varukoopiast taastada"):
        return
    if not uiutil.ask_yes_no(
            "Olekupuu taastamisel varukoopiast " +
            "kustutatakse vana olekupuu.\nKas jätkan"):
        return

    import time
    s_time = time.time()

    try:
        restorer = burner.Restorer(
            os.path.abspath(os.path.join(
                evcommon.EVREG_CONFIG, '..',
                'restore-' + time.strftime("%Y%m%d%H%M%S"))))

        while True:
            backup_dir = uiutil.ask_dir_name(
                "Sisesta kataloog, kus asuvad varukoopia failid")
            restorer.add_chunks(backup_dir)

            if not uiutil.ask_yes_no(
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
                time.strftime("%H:%M:%S",
                              time.gmtime(long(time.time() - s_time)))


def do_change_election_description(elid):
    description = uiutil.ask_string("Sisesta valimiste kirjeldus")
    el_reg = Election().get_sub_reg(elid)
    el_reg.create_string_value(['common'], 'description', description)


def do_view_status_report():
    import evfiles
    report_file = evfiles.statusreport_file().path()
    subprocess.call([PROGRAM_LESS, report_file])


def do_verification_conf():
    try:
        def_time = Election().get_verification_time()
    except (IOError, LookupError):
        def_time = 30

    try:
        def_count = Election().get_verification_count()
    except (IOError, LookupError):
        def_count = 3

    verif_time = uiutil.ask_int(
        "Sisesta taimaut hääle kontrollimiseks minutites",
        def_time, 1)
    verif_count = uiutil.ask_int(
        "Sisesta lubatud arv kordusi hääle kontrollimiseks",
        def_count, 1)

    Election().set_verification_time(verif_time)
    Election().set_verification_count(verif_count)


def do_schedule_autostart():
    time = uiutil.ask_time(
        "Sisesta valimiste automaatse algusaja kuupäev ja kellaaeg")
    autocmd.schedule(autocmd.COMMAND_START, time)


def do_unschedule_autostart():
    _, time = autocmd.scheduled(autocmd.COMMAND_START)
    if uiutil.ask_yes_no(
            "Kas soovid kustutada automaatse algusaja %s" % time,
            uiutil.ANSWER_NO):
        autocmd.unschedule(autocmd.COMMAND_START)


def do_schedule_autostop():

    time = uiutil.ask_time(
        "Sisesta nimekirjade väljastamise automaatse "
        "lõpetamise kuupäev ja kellaaeg")

    def_grace = autocmd.stop_grace_period()
    if not def_grace:
        def_grace = 15

    grace_time = uiutil.ask_int(
        "Sisesta ajavahemik nimekirjade väljastamise "
        "automaatse lõpu\nja häälte vastuvõtmise automaatse lõpu vahel "
        "minutites", def_grace, 1)
    autocmd.set_stop_grace_period(grace_time)

    autocmd.schedule(autocmd.COMMAND_PREPARE_STOP, time)


def do_unschedule_autostop():
    prepare = autocmd.scheduled(autocmd.COMMAND_PREPARE_STOP)
    stop = autocmd.scheduled(autocmd.COMMAND_STOP)
    time = prepare[1] if prepare else stop[1]
    if uiutil.ask_yes_no(
            "Kas soovid kustutada automaatse lõpuaja %s" % time,
            uiutil.ANSWER_NO):
        if prepare:
            autocmd.unschedule(autocmd.COMMAND_PREPARE_STOP)
        if stop:
            autocmd.unschedule(autocmd.COMMAND_STOP)


def do_session_conf():
    try:
        def_length = Election().get_session_length()
    except (IOError, LookupError):
        def_length = 60

    session_length = uiutil.ask_int(
        "Sisesta valimisseansi kehtivusaeg minutites",
        def_length, 1)

    Election().set_session_length(session_length)

# vim:set ts=4 sw=4 et fileencoding=utf8:
