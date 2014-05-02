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

import time
import election
from evlog import AppLog
import htscommon

def purge_otp(otp_key):
    elec = election.Election()
    reg = elec.get_root_reg()

    voter = reg.read_string_value(otp_key, "voter").value.rstrip()
    voter_key = htscommon.get_user_key(voter)
    elids = reg.read_string_value(otp_key, "elids").value.rstrip().split("\t")

    for elid in elids:
        sreg = elec.get_sub_reg(elid)
        if sreg.check(voter_key + [htscommon.VOTE_VERIFICATION_ID_FILENAME]):
            sreg.delete_value(voter_key, htscommon.VOTE_VERIFICATION_ID_FILENAME)
    reg.ensure_no_key(otp_key)

def purge_otps():
    runtime = int(time.time())
    AppLog().set_app("purgeotps.py")
    AppLog().log("Purging expired vote ID's as of %s: START" % \
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(runtime)))
    try:
        reg = election.Election().get_root_reg()
        timeout = election.Election().get_verification_time() * 60
        for otp in reg.list_keys(htscommon.get_verification_key()):
            otp_key = htscommon.get_verification_key(otp)
            created = reg.read_integer_value(otp_key, "timestamp").value
            if created + timeout < runtime:
                AppLog().log("Purging expired vote ID %s" % otp)
                purge_otp(otp_key)
    except:
        AppLog().log_exception()
    finally:
        AppLog().log("Purging expired vote ID's: DONE")


if __name__ == '__main__':
    if election.ElectionState().election_on():
        purge_otps()

# vim:set ts=4 sw=4 et fileencoding=utf8:
