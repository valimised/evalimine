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

import purge
from election import Election
from election import ElectionState
import htscommon


def purge_otp(reg, otp):
    otp_key = htscommon.get_verification_key(otp)

    voter = reg.read_string_value(otp_key, "voter").value.rstrip()
    voter_key = htscommon.get_user_key(voter)
    elids = reg.read_string_value(otp_key, "elids").value.rstrip().split("\t")

    for elid in elids:
        sreg = Election().get_sub_reg(elid)
        if sreg.check(voter_key + [htscommon.VOTE_VERIFICATION_ID_FILENAME]):
            sreg.delete_value(voter_key, htscommon.VOTE_VERIFICATION_ID_FILENAME)
    reg.ensure_no_key(otp_key)


def purge_otps():

    # Read the verification timeout value before defining check_otp, so we only
    # have to read it once.
    timeout = Election().get_verification_time() * 60

    def check_otp(reg, otp, runtime):
        otp_key = htscommon.get_verification_key(otp)
        created = reg.read_integer_value(otp_key, "timestamp").value
        return created + timeout < runtime

    purger = purge.Purger("expired vote ID", htscommon.get_verification_key())
    purger.work(check_otp, purge_otp)


if __name__ == '__main__':
    if ElectionState().election_on():
        purge_otps()

# vim:set ts=4 sw=4 et fileencoding=utf8:
