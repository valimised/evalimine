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

import re
import os
import time
import getpass
import shutil
# tab-completioni jaoks vajalikud moodulid
import curses.ascii
import struct
import fcntl
import termios
import glob
import sys
import tty

NOT_DEFINED_STR = "pole määratud"

ANSWER_YES = "jah"
ANSWER_NO = "ei"

TMPFILE_PREFIX = "evotetmp"


def del_tmp_files():
    map(os.remove, glob.iglob("/tmp/%s*" % TMPFILE_PREFIX))


def clear_dir(dir_):
    for entry in os.listdir(dir_):
        path = os.path.join(dir_, entry)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except Exception as e:
            print "Viga %s kustutamisel: %s" % (path, e.message)


def clrscr():
    os.system("clear")


def ask_del_election_id(election_ids):
    """
    Küsib operaatorilt valimiste ID-d, mida kustutda.
    @return: valimiste identifikaator
    """
    do = 1
    while do:
        elid = ask_string(
            "Sisestage kustutatav valimiste identifikaator", "^\w{1,28}$",
            "Valimiste identifikaator peab olema 1..28 tähte/numbrit")
        if elid in election_ids:
            do = 0
        else:
            print 'Valimiste identifikaatorit "%s" ei ole' % elid
    return elid


def ask_election_id(election_ids):
    """
    Küsib operaatorilt valimiste ID-d. Duplikaatite kontrollime
    listilst election_ids
    @return: valimiste identifikaator
    """
    do = 1
    while do:
        elid = ask_string(
            "Sisestage valimiste identifikaator",
            "^\w{1,28}$",
            "Valimiste identifikaator peab olema 1..28 tähte/numbrit")
        do = 0
        for i in range(len(election_ids)):
            if elid == election_ids[i]:
                print "Valimiste identifikaator pole unikaalne"
                do = 1
                break
    return elid


def ask_id_num():
    """
    Küsib operaatorilt isikukoodi.
    @return: isikukood
    """
    return ask_string(
        "Sisesta isikukood", "^\d{11,11}$",
        "Isikukood peab koosnema 11-st numbrist")


def ask_file_name(prefix, default=None):
    """
    Küsib operaatorilt faili nime.
    @return: faili nimi
    """
    while True:
        filename = ask_string(prefix, None, None, default)
        if not check_file(filename):
            print ("Faili %s pole olemas või on tegu kataloogiga" %
                   filename)
            continue
        break
    return filename


def ask_dir_name(prefix, default=None):
    """
    Küsib operaatorilt kataloogi nime.
    @return: kataloogi nimi
    """
    while True:
        dirname = ask_string(prefix, None, None, default)
        if not check_dir(dirname):
            print ("Kataloogi %s pole olemas või on tegu failiga" %
                   dirname)
            continue
        break
    return dirname


def ask_file_name_from_cd(prefix, default=None):
    """
    Küsib operaatorilt faili nime. Faili kopeeritakse /tmp/
    kataloogi spets prefikiga, et võimaldada CD vahetust dialoogi ajal.
    @return: faili nimi
    """

    EXTENSIONS = [".signature", ".sig", ".sha256", ".sha1"]

    while True:
        file_path = ask_string(prefix, None, None, default)
        if not check_file(file_path):
            print "Faili %s pole olemas või on tegu kataloogiga" % file_path
            continue
        file_name = os.path.split(file_path)[1]
        time_str = time.strftime("%Y%m%d%H%M%S")
        tmp_file = os.path.join("/", "tmp", "%s_%s_%s" %
                                (TMPFILE_PREFIX, time_str, file_name))
        print "Palun oota. Laadin faili.."
        try:
            shutil.copyfile(file_path, tmp_file)
            for ext in EXTENSIONS:
                if check_file(file_path + ext):
                    shutil.copyfile(file_path + ext, tmp_file + ext)
                    break  # for one extension
            break  # for endless loop
        except Exception as what:
            print "Viga! Faili ei õnnestu laadida: %s." % str(what)
    return tmp_file


def ask_yes_no(prefix, default=None):
    while True:
        if default is not None:
            yn = raw_input("%s (%s/%s) [%s]? " %
                           (prefix, ANSWER_YES, ANSWER_NO, default))
        else:
            yn = raw_input("%s (%s/%s)? " %
                           (prefix, ANSWER_YES, ANSWER_NO))
        yn = yn.strip().lower()
        if len(yn) > 0 and ANSWER_YES.find(yn) == 0:
            return 1
        if len(yn) > 0 and ANSWER_NO.find(yn) == 0:
            return 0
        if len(yn) == 0:
            if default == ANSWER_YES:
                return 1
            elif default == ANSWER_NO:
                return 0
        print "Palun vasta %s või %s!" % (ANSWER_YES, ANSWER_NO)


def check_file(path):
    return os.path.isfile(path)


def check_dir(path):
    return os.path.isdir(path)


def ask_int(prefix, default, minval=None, maxval=None):
    while True:
        i = raw_input("%s [%d]: " % (prefix, default))
        i = i.strip()
        if len(i) == 0:
            return default
        try:
            retval = int(i)
        except ValueError:
            print "Palun sisesta täisarv"
            continue
        if minval is not None and retval < minval:
            print "Palun sisesta täisarv, mis on võrdne või suurem " + \
                "kui %d" % minval
            continue
        if maxval is not None and retval > maxval:
            print "Palun sisesta täisarv, mis on võrdne või väiksem " + \
                "kui %d" % maxval
            continue
        return retval


def ask_time(prefix, format="%d.%m.%Y %H:%M", default=None):
    while True:
        if default is None:
            tstr = raw_input("%s: " % prefix)
        else:
            tstr = raw_input("%s [%s]: " %
                             (prefix, time.strftime(format, default)))
        tstr = tstr.strip()
        if len(tstr) == 0 and default:
            return default
        try:
            return time.strptime(tstr, format)
        except ValueError:
            print "Palun sisesta kuupäev ja kellaaeg kujul %s" % format
            continue


def ask_string(prefix, pattern=None, err_text=None, default=None):
    """
    Küsib operaatorilt küsimuse prefix. Sisestatud vastus peab
    kattuma mustriga pattern, vastasel korral näidatakse
    veateksti err_text ja uuele ringile.
    @return: sisestatud string
    """
    while True:
        if default is None:
            in_str = _get_string("%s: " % prefix)
        else:
            in_str = _get_string("%s [%s]: " % (prefix, default))
        in_str = in_str.strip()
        if len(in_str) < 1:
            if default is not None:
                in_str = default
            else:
                if err_text is not None:
                    print err_text
                continue
        if (pattern is not None):
            if not re.compile(pattern).match(in_str):
                if err_text is not None:
                    print err_text
                continue
            else:
                return in_str
        else:
            return in_str


def ask_int_list(prefix, maxnum):
    numstr = ask_string(prefix, r'^\d+(,\s*\d+)*$')
    numlist = []
    for el in numstr.split(','):
        tok = int(el) - 1
        if (tok >= 0) and (tok < maxnum):
            numlist.append(tok)
        else:
            print 'Ei arvesta vigast väärtust: %d' % (tok + 1)

    return numlist


def ask_password(prefix, err_text):
    """
    Küsib operaatorilt parooli.
    @return: sisestatud string
    """
    while True:
        in_str = getpass.getpass(prefix)
        in_str = in_str.strip()
        if len(in_str) < 1:
            print err_text
            continue
        else:
            return in_str


def _get_string(prefix):
    """
    Küsib stdio'st stringi. TAB klahv toimib autocomplete'na.
    @return sisestatud string
    """
    inp = ""

    sys.stdout.write(prefix)
    _to_new_line(prefix, inp)

    ch = _get_char()
    # Kuni sisestatakse "Enter"
    while ord(ch) != curses.ascii.CR:
        if ord(ch) == curses.ascii.EOT:
            # CTRL-D katkestab
            raise EOFError()
        if ord(ch) == curses.ascii.TAB:
            # TAB-completion
            comp = _complete(inp)
            if len(comp) == len(inp):
                # Autocomplete ei aita, pakume faile
                files = _possible(inp)
                if len(files) > 0:
                    print _display(files)
                    sys.stdout.write(prefix)
                    sys.stdout.write(inp)
                    _to_new_line(prefix, inp)
            else:
                # Autocomplete
                sys.stdout.write(comp[len(inp):])
                inp = inp + comp[len(inp):]
                _to_new_line(prefix, inp)
        elif ord(ch) == curses.ascii.DEL and len(inp) > 0:
            # Backspacega kustutamine
            if _del_char(prefix, inp):
                inp = inp[:-1]
        else:
            # Uue sümboli sisestamine
            sys.stdout.write(ch)
            inp = inp + ch
            _to_new_line(prefix, inp)
        ch = _get_char()

    # Reavahetus lõppu
    sys.stdout.write(chr(curses.ascii.LF))
    return inp


def _to_new_line(prefix, inp):
    """
    Kui sisestamisel satuti rea loppu, siis kursor uuele reale
    """
    _, _w = _term_size()
    # et saaks õige kuvatava tähtede arvu
    prefix_len = len(unicode(prefix, "utf8"))
    if (prefix_len + len(inp)) % _w == 0 and prefix_len + len(inp) > 0:
        fd = sys.stdin.fileno()
        # vana seadistus
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            _go_down()
            for _ in range(0, _w):
                _go_left()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _del_char(prefix, inp):
    """
    Kursor kas samm vasakule või rida ülespoole ja lõppu.
    Tagastab:
        False - midagi ei juhtunud
        True - kustutati symbol
    """
    _, _w = _term_size()
    # et saaks õige kuvatava tähtede arvu
    prefix_len = len(unicode(prefix, "utf8"))
    if (prefix_len + len(inp)) % _w == 0 and prefix_len + len(inp) > 0:
        up_and_right = True
    elif len(inp) > 0:
        up_and_right = False
    else:
        return False

    fd = sys.stdin.fileno()
    # vana seadistus
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        if up_and_right:
            _go_up()
            for _ in range(0, _w):
                _go_right()
            sys.stdout.write(chr(curses.ascii.SP))
            _go_left()
            # Samm tagasi ja kirjutame üle, et kursor
            # saaks õigele kohale
            if len(inp) > 1:
                sys.stdout.write(inp[-2])
            else:
                sys.stdout.write(prefix[-1])
        else:
            _go_left()
            sys.stdout.write(chr(curses.ascii.SP))
            _go_left()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return True


def _go_left():
    sys.stdout.write(chr(27))
    sys.stdout.write(chr(91))
    sys.stdout.write(chr(68))


def _go_right():
    sys.stdout.write(chr(27))
    sys.stdout.write(chr(91))
    sys.stdout.write(chr(67))


def _go_up():
    sys.stdout.write(chr(27))
    sys.stdout.write(chr(91))
    sys.stdout.write(chr(65))


def _go_down():
    sys.stdout.write(chr(curses.ascii.LF))


def _get_char():
    """
    Küsib stdio'st üksiku sümboli seda ekraanile kuvamata
    """
    fd = sys.stdin.fileno()
    # vana seadistus
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def _complete(string):
    """
    Tagastab argumendina antud stringi, millele on appenditud
    võimalik completion. Kui completionit ei leidu, siis
    tagastatakse esialgne string
    """
    if len(string) == 0:
        return "/"
    if string[0] != "/":
        # abi ainult fullpathi leidmisel
        return string
    if '*' not in string:
        string += "*"

    _g = glob.glob(string)
    if len(_g) == 0:
        _s = string[:-1]
    elif len(_g) == 1:
        _s = _g[0]
        if os.path.isdir(_s) and _s[-1] != "/":
            _s += "/"
        if os.path.isfile(_s) and _s[-1] != " ":
            _s += " "
    else:
        chars_lst = zip(*_g)
        for i in range(0, len(chars_lst)):
            chars = chars_lst[i]
            if min(chars) != max(chars):
                j = i
                break
            else:
                j = min([len(_s) for _s in _g])
        _s = _g[0][:j]
    _s = os.path.expanduser(_s)
    return _s


def _possible(string):
    """
    Tagastab listi võimalikest failidest, mida järgnevalt valida.
    """
    if string[0] != '/':
        return []

    if '*' not in string:
        string += "*"

    _g = glob.glob(string)
    lst = []
    for file_name in _g:
        lst.append(file_name.split('/')[-1:][0])
    return lst


def _display(files):
    """
    Tagastab listis olevatest failidest moodustatud stringi, mis
    on kuvamiseks sobival kujul. Kirjed on sorteeritud ning
    arvestatakse terminaliakna suurust.
    """
    files.sort()
    max_len = 0
    for file_name in files:
        if len(file_name) > max_len:
            max_len = len(file_name)
    max_len = max_len + 2
    cols = _term_size()[1] / max_len
    rows = len(files) / cols
    if len(files) % cols != 0:
        rows = rows + 1

    table = "\n"
    for i in range(0, rows):
        for j in range(0, cols):
            idx = i + j * rows
            if idx < len(files):
                table = table + files[i + j * rows].ljust(max_len)
        table = table + '\n'
    return table[:-1]


def _term_size():
    """
    Tagastab tuple (height, width) terminaliakna mõõtmetest.
    """
    _h, _w = struct.unpack(
        "hhhh", fcntl.ioctl(0, termios.TIOCGWINSZ, "\000" * 8))[0:2]
    return _h, _w


# vim:set ts=4 sw=4 et fileencoding=utf8:
