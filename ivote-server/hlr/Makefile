CXX = g++
CXXFLAGS = -Wall
LDLIBS = -lcrypto -ldl

PROGRAMS = sign_data threaded_decrypt

all: $(PROGRAMS)

include ../rules.mk

threaded_decrypt: threaded_decrypt.o base64.o count_lines.o p11.o progress_bar.o
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $+ $(LDLIBS) -lpthread


sign_data: sign_data.o p11.o
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $+ $(LDLIBS)

clean: pyclean objclean
	$(RM) $(PROGRAMS) .depend

dep: .depend

.depend: *.cpp *.h Makefile
	$(CXX) -MM *.cpp > .depend

-include .depend
