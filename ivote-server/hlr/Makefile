CXX = g++
CXXFLAGS = -Wall
LDLIBS = -lcrypto -ldl

PROGRAMS = threaded_decrypt

all: $(PROGRAMS)

include ../rules.mk

threaded_decrypt: threaded_decrypt.o base64.o count_lines.o p11.o progress_bar.o
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $+ $(LDLIBS) -lpthread

clean: pyclean objclean
	$(RM) $(PROGRAMS) .depend

dep: .depend

.depend: *.cpp *.h Makefile
	$(CXX) -MM *.cpp > .depend

-include .depend
