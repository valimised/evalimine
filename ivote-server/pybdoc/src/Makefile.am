SUBDIRS = xml crypto

AM_CXXFLAGS = -Wall -Wextra -Werror -g -O0

lib_LTLIBRARIES = libbdoc.la

libbdoc_la_SOURCES = BDoc.cpp CallStack.cpp ChallengeVerifierImpl.cpp DateTime.cpp PyBDoc.cpp Signature.cpp StackException.cpp XMLHelper.cpp

libbdoc_la_LIBADD = crypto/libbdoccrypto.la xml/libbdocxml.la -lxerces-c \
	-lxml-security-c -lcrypto -lssl -ldl
