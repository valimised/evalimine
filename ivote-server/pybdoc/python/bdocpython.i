%module bdocpython

/*
Copyright: Eesti Vabariigi Valimiskomisjon
(Estonian National Electoral Committee), www.vvk.ee
Written in 2004-2013 by Cybernetica AS, www.cyber.ee

This work is licensed under the Creative Commons
Attribution-NonCommercial-NoDerivs 3.0 Unported License.
To view a copy of this license, visit
http://creativecommons.org/licenses/by-nc-nd/3.0/.
*/


%{
	#include "PyBDoc.h"
%}

%rename(assign) *::operator=;
%apply (char *STRING, int LENGTH) { (const char *xml, size_t xml_len) };
%apply (char *STRING, int LENGTH) { (const unsigned char *buf, size_t len) };

%include std_string.i

%include std_list.i

%template(strlist) std::list<std::string>;

%include exception.i
%exception {
        try {
                $action
        }
        catch (std::exception& exc) {
                SWIG_exception(SWIG_RuntimeError, exc.what());
        }
        catch (...) {
                SWIG_exception(SWIG_RuntimeError,"Unknown exception");
        }
}

%include PyBDoc.h

