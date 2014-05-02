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


#ifndef THREADED_DECRYPT_H
#define THREADED_DECRYPT_H

class Boss;
class Worker;

class Boss
{
	public:

		Boss(const std::string& input, const std::string& output, PKCS11 *p, const std::string& label);
		~Boss();

		void preparePKCS11(const std::string& token, const std::string& pin);
		void cleanupPKCS11();
		Session* getSession();

		void prepareWork();

		int getTask(std::string& task, std::string& context);

		void setResult(const std::string& result, const std::string& context, int no);

		const std::string& label() const;

	protected:

	private:

		std::map<int, std::string> _cache;
		int _last_saved;

		std::string _in;
		std::string _out;
		std::string _label;
		PKCS11 *_p;
		FILE *_fin;
		FILE *_fout;

		ProgressBar *_pc;

		int _line_nr;
};

class Worker
{
	public:

		Worker(Session *s);
		~Worker();

		void init(const std::string& label);

		std::string solveTask(const std::string& task, Base64 &base64);

	protected:

	private:

		CK_BYTE_PTR _ctx;
		CK_ULONG _ctx_len;
		Session *_sess;

};

#endif
