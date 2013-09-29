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

import subprocess
import stat
import time
import os.path
import shutil
import evcommon
import uiutil

BURN_PROGRAM = "growisofs"

DVD_MIN_SPEED = 1
DVD_MAX_SPEED = 256
DVD_DEF_SPEED = 4
DVD_SIZE = 4400000000                   # DVD 4,7 GB peaks olema siis 4,4GiB'i.
DVD_CHUNK_SIZE = 1024 * 1024 * 1024     # 1GiB

APACHE2_LOG_DIR = '/var/log/apache2'


def get_backup_prefix(src_dir):
    return "evote-%s-%s." % \
        (os.path.basename(src_dir), time.strftime("%Y%m%d%-H%M%S"))


class DiskBurner:
    """Klass, mis aitab DVD-plaate kirjutada.
    """

    def __init__(self, work_dir):
        self.work_dir = work_dir
        if os.path.isdir(work_dir):
            self.delete_files()
        os.mkdir(work_dir)

    def delete_files(self):
        if os.path.isdir(self.work_dir):
            shutil.rmtree(self.work_dir, True)
        return

    def _backup(self, src_dir, backup_prefix, chunk_size):
        head, tail = os.path.split(src_dir)
        tar = subprocess.Popen(['tar', '-C', head, '-czf', '-', tail], \
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        split = subprocess.Popen(\
                ['split', '-b', '%s' % chunk_size, '-d', '-', \
                    os.path.join(self.work_dir, backup_prefix)], \
                        stdin=tar.stdout, stderr=subprocess.PIPE)
        tar.wait()
        split.wait()

        if (tar.returncode != 0):
            print tar.stderr.read()
            return False

        if (split.returncode != 0):
            print split.stderr.read()
            return False

        return True

    def backup_dir(self, src_dir, apache=False):
        if not self._backup(src_dir, get_backup_prefix(src_dir), \
                DVD_CHUNK_SIZE):
            return False

        if apache and not self._backup(APACHE2_LOG_DIR, \
                get_backup_prefix(APACHE2_LOG_DIR), DVD_CHUNK_SIZE):
            return False

        # Jagame jupid DVD'de kaupa kataloogidesse.

        chunks = os.listdir(self.work_dir)
        chunks.sort()

        dvd_count = 0
        current_size = 0
        current_dir = os.path.join(self.work_dir, "%d" % dvd_count)
        os.mkdir(current_dir)

        for chunk in chunks:
            chunk_path = os.path.join(self.work_dir, chunk)
            chunk_size = os.path.getsize(chunk_path)

            if current_size + chunk_size > DVD_SIZE:
                current_size = 0
                dvd_count += 1
                current_dir = os.path.join(self.work_dir, "%d" % dvd_count)
                os.mkdir(current_dir)
            current_size += chunk_size

            os.rename(chunk_path, os.path.join(current_dir, chunk))

        return True

    def burn(self):
        dvd_def_speed = DVD_DEF_SPEED
        dvd_count = 0
        dvd_dirs = os.listdir(self.work_dir)
        dvd_dirs_size = len(dvd_dirs)
        dvd_dirs.sort()

        for dvd_dir in dvd_dirs:
            dvd_count += 1

            if dvd_dirs_size > 1:
                print "Hakkame krijutama %d. DVD-d %d-st" % \
                        (dvd_count, dvd_dirs_size)

            if not uiutil.ask_yes_no(\
                    "Palun sisestage DVDR(W) meedia seadmesse. Jätkan"):
                print "DVD kirjutamine katkestati"
                return 1

            while True:
                dvd_speed = uiutil.ask_int(\
                        "Palun sisestage DVD kirjutamiskiirus", \
                        dvd_def_speed, DVD_MIN_SPEED, DVD_MAX_SPEED)
                dvd_def_speed = dvd_speed

                cmdline = '%s -speed=%d -Z /dev/dvd -q -r -J %s' % \
                        (BURN_PROGRAM, dvd_speed, \
                            os.path.join(self.work_dir, dvd_dir))

                print cmdline
                rc = subprocess.call(cmdline, shell=True)
                if rc == 0:
                    break
                print "Salvestamine nurjus veakoodiga %d" % rc
                if not uiutil.ask_yes_no("Kas proovite uuesti"):
                    print "DVD kirjutamine katkestati"
                    return 1
        return 0


class Restorer (DiskBurner):
    def __init__(self, work_dir):
        DiskBurner.__init__(self, work_dir)
        self.chunks = []

    def chunk_count(self):
        return len(self.chunks)

    def add_chunks(self, src_dir):
        count = 0
        for chunk in os.listdir(src_dir):
            if chunk.startswith("evote-registry"):
                print "Kopeerin faili '%s' ..." % chunk
                shutil.copy(os.path.join(src_dir, chunk), self.work_dir)
                subprocess.call('chmod ug+w %s' % \
                        os.path.join(self.work_dir, chunk), shell=True)
                self.chunks.append(os.path.join(self.work_dir, chunk))
                count += 1
        if (count == 0):
            print 'Kataloogis \'%s\' ei olnud ühtegi varukoopia faili' % \
                    src_dir

    def restore(self, reg_dir):
        if len(self.chunks) == 0:
            print('Pole ühtegi varukoopia faili. Loobun taastamisest')
            return

        self.chunks.sort()

        command = ['cat']
        command.extend(self.chunks)

        cat = subprocess.Popen(command, stdout=subprocess.PIPE, \
                stderr=subprocess.PIPE)
        tar = subprocess.Popen(['tar', '-xzp'], \
                stdin=cat.stdout, stderr=subprocess.PIPE,\
                cwd=self.work_dir)
        cat.wait()
        tar.wait()

        if (cat.returncode != 0):
            print cat.stderr.read()
            return False

        if (tar.returncode != 0):
            print tar.stderr.read()
            return False

        # Nüüd võime vana registri uue vastu vangerdada.
        os.rename(reg_dir, '%s-%s' % \
                (reg_dir, time.strftime("%Y%m%d%H%M%S")))
        os.rename(os.path.join(self.work_dir, 'registry'), reg_dir)

        return True


class FileListBurner(DiskBurner):

    def __init__(self, work_dir):
        DiskBurner.__init__(self, work_dir)
        self.application_log_exists = False
        self.error_log_exists = False
        self.debug_log_exists = False
        self.current_disk = None
        self.current_disk_name = ''
        self.session_dir_name = ''
        self.session_id = 'evote-%s' % time.strftime("%Y%m%d%-H%M%S")
        self.current_dvd_size = 0

    def _disk_name(self, election_id):
        self.current_disk_name = os.path.join(self.work_dir, '%d' % \
                self.current_disk)
        self.session_dir_name = os.path.join(self.current_disk_name, '%s' % \
                self.session_id)
        ret = os.path.join(self.session_dir_name, '%s' % election_id)
        if not os.path.isdir(ret):
            os.makedirs(ret)
        return ret

    def _new_disk(self, election_id):
        if self.current_disk == None:
            self.current_disk = 0
        else:
            self.current_disk += 1
        ret = self._disk_name(election_id)
        return ret

    def append_files(self, election_id, file_list):

        dir_name = ''
        if self.current_disk != None:
            dir_name = self._disk_name(election_id)
        else:
            dir_name = self._new_disk(election_id)

        for i in file_list:
            file_size = 0
            try:
                file_size = os.stat(i)[stat.ST_SIZE]
            except OSError:
                print "Faili '%s' ei eksisteeri" % i
                continue

            if file_size > DVD_SIZE:
                print "Fail '%s' on liiga suur, et DVD-le mahtuda" % i
                continue

            if file_size + self.current_dvd_size > DVD_SIZE:
                self.current_dvd_size = file_size
                dir_name = self._new_disk(election_id)

            tail = os.path.split(i)[1]

            if tail == evcommon.APPLICATION_LOG_FILE:
                if not self.application_log_exists:
                    shutil.copy(i, self.session_dir_name)
                    self.application_log_exists = True
            elif tail == evcommon.ERROR_LOG_FILE:
                if not self.error_log_exists:
                    shutil.copy(i, self.session_dir_name)
                    self.error_log_exists = True
            elif tail == evcommon.DEBUG_LOG_FILE:
                if not self.debug_log_exists:
                    shutil.copy(i, self.session_dir_name)
                    self.debug_log_exists = True
            else:
                shutil.copy(i, dir_name)

        return True


# vim:set ts=4 sw=4 et fileencoding=utf8:
