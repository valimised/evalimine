#include <string>
#include <fstream>
#include <cstdio>
#include <stdexcept>
#include <iostream>
#include <sys/types.h>
#include <dirent.h>
#include "PyBDoc.h"

using std::string;

struct InitPyBDOC {
	InitPyBDOC() {
		initialize();
	}

	~InitPyBDOC() {
		terminate();
	}
};

static string read(const char *fn)
{
	std::ifstream in(fn);
	return string(std::istreambuf_iterator<char>(in),
	              std::istreambuf_iterator<char>());
}

static void show(const BDocVerifierResult& r)
{
	std::cout << "result: " << r.result
		<< "\ncert_is_valid: " << r.cert_is_valid
		<< "\nocsp_is_good: " << r.ocsp_is_good
		<< "\nsubject: " << r.subject
		<< "\nocsp_time: " << r.ocsp_time
		<< "\nerror: " << r.error
		<< "\nsignature: " << r.signature
		<< std::endl;
}

static void addCertDir(BDocVerifier &bdoc, const char *directory)
{
	DIR *dir = opendir(directory);
	dirent *entry;

	while ((entry = readdir(dir))) {
		string filename(entry->d_name);
		if (filename.size() < 5 || filename[0] == '.' ||
		    filename.substr(filename.size() - 4) != ".crt") {
			std::cerr << "Ignoring: " << filename << std::endl;
		} else {
			string path(string(directory) + '/' + filename);
			std::cerr << "Adding certificate: " << path << std::endl;
			bdoc.addCertToStore(path.c_str());
		}
	}
	closedir(dir);
}

int pybdoc_test_main(int argc, char **argv) {
	InitPyBDOC init;
	BDocVerifier bdoc;
	string document;

	try {
		for (int i = 1; i < argc - 1; ++i) {
			string arg = argv[i];
			if (arg == "-schema") {
				bdoc.setSchemaDir(argv[++i]);
			} else if (arg == "-cert") {
				bdoc.addCertToStore(argv[++i]);
			} else if (arg == "-certdir") {
				addCertDir(bdoc, argv[++i]);
			} else if (arg == "-digest") {
				bdoc.setDigestURI(argv[++i]);
			} else if (arg == "-doc") {
				if (argc - i < 2) {
					fprintf(stderr, "-doc path name");
					return 2;
				}
				document = read(argv[++i]);
				bdoc.setDocument((const unsigned char*) document.data(),
								 document.size(), argv[++i]);
			} else if (arg == "-verifyOffline") {
				string xml = read(argv[++i]);
				show(bdoc.verifyBESOffline(xml.c_str(), xml.size()));
			} else if (arg == "-verifyOnline") {
				string xml = read(argv[++i]);
				show(bdoc.verifyInHTS(xml.c_str(), xml.size()));
			} else if (arg == "-verifyTM") {
				string xml = read(argv[++i]);
				show(bdoc.verifyTMOffline(xml.c_str(), xml.size()));
			} else {
				fprintf(stderr, "Unknown option: %s\n", argv[i]);
				return 2;
			}
		}
	} catch (std::exception& ex) {
		fprintf(stderr, "Exception: %s\n", ex.what());
		return 1;
	}
	return 0;
}
