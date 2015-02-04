/*
 * Copyright: Eesti Vabariigi Valimiskomisjon
 * (Estonian National Electoral Committee), www.vvk.ee
 * Written in 2004-2014 by Cybernetica AS, www.cyber.ee
 *
 * This work is licensed under the Creative Commons
 * Attribution-NonCommercial-NoDerivs 3.0 Unported License.
 * To view a copy of this license, visit
 * http://creativecommons.org/licenses/by-nc-nd/3.0/.
 * */

#include <iostream>
#include <fstream>

#include "pkcs11.h"
#include "p11.h"

enum ExitCodes {
	EXIT_OK = 0,
	EXIT_INVALID_ARGUMENT_COUNT,
	EXIT_CANNOT_OPEN_INPUT,
	EXIT_CANNOT_OPEN_OUTPUT,
	EXIT_ERROR_READING_INPUT,
	EXIT_ERROR_WRITING_OUTPUT,
	EXIT_SIGN_UTIL_FAILED
};


void usage(const char *self)
{
	printf("Kasutamine:\n");
	printf("	%s <input file> <output file> <token name> "
		   "<priv key label> <PIN> <PKCS11 lib>\n", self);
}

int main(int argc, char **argv)
{
	if (argc != 7) {
		usage(argv[0]);
		return EXIT_INVALID_ARGUMENT_COUNT;
	}

	int ret = EXIT_OK;

	std::string inf = std::string(argv[1]);
	std::string outf = std::string(argv[2]);
	std::string token = std::string(argv[3]);
	std::string label = std::string(argv[4]);
	std::string pin = std::string(argv[5]);
	std::string lib = std::string(argv[6]);

	char *memblock = NULL;
	std::streampos size;
	PKCS11 *p11 = NULL;
	Session *sess = NULL;
	try {

		std::ifstream infile(inf.c_str(), std::ios::in | std::ios::binary | std::ios::ate);
		if (infile.is_open()) {
			size = infile.tellg();
			memblock = new char[size];
			infile.seekg(0, std::ios::beg);
			infile.read(memblock, size);
			infile.close();
		}
		else {
			return EXIT_CANNOT_OPEN_INPUT;
		}

		p11 = new PKCS11(lib);
		p11->init(false);
		p11->login(token, pin);
		sess = p11->getSession();
		sess->setCurrentPrivKey(label);

		std::string signature = sess->signit(memblock, size);
		delete [] memblock;

		std::ofstream outfile(outf.c_str(), std::ios::out | std::ios::binary | std::ios::ate);
		if (outfile.is_open()) {
			outfile.write(signature.data(), signature.length());
			outfile.close();
		}
		else {
			return EXIT_CANNOT_OPEN_OUTPUT;
		}

		p11->logout();
		delete p11;
		p11 = NULL;
	}
	catch (std::exception &e) {
		fprintf(stderr, "Exception caught: %s\n", e.what());
		return EXIT_SIGN_UTIL_FAILED;
	}
	catch (...) {
		fprintf(stderr, "Unknown exception caught\n");
		return EXIT_SIGN_UTIL_FAILED;
	}

	return ret;
}

