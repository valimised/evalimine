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



#ifndef P11_H_INCLUDED
#define P11_H_INCLUDED

# include <stdio.h>

# include <vector>
# include <string>

# include "pkcs11.h"

void throwCKR(const std::string &prefix, CK_RV rc);

class PKCS11;
class Session;


typedef struct Slots {
	CK_SLOT_ID_PTR list;
	CK_ULONG count;
	CK_SLOT_ID current;
	Session *session;
} Slots;


class PKCS11 {

	public:

		PKCS11(const std::string &libname);

		virtual ~PKCS11();

		void init(bool threads = false);

		void login(const std::string &token, const std::string &pin);
		void logout();

		Session* getSession();

		void listInfo();

	protected:

		void getSlots(CK_BBOOL withtoken = CK_FALSE);

		void listMechanisms(CK_SLOT_ID sl);
		void listTokenInfo(CK_SLOT_ID sl);

	private:

		CK_FUNCTION_LIST_PTR _flist;
		void *_dso;
		bool _logged_in;
		Slots _slots;
};


class Session {

	public:

		virtual ~Session();

		void setCurrentPrivKey(const std::string &priv_key_label);
		void setCurrentPubKey(const std::string &pub_key_label);

		CK_ULONG getRSAModulusLen();

		std::string encrypt(const char *data, size_t len);
		std::string decrypt(
			const char *data,
			size_t len,
			CK_BYTE_PTR ctx,
			CK_ULONG_PTR ctx_len);

		std::string signit(const char *data, size_t len);

		void listObjects(FILE *out);
		void deleteObject(unsigned int onum);
		void deleteAllObjects();

		void genRSA(int bits, const std::string &label, unsigned char id);
		void exportRsaPrivKey(const std::string &pub_key_label,
			const std::string &priv_key_label, const char *output);

	protected:

		friend class PKCS11;

		void logout();
		void login(const std::string& pin);

		Session(CK_SESSION_HANDLE h, CK_FUNCTION_LIST_PTR fl);

	private:

		CK_FUNCTION_LIST_PTR _flist;
		CK_SESSION_HANDLE _session;
		std::vector<CK_OBJECT_HANDLE> _objects;

		CK_OBJECT_HANDLE _hpub;
		CK_OBJECT_HANDLE _hpriv;

		CK_BYTE_PTR _buffer;
};

#endif
