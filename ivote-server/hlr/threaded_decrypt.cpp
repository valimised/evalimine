/*
 * Copyright: Eesti Vabariigi Valimiskomisjon
 * (Estonian National Electoral Committee), www.vvk.ee
 * Written in 2004-2013 by Cybernetica AS, www.cyber.ee
 *
 * This work is licensed under the Creative Commons
 * Attribution-NonCommercial-NoDerivs 3.0 Unported License.
 * To view a copy of this license, visit
 * http://creativecommons.org/licenses/by-nc-nd/3.0/.
 * */


#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <map>
#include <vector>
#include <stdexcept>
#include <assert.h>

#include "pkcs11.h"
#include "base64.h"
#include "p11.h"
#include "progress_bar.h"
#include "count_lines.h"
#include "threaded_decrypt.h"

enum ExitCodes {
	EXIT_OK = 0,
	EXIT_INVALID_ARGUMENT_COUNT,
	EXIT_CANNOT_OPEN_VOTES_FILE_FOR_READING,
	EXIT_CANNOT_OPEN_DECRYPTED_VOTES_FILE_FOR_WRITING,
	EXIT_INVALID_VOTES_FILE_FORMAT_NO_VERSION_NUMBER,
	EXIT_INVALID_VOTES_FILE_FORMAT_NO_IDENTIFICATOR,
	EXIT_ERROR_READING_INPUT,
	EXIT_ERROR_WRITING_OUTPUT,
	EXIT_INVALID_VOTES_FILE_LINE_FORMAT,
	EXIT_DECRYPT_UTIL_FAILED
};


#define CORRUPTED_VOTE "xxx"

#define LINE_MAX_LEN (172 * 1024 + 2)

#define MAX_THREADS 9

pthread_mutex_t boss_mutex;

Boss *boss = NULL;

/*
 *
 * Class Boss
 *
 * */

Boss::Boss(const std::string& input, const std::string& output, PKCS11 *p, const std::string& label)
{
	_in = input;
	_out = output;
	_p = p;
	_label = label;

	_line_nr = 0;
	_last_saved = 0;

	_fin = NULL;
	_fout = NULL;

	_pc = NULL;
}

Boss::~Boss()
{
	fclose(_fout);
	fclose(_fin);
	delete _pc;
}

const std::string& Boss::label() const
{
	return _label;
}

int Boss::getTask(std::string& task, std::string& context)
{
	char line[LINE_MAX_LEN];
	if (fgets(line, LINE_MAX_LEN, _fin) != NULL) {

		char *index = strrchr(line, '\t');
		_line_nr++;

		if (index == NULL) {
			fprintf(stderr, "Invalid vote line format: line nr %d\n",
					_line_nr);
			exit(EXIT_INVALID_VOTES_FILE_LINE_FORMAT);
		}
		index++;

		task = std::string(index);
		context = std::string(line, strlen(line) - 1);

#ifdef WITHOUT_PKCS11
		fprintf(stderr, "\nINPUT: %s", line);
		fprintf(stderr, "TASK: %s", task.c_str());
		fprintf(stderr, "CONTEXT: %s\n\n", context.c_str());
#endif
		return _line_nr;
	}

	if (ferror(_fin)) {
		fprintf(stderr, "Error reading input: %s\n", strerror(errno));
		exit(EXIT_ERROR_READING_INPUT);
	}

	return -1;
}

void Boss::setResult(const std::string& result, const std::string& context, int no)
{
	std::string decrypted_line = context + "\t" + result + "\n";

	if (no == _last_saved + 1) {
		if (fputs(decrypted_line.c_str(), _fout) == EOF) {
			fprintf(stderr, "Error writing output: %s\n", strerror(errno));
			exit(EXIT_ERROR_WRITING_OUTPUT);
		}
		_last_saved++;

		while (!_cache.empty()) {
			if (_cache.count(_last_saved + 1) > 0) {
				if (fputs(_cache[_last_saved + 1].c_str(), _fout) == EOF) {
					fprintf(stderr, "Error writing output: %s\n", strerror(errno));
					exit(EXIT_ERROR_WRITING_OUTPUT);
				}
				_cache.erase(_last_saved + 1);
				_last_saved++;
			}
			else {
				break;
			}
		}
	}
	else {
		assert(_cache.count(no) == 0);
		_cache[no] = decrypted_line;
	}

	_pc->next("Dekrüpteerin hääli");

}


void Boss::prepareWork()
{
	char line[LINE_MAX_LEN];
	int lines = countLines(_in.c_str());
	if (lines < 0) {
		fprintf(stderr, "Error reading input: %s\n", strerror(errno));
		exit(EXIT_ERROR_READING_INPUT);
	}
	else {
		if (lines == 0) {
			exit(EXIT_INVALID_VOTES_FILE_FORMAT_NO_VERSION_NUMBER);
		}
		if (lines == 1) {
			exit(EXIT_INVALID_VOTES_FILE_FORMAT_NO_IDENTIFICATOR);
		}
	}

	_pc = new ProgressBar(lines);

	_fin = fopen(_in.c_str(), "r");
	if (_fin == NULL) {
		exit(EXIT_CANNOT_OPEN_VOTES_FILE_FOR_READING);
	}
	_fout = fopen(_out.c_str(), "w");
	if (_fout  == NULL) {
		exit(EXIT_CANNOT_OPEN_DECRYPTED_VOTES_FILE_FOR_WRITING);
	}

	if (fgets(line, LINE_MAX_LEN, _fin) == NULL) {
		exit(EXIT_INVALID_VOTES_FILE_FORMAT_NO_VERSION_NUMBER);
	}
	fputs(line, _fout);

	if (fgets(line, LINE_MAX_LEN, _fin) == NULL) {
		exit(EXIT_INVALID_VOTES_FILE_FORMAT_NO_IDENTIFICATOR);
	}
	fputs(line, _fout);

	_line_nr = 2;
	_last_saved = 2;
}

Session* Boss::getSession()
{
#ifndef WITHOUT_PKCS11
	return _p->getSession();
#else
	return NULL;
#endif
}

void Boss::preparePKCS11(const std::string& token, const std::string& pin)
{
#ifndef WITHOUT_PKCS11
	_p->init(true);
	_p->login(token, pin);
#endif
}

void Boss::cleanupPKCS11()
{
#ifndef WITHOUT_PKCS11
	_p->logout();
	_p = NULL;
#endif
}

/*
 *
 * Class Worker
 *
 * */

Worker::Worker(Session *s)
{
	_sess = s;
	_ctx = NULL;
	_ctx_len = 0;
}

Worker::~Worker()
{
	free(_ctx);
}

void Worker::init(const std::string& label)
{
#ifndef WITHOUT_PKCS11
	_sess->setCurrentPrivKey(label);
	_ctx_len = _sess->getRSAModulusLen();

	_ctx = (CK_BYTE_PTR)malloc(_ctx_len);
	if (_ctx == NULL) {
		throw std::bad_alloc();
	}
#endif
}

std::string Worker::solveTask(const std::string& task, Base64 &base64)
{
	struct buffer_st buf;
	base64.decode(&buf, task.c_str(), task.length());

	std::string decrypted_vote;

#ifndef WITHOUT_PKCS11
	try {
		CK_ULONG tmp_len = _ctx_len;
		decrypted_vote = _sess->decrypt(buf.data, buf.offset, _ctx, &tmp_len);
	}
	catch (std::exception &e) {
		fprintf(stderr, "Vote decryption failed: %s\n", e.what());
		// Kui hääle dekrüptimine ei õnnestunud, siis paneme "xxx"
		// hääle asemele, mis kindlasti feilib ja läheb Log4.
		decrypted_vote = CORRUPTED_VOTE;
	}
#else
	decrypted_vote = "WITHOUTPKCS11";
#endif

	struct buffer_st buf2;
	base64.encode(&buf2, decrypted_vote.c_str(),
				  decrypted_vote.length(), true);

	std::string ret(buf2.data, buf2.offset);

	buffer_delete(&buf);
	buffer_delete(&buf2);
	return ret;
}

void *threadMain(void *t)
{
	int *ret = new int;
	try {
		pthread_mutex_lock(&boss_mutex);
		Session *sess = boss->getSession();
		pthread_mutex_unlock(&boss_mutex);

		Worker *w = new Worker(sess);

		w->init(boss->label());

		std::string task;
		std::string ctx;
		int no;
		Base64 base64;

		while (true) {
			pthread_mutex_lock(&boss_mutex);
			no = boss->getTask(task, ctx);
			pthread_mutex_unlock(&boss_mutex);

			if (no > -1) {
				std::string res = w->solveTask(task, base64);
				pthread_mutex_lock(&boss_mutex);
				boss->setResult(res, ctx, no);
				pthread_mutex_unlock(&boss_mutex);
			}
			else {
				break;
			}
		}

		delete w;
		delete sess;
		*ret = 0;
	}
	catch (std::exception& e) {
		*ret = -1;
		fprintf(stderr, "Exception caught: %s\n", e.what());
	}
	catch (...) {
		*ret = -1;
		fprintf(stderr, "Unknown exception caught\n");
	}

	pthread_exit(ret);
}

int createThreads(int num)
{
	assert(num <= MAX_THREADS);
	pthread_t threads[MAX_THREADS];
	pthread_attr_t attr;
	int *status = NULL;
	int ret = 1;

	pthread_attr_init(&attr);
	pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);

	for (long t = 0; t < num; t++) {
		int rc = pthread_create(&threads[t], &attr, threadMain, (void *)t);
		if (rc) {
			printf("ERROR; return code from pthread_create() is %d\n", rc);
			return -1;
		}
	}

	pthread_attr_destroy(&attr);

	for (int t = 0; t < num; t++) {
		pthread_join(threads[t], (void **)&status);
		if (*status == -1) {
			ret = -1;
		}
	}

	return ret;
}

void usage(const char *self)
{
	printf("Kasutamine:\n");
	printf("    %s <input file> <output file> <token name> "
		   "<priv key label> <PIN> <PKCS11 lib>\n", self);
}

int main(int argc, char **argv)
{
	if (argc != 7) {
		usage(argv[0]);
		return EXIT_INVALID_ARGUMENT_COUNT;
	}

	int ret = EXIT_OK;

	pthread_mutex_init(&boss_mutex, NULL);

	try {
		PKCS11 *p11 = NULL;
#ifndef WITHOUT_PKCS11
		p11 = new PKCS11(argv[6]);
#endif
		boss = new Boss(argv[1], argv[2], p11, argv[4]);
		boss->preparePKCS11(argv[3], argv[5]);
		boss->prepareWork();

		if (createThreads(MAX_THREADS) == -1) {
			ret = EXIT_DECRYPT_UTIL_FAILED;
		}

		boss->cleanupPKCS11();
        delete p11;
	}
	catch (std::exception &e) {
		fprintf(stderr, "Exception caught: %s\n", e.what());
		return EXIT_DECRYPT_UTIL_FAILED;
	}
	catch (...) {
		fprintf(stderr, "Unknown exception caught\n");
		return EXIT_DECRYPT_UTIL_FAILED;
	}

	pthread_mutex_destroy(&boss_mutex);
//	pthread_exit(NULL);

	return ret;
}

