include rules.mk
# Let 'all' be the default goal, and not the first target from rules.mk
.DEFAULT_GOAL=

all:
	for i in $(PYTHON_SUBDIRS) ; \
	do \
		make -C $$i test; \
	done

pylint:
	for i in $(PYTHON_SUBDIRS) ; \
	do \
		make -C $$i check; \
	done

pycheck:
	for i in $(PYTHON_SUBDIRS) ; \
	do \
		make -C $$i checker; \
	done

ARCH:=$(shell dpkg-architecture -qDEB_HOST_ARCH)
debuild:
	debuild -i -I || echo "debuild $(ARCH)"
	./debian/repo.py ../evote-$(ARCH) .. $(ARCH)

deb: pybdoc/Makefile

	$(MAKE) -C pybdoc
	$(MAKE) -C common messages
	$(MAKE) -C hlr

clean: pybdoc/Makefile
	$(MAKE) -C pybdoc clean
	for i in $(PYTHON_SUBDIRS) ; \
	do \
		make -C $$i clean || exit 1; \
	done

distclean: pybdoc/Makefile
	$(MAKE) -C pybdoc distclean
	for i in $(PYTHON_SUBDIRS) ; \
	do \
		make -C $$i clean || exit 1; \
	done

pybdoc/Makefile:
	$(MAKE) -C pybdoc -f Makeall
