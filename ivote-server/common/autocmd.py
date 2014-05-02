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
import signal
import subprocess
import sys
import time

import election
import evcommon
import evreg

# Commands to automatically execute.
COMMAND_START = "start"
COMMAND_PREPARE_STOP = "prepare_stop"
COMMAND_STOP = "stop"

# Expected server states for the commands.
EXPECTED = {
        COMMAND_START:        election.ETAPP_ENNE_HAALETUST,
        COMMAND_PREPARE_STOP: election.ETAPP_HAALETUS,
        COMMAND_STOP:         election.ETAPP_HAALETUS,
    }

# The name of this module.
MODULE_AUTOCMD = "autocmd"

# The registry key for this module.
AUTOCMD_KEY = ["common", "autocmd"]

TIME_FORMAT = "%H:%M %d.%m.%Y"

# Registry location of the pid of a console to refresh when a command executes.
# It might make more sense for these to be in evui/evui.py, but we can't import
# evui from here, because it is a private module.
REFRESH_PID_KEY = ["common"]
REFRESH_PID_VALUE = "refresh.pid"

# Translated messages.
ERROR_SUBPROCESS = "Programmi väljakutsel esines viga: %s"
ERROR_SCHEDULE = "Automaatse sündmuse seadistamine ebaõnnestus!"

def stop_grace_period():
    """Get the configured time between COMMAND_PREPARE_STOP and COMMAND_STOP."""
    reg = evreg.Registry(root=evcommon.EVREG_CONFIG)
    try:
        return reg.read_integer_value(AUTOCMD_KEY, "grace").value
    except (IOError, LookupError):
        return None

def set_stop_grace_period(grace):
    """Configure the time between COMMAND_PREPARE_STOP and COMMAND_STOP."""
    reg = evreg.Registry(root=evcommon.EVREG_CONFIG)
    reg.ensure_key(AUTOCMD_KEY)
    reg.create_integer_value(AUTOCMD_KEY, "grace", grace)

def _job_value(cmd):
    return cmd + "_job"

def _time_value(cmd):
    return cmd + "_time"

def scheduled(cmd):
    reg = evreg.Registry(root=evcommon.EVREG_CONFIG)
    if not reg.check(AUTOCMD_KEY):
        return None
    try:
        job = reg.read_integer_value(AUTOCMD_KEY, _job_value(cmd)).value
        timestr = reg.read_string_value(AUTOCMD_KEY, _time_value(cmd)).value
    except (IOError, LookupError):
        return None
    return job, timestr

def _at(timestr, command):
    proc = subprocess.Popen(("at", timestr),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, err = proc.communicate(command)

    if proc.returncode != 0:
        print ERROR_SUBPROCESS % err
        return None

    for line in err.splitlines():
        if line.startswith("job "):
            _, job, _ = line.split(None, 2)
    return int(job)

def schedule(cmd, tstruct):
    if scheduled(cmd):
        raise Exception, "Command already scheduled"
    timestr = time.strftime(TIME_FORMAT, tstruct)
    job = _at(timestr, "python -m %s %i %s" % (MODULE_AUTOCMD, EXPECTED[cmd], cmd))
    if not job:
        print ERROR_SCHEDULE
        return

    reg = evreg.Registry(root=evcommon.EVREG_CONFIG)
    reg.ensure_key(AUTOCMD_KEY)
    reg.create_integer_value(AUTOCMD_KEY, _job_value(cmd), job)
    reg.create_string_value(AUTOCMD_KEY, _time_value(cmd), timestr)

def _atrm(job):
    try:
        subprocess.check_output(("atrm", str(job)), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print ERROR_SUBPROCESS % e.output

def _clean_reg(cmd):
    reg = evreg.Registry(root=evcommon.EVREG_CONFIG)
    try:
        reg.delete_value(AUTOCMD_KEY, _job_value(cmd))
    except OSError:
        pass
    try:
        reg.delete_value(AUTOCMD_KEY, _time_value(cmd))
    except OSError:
        pass

def unschedule(cmd, job):
    _atrm(job)
    _clean_reg(cmd)

def _execute_start():
    if election.ElectionState().get() == election.ETAPP_ENNE_HAALETUST:
        election.ElectionState().next()

def _execute_prepare_stop():
    import datetime

    if election.ElectionState().election_on():
        election.Election().refuse_new_voters()
        sched = scheduled(COMMAND_PREPARE_STOP)
        minutes = stop_grace_period()
        if not sched or not minutes:
            return
        _, time = sched

        dt = datetime.datetime.strptime(time, TIME_FORMAT)
        dt += datetime.timedelta(minutes=minutes)
        print "Scheduling command \"stop\" for %s" % dt
        schedule(COMMAND_STOP, dt.timetuple())

def _execute_stop():
    if election.ElectionState().election_on():
        election.ElectionState().next()

def _signal_ui():
    print "Signaling UI to refresh...",
    try:
        reg = evreg.Registry(root=evcommon.EVREG_CONFIG)
        pid = reg.read_integer_value(REFRESH_PID_KEY, REFRESH_PID_VALUE).value
    except IOError:
        print "No UI PID found."
    else:
        print "Found UI with PID %i" % pid
        os.kill(pid, signal.SIGUSR1)

def _main(expected, cmd):
    if election.ElectionState().get() == int(expected):
        print "Executing automatic command \"%s\"" % cmd
        if cmd == COMMAND_START:
            _execute_start()
        elif cmd == COMMAND_PREPARE_STOP:
            _execute_prepare_stop()
        elif cmd == COMMAND_STOP:
            _execute_stop()
        else:
            raise Exception, "Unknown command"
        _clean_reg(cmd)
        _signal_ui()
        print "Done."
    else:
        print "Unexpected state, nothing to do."

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: %s <expected-state> <command>" % sys.argv[0]
        print "  Checks that the server is in state <expected-state> and then " \
                "executes the commands associated with <command>."
        print "  <expected-state> is a constant from election.py"
        print "  <command> is a constant from autocmd.py"
        sys.exit(1)
    _main(sys.argv[1], sys.argv[2])

# vim: set ts=4 sw=4 et fileencoding=utf8:
