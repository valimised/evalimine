# Registry
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

"""
Module to implement filesystem based registry, where registry keys are
directories and registry values (with types) are stored in files.

Supported value types: string (UTF8), integer (int32) and IP
Address.

@var    STRING: string type
@var    STRING_STR: string prefix to identify string types in registry value
            files
@var    INTEGER: integer type
@var    INTEGER_STR: string prefix to identify integer types in registry value
            files
@var    IP_ADDR: IP address type
@var    IP_ADDR_STR: prefix to identify IP address types in registry value
            files
"""

import os
import fcntl

STRING = 1
INTEGER = 2
IP_ADDR = 3

STRING_STR = 'string:'
INTEGER_STR = 'integer:'
IP_ADDR_STR = 'ip_addr:'


def create_registry(path_to_registry):
    try:
        os.stat(path_to_registry)
    except OSError:
        os.makedirs(path_to_registry)


class Registry:
    """Registry handling class
    """

    def __init__(self, **args):
        """
        @type       root: string
        @keyword    root: root directory of registry
        """
        self.root = args['root']
        os.stat(self.root)

    def _dirname(self, key):
        return os.path.join(self.root, *key)

    def path(self, key=['']): # pylint: disable=W0102
        return self._dirname(key)

    def reset_key(self, key):
        self.ensure_no_key(key)
        self.create_key(key)

    def ensure_key(self, key):
        """Ensure there's key 'key' in the registry
        @type   key: string
        @param  key: key name
        Returns True if the key was created, False otherwise
        """
        if not self.check(key):
            self.create_key(key)
            return True
        return False

    def ensure_no_key(self, key):
        """Ensure there's no key 'key' in the registry
        @type   key: string
        @param  key: key name
        Returns True if the key existed, False otherwise
        """
        if self.check(key):
            self.delete_key(key)
            return True
        return False

    def create_key(self, key):
        """Create registry key

        @type   key: string
        @param  key: key name
        """
        os.makedirs(self._dirname(key))

    def delete_key(self, key=['']): # pylint: disable=W0102
        """Delete registry key

        @type   key: string
        @param  key: key name
        """

        self.delete_sub_keys(key)
        os.rmdir(self._dirname(key))

    def delete_sub_keys(self, key):
        """
        Delete subkeys of a registry key
        @type   key: string
        @param  key: key name
        """

        if not self.check(key):
            return

        dname = self._dirname(key)

        for name in os.listdir(dname):
            path = os.path.join(dname, name)
            if os.path.isdir(path):
                self.delete_key(key + [name])
            else:
                os.remove(path)

    def truncate_value(self, key, name):
        RegistryValue(self.root, key, name).truncate()

    def list_keys(self, sub=['']): # pylint: disable=W0102
        """List subkeys
        @type   sub: string
        @param  sub: subkey to list
        @return: list of subkeys
        """
        return os.listdir(self._dirname(sub))

    def check(self, key):
        """Check registry key

        @type   key: string
        @param  key: key name

        @return: False when key does not exist, True otherwise
        """
        try:
            os.stat(self._dirname(key))
        except OSError:
            return False
        return True

    def create_value(self, key, name, value, ttype=STRING):
        """Create registry value

        @type   key: string
        @param  key: key name
        @type   name: string
        @param  name: value name
        @type   value: string or integer
        @param  value: registry value
        @type   type: integer
        @param  type: value type

        @return: RegistryValue object
        """
        val = RegistryValue(self.root, key, name)
        val.create(value, ttype)
        return val

    def create_string_value(self, key, name, value):
        """L{CreateValue} wrapper for String values
        """
        return self.create_value(key, name, value, STRING)

    def create_integer_value(self, key, name, value):
        """L{CreateValue} wrapper for Integer values
        """
        return self.create_value(key, name, value, INTEGER)

    def create_ipaddr_value(self, key, name, value):
        """L{CreateValue} wrapper for IP addr values
        """
        return self.create_value(key, name, value, IP_ADDR)

    def read_value(self, key, name, ttype=None):
        """Read registry value

        @type   key: string
        @param  key: key name
        @type   name: string
        @param  name: value name
        @type   ttype: integer
        @param  ttype: value type

        @return: RegistryValue object
        """
        val = RegistryValue(self.root, key, name)
        val.read(ttype)
        return val

    def read_string_value(self, key, name):
        """L{ReadValue} wrapper for String values
        """
        return self.read_value(key, name, STRING)

    def read_integer_value(self, key, name):
        """L{ReadValue} wrapper for Integer values
        """
        return self.read_value(key, name, INTEGER)

    def read_ipaddr_value(self, key, name):
        """L{ReadValue} wrapper for IP Address values
        """
        return self.read_value(key, name, IP_ADDR)

    def delete_value(self, key, name):
        return RegistryValue(self.root, key, name).delete()


class RegistryValue:
    """Class to represent registry value

    @type   have_value: boolean
    @ivar   have_value: True, when RegistryValue have value assigned
    @type   root: string
    @ivar   root: root directory of regsitry
    @type   key: string
    @ivar   key: regsitry key name
    @type   name: string
    @ivar   name: value name
    @type   ttype: integer
    @ivar   ttype: value type
    @type   value: string or integer
    @ivar   value: value
    """

    def __init__(self, root, key, name):
        """

        @type   root: string
        @param  root: root directory of registry
        @type   key: string
        @param  key: registry key name
        @type   name: string
        @param  name: registry value name
        """
        self.root = root
        self.key = key
        self.name = name
        self.ttype = None
        self.value = None
        self.have_value = False

    def __repr__(self):
        if not self.have_value:
            raise LookupError("No value")
        return self.value

    def _filename(self):
        fp = [self.root] + self.key + [self.name]
        return os.path.join(*fp)

    def check(self):
        try:
            os.stat(self._filename())
        except OSError:
            return False
        return True

    def create(self, value, ttype):
        """Creates new registry value

        @type   value: string or integer
        @param  value: registry value
        @type   type: integer
        @param  type: value type
        """

        typestr = ''

        if ttype == STRING:
            typestr = STRING_STR
        elif ttype == INTEGER:
            typestr = INTEGER_STR
        elif ttype == IP_ADDR:
            typestr = IP_ADDR_STR
        else:
            raise TypeError("No valid type given")

        _wf = file(self._filename(), 'w')
        fcntl.lockf(_wf, fcntl.LOCK_EX)
        _wf.write('%s%s' % (typestr, value))
        _wf.close()
        self.ttype = ttype
        self.value = value
        self.have_value = True

    def read(self, ttype=None):
        """Read registry value

        Raises LookupError when values does not exist or TypeError when
        value type is not as requested type

        @type   type: integer
        @param  type: Value type (STRING, INTEGER, IP_ADDR) or None
                when type will automatically detected

        """
        _rf = file(self._filename(), 'r')
        fcntl.lockf(_rf, fcntl.LOCK_SH)
        val = _rf.read(-1)
        _rf.close()
        if val.find(STRING_STR, 0, len(STRING_STR)) == 0:
            if not ttype in [STRING, None]:
                raise TypeError("Type mismatch")
            self.value = val.replace(STRING_STR, '', 1)
            self.ttype = STRING

        elif val.find(INTEGER_STR, 0, len(INTEGER_STR)) == 0:
            if not ttype in [INTEGER, None]:
                raise TypeError("Type mismatch")
            self.value = int(val.replace(INTEGER_STR, '', 1))
            self.ttype = INTEGER

        elif val.find(IP_ADDR_STR, 0, len(IP_ADDR_STR)) == 0:
            if not ttype in [IP_ADDR, None]:
                raise TypeError("Type mismatch")
            self.value = str(val.replace(IP_ADDR_STR, '', 1))
            self.ttype = IP_ADDR

        else:
            raise LookupError("No value")

        self.have_value = True

    def delete(self):
        """Delete registry value
        """
        os.remove(self._filename())

    def truncate(self):
        if self.check():
            _wf = file(self._filename(), 'w')
            fcntl.lockf(_wf, fcntl.LOCK_EX)
            _wf.truncate()
            _wf.close()



# vim:set ts=4 sw=4 et fileencoding=utf8:
