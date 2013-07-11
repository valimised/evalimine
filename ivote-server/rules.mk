ROOT_DIR:=$(dir $(lastword $(MAKEFILE_LIST)))
PYTHON_SUBDIRS=common hes hts hlr evui cgi
PYTHONPATH:=$(subst $(eval) ,:,$(addprefix $(ROOT_DIR),$(PYTHON_SUBDIRS)))
# Can't use += to append to PYTHONPATH as that adds whitespace
PYTHONPATH:=$(PYTHONPATH):$(ROOT_DIR)pybdoc/python:$(ROOT_DIR)pybdoc/python/.libs:$(ROOT_DIR)pybdoc/src/.libs

PYTHON=python2.7
PYLINT=pylint -E
PYLINTRC=$(ROOT_DIR)common/pylintrc
PYLINT_OPTIONS=--rcfile="$(PYLINTRC)" *.py
RM=rm -f

PYCHECK=pychecker
PYCHECKRC=$(ROOT_DIR)common/pycheckrc
PYCHECK_OPTIONS=-F $(PYCHECKRC) -aqI6A --limit=40 --changetypes *.py

pyclean:
	$(RM) *.pyc *.pyo

objclean:
	$(RM) core *.o *~

test:
	for i in test_*; do env LD_LIBRARY_PATH="$(PYTHONPATH)" PYTHONPATH="$(PYTHONPATH)" ./$$i; done

check:
	env LD_LIBRARY_PATH="$(PYTHONPATH)" PYTHONPATH="$(PYTHONPATH)" IVOTE_TEST_RUN="1" $(PYLINT) $(PYLINT_OPTIONS)

checker:
	env LD_LIBRARY_PATH="$(PYTHONPATH)" PYTHONPATH="$(PYTHONPATH)" IVOTE_TEST_RUN="1" $(PYCHECK) $(PYCHECK_OPTIONS)

