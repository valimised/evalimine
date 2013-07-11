
SWIG_SOURCES = bdocpython.i
BUILT_SOURCES = $(srcdir)/bdocpython_wrap.cxx 

pkgpython_PYTHON = bdocpython.py

pkgpyexec_LTLIBRARIES = _bdocpython.la

_bdocpython_la_SOURCES = $(srcdir)/bdocpython_wrap.cxx $(SWIG_SOURCES)
_bdocpython_la_CPPFLAGS = $(SWIG_PYTHON_CPPFLAGS) -I$(top_srcdir)/src
_bdocpython_la_LDFLAGS = -module
_bdocpython_la_LIBADD = ../src/libbdoc.la -lpython2.7

bdocpython_wrap.cxx : $(SWIG_SOURCES)
	$(SWIG) $(SWIG_PYTHON_OPT) -I$(top_srcdir)/src -o $@ $<

CLEANFILES = bdocpython_wrap.cxx bdocpython.py *.pyc


