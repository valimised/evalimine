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

#include "p11.h"

#include <stdexcept>

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <ctype.h>
#include <dlfcn.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>

#include <openssl/rsa.h>
#include <openssl/bn.h>
#include <openssl/pem.h>

static struct {
	CK_RV rc;
	const char *desc;
} known_pkcs11_return_codes[] = {
	{ CKR_OK, "Success" },
	{ CKR_CANCEL, "Callback has returned CKR_CANCEL" },
	{ CKR_HOST_MEMORY, "Insufficient memory to perform requested operation" },
	{ CKR_SESSION_READ_ONLY, "Session is read-only" },
	{ CKR_DEVICE_ERROR, "Device-error" },
	{ 0, 0 }
};


void throwCKR(const std::string &prefix, CK_RV rc)
{
	char buf[64];
	std::string s(prefix);

	snprintf(buf, sizeof(buf), ": 0x%lx", rc);
	s += buf;

	for (int i = 0; known_pkcs11_return_codes[i].desc; ++i) {
		if (known_pkcs11_return_codes[i].rc == rc) {
			s += " (";
			s += known_pkcs11_return_codes[i].desc;
			s += ")";
			break;
		}
	}

	throw std::runtime_error(s);
}

/*
 *
 * Class PKCS11
 *
 * */

PKCS11::PKCS11(const std::string &libname)
{
	_logged_in = false;
	_slots.list = NULL_PTR;
	_slots.count = 0;
	_slots.session = NULL;
	_flist = NULL_PTR;
	_dso = NULL;

	_dso = dlopen(libname.c_str(), RTLD_LAZY);
	if (_dso == 0) {
		const char *errstr = dlerror();
		if (errstr == 0) {
			errstr = "No error returned by dlerror()???";
		}
		throw std::runtime_error(std::string("dlopen() failed: ") 
						+ errstr);
	}
	CK_C_GetFunctionList gfl =
		(CK_C_GetFunctionList) dlsym(_dso, "C_GetFunctionList");
	if (gfl == 0) {
		const char *errstr = dlerror();
		if (errstr == 0) {
			errstr = "Expected symbol is NULL pointer";
		}
		throw std::runtime_error(std::string("dlsym() failed: ") 
						+ errstr);
	}
	CK_RV rc = gfl(&_flist);
	if (rc != CKR_OK) {
		_flist = NULL_PTR;
		throwCKR("C_GetFunctionList() failed", rc);
	}
}

PKCS11::~PKCS11()
{
	if (_flist != NULL_PTR) {
		CK_RV rc = _flist->C_Finalize(NULL_PTR);
		if (rc != CKR_OK) {
			fprintf(stderr,
				"Warning: C_Finalize() returned non-OK value: 0x%lx\n", rc);
		}
	}

	free(_slots.list);

	if (_dso) {
		dlclose(_dso);
	}
}


void PKCS11::init(bool threads)
{
	CK_C_INITIALIZE_ARGS args;
	CK_C_INITIALIZE_ARGS_PTR pArgs = NULL_PTR;

	if (threads) {
		args.CreateMutex = NULL_PTR;
		args.DestroyMutex = NULL_PTR;
		args.LockMutex = NULL_PTR;
		args.UnlockMutex = NULL_PTR;
		args.flags = CKF_OS_LOCKING_OK;
		args.pReserved = NULL_PTR;
		pArgs = &args;
	}

	CK_RV rc = _flist->C_Initialize(pArgs);
	if (rc != CKR_OK) {
		_flist = NULL_PTR;
		throwCKR("C_Initialize() failed", rc);
	}
}

void PKCS11::logout()
{
	if (_slots.session != NULL) {
		if (_logged_in) {
			_logged_in = false;
			_slots.session->logout();
		}

		delete _slots.session;
		_slots.session = NULL;

		CK_RV rc = _flist->C_CloseAllSessions(_slots.current);
		if (rc != CKR_OK) {
			throwCKR("C_CloseAllSessions() failed", rc);
		}
	}
}

Session* PKCS11::getSession()
{
	CK_SESSION_HANDLE h;
	CK_RV rc = _flist->C_OpenSession(_slots.current,
		CKF_SERIAL_SESSION | CKF_RW_SESSION,
		NULL_PTR, NULL_PTR, &h);

	if (rc != CKR_OK) {
		throwCKR("C_OpenSession() failed", rc);
	}

	return new Session(h, _flist);
}

void PKCS11::login(const std::string &token, const std::string &pin)
{
	CK_RV rc;
	CK_TOKEN_INFO tinfo;
	CK_SLOT_ID slot;
	bool slot_found = false;
	char label[32];

	// Do nothing if no token name.
	if (token.size() < 1) {
		return;
	}

	getSlots(CK_TRUE);

	memset(label, ' ', 32);
	strncpy(label, (token + std::string(label, 32)).c_str(), 32);
	for (CK_ULONG i = 0; i < _slots.count; ++i) {
		rc = _flist->C_GetTokenInfo(_slots.list[i], &tinfo);
		if (rc != CKR_OK) {
			throwCKR("C_GetTokenInfo() failed", rc);
		}
		if (memcmp(label, tinfo.label, 32) == 0) {
			slot = _slots.list[i];
			slot_found = true;
			break;
		}
	}
	if (!slot_found) {
		throw std::runtime_error("Requested token cannot be found");
	}

	_slots.current = slot;
	_slots.session = getSession();
	_slots.session->login(pin);
	_logged_in = true;
}

void PKCS11::getSlots(CK_BBOOL withtoken)
{
	if (_slots.list == NULL_PTR) {
		CK_RV rc = _flist->C_GetSlotList(
				withtoken, NULL_PTR, &_slots.count);
		if (rc != CKR_OK) {
			throwCKR("C_GetSlotList() failed", rc);
		}

		if (_slots.count > 0) {
			_slots.list = (CK_SLOT_ID_PTR)malloc(
					_slots.count * sizeof(CK_SLOT_ID));
			if (_slots.list == NULL_PTR) {
				throw std::bad_alloc();
			}

			rc = _flist->C_GetSlotList(withtoken,
						_slots.list, &_slots.count);
			if (rc != CKR_OK) {
				throwCKR("C_GetSlotList() failed", rc);
			}
		}
	}
}

void PKCS11::listInfo()
{
	CK_INFO cinfo;
	CK_RV rc = _flist->C_GetInfo(&cinfo);
	if (rc != CKR_OK) {
		throwCKR("C_GetSlotList() failed", rc);
	}

	printf("C_GetInfo:  \n"
		   "\tCryptoki ver: \"%d.%d\"\n"
		   "\tManufacturer: \"%.32s\"\n"
		   "\tDescription:  \"%.32s\"\n"
		   "\tLibrary ver:  \"%d.%d\"\n",
		   cinfo.cryptokiVersion.major, cinfo.cryptokiVersion.minor,
		   cinfo.manufacturerID,
		   cinfo.libraryDescription,
		   cinfo.libraryVersion.major, cinfo.libraryVersion.minor);

	getSlots();

	printf("Slots count: %ld\n", _slots.count);

	for (CK_ULONG i = 0; i < _slots.count; ++i) {
		printf("Slot %ld info:\n", _slots.list[i]);
		CK_SLOT_INFO sinfo;
		rc = _flist->C_GetSlotInfo(_slots.list[i], &sinfo);
		if (rc != CKR_OK) {
			throwCKR("C_GetSlotInfo() failed", rc);
		}

		printf("\tDescription:  \"%.64s\"\n"
			"\tManufacturer: \"%.32s\"\n"
			"\tHardware ver: \"%d.%d\"\n"
			"\tFirmware ver: \"%d.%d\"\n",
			sinfo.slotDescription, sinfo.manufacturerID,
			sinfo.hardwareVersion.major,
			sinfo.hardwareVersion.minor,
			sinfo.firmwareVersion.major,
			sinfo.firmwareVersion.minor);

		if (sinfo.flags & CKF_REMOVABLE_DEVICE) {
			printf("\tRemovable device\n");
		}

		if (sinfo.flags & CKF_HW_SLOT) {
			printf("\tHardware slot\n");
		}

		if (sinfo.flags & CKF_TOKEN_PRESENT) {
			listTokenInfo(_slots.list[i]);
		}
		listMechanisms(_slots.list[i]);
	}
}

void PKCS11::listTokenInfo(CK_SLOT_ID sl)
{
	printf("\tToken present:\n");
	CK_TOKEN_INFO tinfo;
	CK_RV rc = _flist->C_GetTokenInfo(sl, &tinfo);
	if (rc != CKR_OK) {
		throwCKR("C_GetTokenInfo() failed", rc);
	}
	printf("\t\tLabel:  \"%.32s\"\n"
		   "\t\tManufacturer: \"%.32s\"\n"
		   "\t\tModel: \"%.16s\"\n"
		   "\t\tSerial: \"%.16s\"\n",
		   tinfo.label, tinfo.manufacturerID,
		   tinfo.model, tinfo.serialNumber);

	printf("\t\tUnavailable info:\"%ld\"\n", CK_UNAVAILABLE_INFORMATION);
	printf("\t\tEffectively infinite:\"%d\"\n", CK_EFFECTIVELY_INFINITE);
	printf("\t\tMax sessions:\"%ld\"\n", tinfo.ulMaxSessionCount);
	printf("\t\tCurrent sessions:\"%ld\"\n", tinfo.ulSessionCount);
	printf("\t\tMax RW sessions:\"%ld\"\n", tinfo.ulMaxRwSessionCount);
	printf("\t\tCurrent RW sessions:\"%ld\"\n", tinfo.ulRwSessionCount);
	printf("\t\tMax PIN length:\"%ld\"\n", tinfo.ulMaxPinLen);
	printf("\t\tMin PIN length:\"%ld\"\n", tinfo.ulMinPinLen);
	printf("\t\tTotal public mem:\"%ld\"\n", tinfo.ulTotalPublicMemory);
	printf("\t\tFree public mem:\"%ld\"\n", tinfo.ulFreePublicMemory);
	printf("\t\tTotal private mem:\"%ld\"\n", tinfo.ulTotalPrivateMemory);
	printf("\t\tFree private mem:\"%ld\"\n", tinfo.ulFreePrivateMemory);
	printf("\t\tHardware ver: \"%d.%d\"\n\t\tFirmware ver: \"%d.%d\"\n",
		   tinfo.hardwareVersion.major, tinfo.hardwareVersion.minor, 
		   tinfo.firmwareVersion.major, tinfo.firmwareVersion.minor);
	printf("\t\tTime:  \"%.16s\"\n", tinfo.utcTime);

	if (tinfo.flags & CKF_LOGIN_REQUIRED) {
		printf("\t\tLogin required\n");
	}

	if (tinfo.flags & CKF_TOKEN_INITIALIZED) {
		printf("\t\tToken initialized\n");
	}

	if (tinfo.flags & CKF_RNG) {
		printf("\t\tHas RNG\n");
	}
}

void PKCS11::listMechanisms(CK_SLOT_ID sl)
{
	printf("Available mechanisms:\n");
	CK_ULONG mechCnt = 0;
	CK_RV rc = _flist->C_GetMechanismList(sl, NULL, &mechCnt);
	if (rc != CKR_OK) {
		throwCKR("C_GetMechanismList() failed", rc);
	}

	if (mechCnt > 0) {
		CK_MECHANISM_TYPE_PTR pMechanismList = NULL;
		pMechanismList = (CK_MECHANISM_TYPE_PTR)malloc(
					mechCnt * sizeof(CK_MECHANISM_TYPE));
		rc = _flist->C_GetMechanismList(sl, pMechanismList, &mechCnt);
		if (rc != CKR_OK) {
			throwCKR("C_GetMechanismList() failed", rc);
		}
		for (CK_ULONG j = 0; j < mechCnt; j++) {
			printf("0x%lx\n", pMechanismList[j]);
		}
		free(pMechanismList);
	}
	else {
		printf("No mechanisms available\n");
	}
}

/*
 *
 * Class Session
 *
 * */


Session::Session(CK_SESSION_HANDLE h, CK_FUNCTION_LIST_PTR fl)
{
	_hpub = NULL_PTR;
	_hpriv = NULL_PTR;
	_session = h;
	_flist = fl;
	_buffer = NULL_PTR;
}

Session::~Session()
{
	free(_buffer);
}

void Session::logout()
{
	CK_RV rc = _flist->C_Logout(_session);
	if (rc != CKR_OK) {
		throwCKR("C_Logout() failed", rc);
	}
}

void Session::login(const std::string& pin)
{
	CK_RV rc = _flist->C_Login(_session, CKU_USER, (CK_CHAR_PTR) pin.c_str(),
			pin.length());
	if (rc != CKR_OK) {
		throwCKR("C_Login() failed", rc);
	}
}

void Session::setCurrentPrivKey(const std::string &priv_key_label)
{
	CK_RV rc;
	CK_ULONG ulObjectCount;

	CK_OBJECT_CLASS keyClass = CKO_PRIVATE_KEY;
	CK_KEY_TYPE keyTypeRsa = CKK_RSA;
	CK_BBOOL True = TRUE;

	CK_ATTRIBUTE rsaTemplate[] = {
		{CKA_CLASS, &keyClass, sizeof(keyClass)},
		{CKA_TOKEN, &True, 1},
		{CKA_KEY_TYPE, &keyTypeRsa, sizeof(keyTypeRsa)},
		{CKA_LABEL, (CK_BYTE_PTR)priv_key_label.c_str(),
			priv_key_label.length()}
	};

	CK_ULONG rsa_tmpl_size = sizeof(rsaTemplate) / sizeof(CK_ATTRIBUTE);

	rc = _flist->C_FindObjectsInit(_session, rsaTemplate, rsa_tmpl_size);
	if (rc != CKR_OK) {
		throwCKR("C_FindObjectsInit() failed", rc);
	}

	rc = _flist->C_FindObjects(_session, &_hpriv, 1, &ulObjectCount);
	if (rc != CKR_OK) {
		throwCKR("C_FindObjects() failed", rc);
	}

	if (ulObjectCount == 0) {
		throw std::runtime_error("Requested private key cannot be found");
	}

	rc = _flist->C_FindObjectsFinal(_session);
	if (rc != CKR_OK) {
		throwCKR("C_FindObjectsFinal() failed", rc);
	}
}

void Session::setCurrentPubKey(const std::string &pub_key_label)
{
	CK_RV rc;
	CK_ULONG ulObjectCount;

	CK_OBJECT_CLASS keyClass = CKO_PUBLIC_KEY;
	CK_KEY_TYPE keyTypeRsa = CKK_RSA;
	CK_BBOOL True = TRUE;

	CK_ATTRIBUTE rsaTemplate[] = {
		{CKA_CLASS, &keyClass, sizeof(keyClass)},
		{CKA_TOKEN, &True, 1},
		{CKA_KEY_TYPE, &keyTypeRsa, sizeof(keyTypeRsa)},
		{CKA_LABEL, (CK_BYTE_PTR)pub_key_label.c_str(),
			pub_key_label.length()}
	};

	CK_ULONG rsa_tmpl_size = sizeof(rsaTemplate) / sizeof(CK_ATTRIBUTE);

	rc = _flist->C_FindObjectsInit(_session, rsaTemplate, rsa_tmpl_size);
	if (rc != CKR_OK) {
		throwCKR("C_FindObjectsInit() failed", rc);
	}

	rc = _flist->C_FindObjects(_session, &_hpub, 1, &ulObjectCount);
	if (rc != CKR_OK) {
		throwCKR("C_FindObjects() failed", rc);
	}

	if (ulObjectCount == 0) {
		throw std::runtime_error("Requested public key cannot be found");
	}

	rc = _flist->C_FindObjectsFinal(_session);
	if (rc != CKR_OK) {
		throwCKR("C_FindObjectsFinal() failed", rc);
	}
}

CK_ULONG Session::getRSAModulusLen()
{
	CK_OBJECT_HANDLE obj = NULL_PTR;

	if (_hpub != NULL_PTR) {
		obj = _hpub;
	}
	else if (_hpriv != NULL_PTR) {
		obj = _hpriv;
	}
	else {
		throw std::runtime_error("Keys are not initialized!");
	}

	CK_ULONG modulus_bits = 0;

	CK_ATTRIBUTE templ[] = {
		{CKA_MODULUS_BITS, &modulus_bits, sizeof(modulus_bits)}
	};

	CK_RV rc = _flist->C_GetAttributeValue(_session, obj, templ, 1);
	if (rc != CKR_OK) {
		throwCKR("C_GetAttributeValue() failed", rc);
	}

	return modulus_bits;
}

std::string Session::encrypt(const char *data, size_t len)
{
	std::string ret;

	CK_RV rc;
	CK_BYTE_PTR encrypted_data;
	CK_ULONG encrypted_len;

	CK_RSA_PKCS_OAEP_PARAMS params = {
		CKM_SHA_1,
		CKG_MGF1_SHA1,
		CKZ_DATA_SPECIFIED,
		NULL_PTR,
		0
	};

	CK_MECHANISM mechanism = {
		CKM_RSA_PKCS_OAEP, &params, sizeof(params)
	};


	if (_hpub == NULL_PTR) {
		throw std::runtime_error("Public key == NULL");
	}

	rc = _flist->C_EncryptInit(_session, &mechanism, _hpub);
	if (rc != CKR_OK) {
		throwCKR("C_EncryptInit() failed", rc);
	}

	rc = _flist->C_Encrypt(_session, (CK_BYTE_PTR)data, len,
			NULL, &encrypted_len);
	if (rc != CKR_OK) {
		throwCKR("C_Encrypt() failed", rc);
	}

	encrypted_data = NULL;
	encrypted_data = (CK_BYTE_PTR) malloc(encrypted_len);
	rc = _flist->C_Encrypt(_session, (CK_BYTE_PTR)data, len,
			encrypted_data, &encrypted_len);
	if (rc != CKR_OK) {
		throwCKR("C_Encrypt() failed", rc);
	}

	ret = std::string((char *)encrypted_data, encrypted_len);
	delete encrypted_data;
	encrypted_data = NULL;

	return ret;
}

std::string Session::signit(const char *data, size_t len)
{
	std::string ret;

	CK_RV rc;
	CK_BYTE_PTR signed_data = NULL;
	CK_ULONG signed_len;


	CK_MECHANISM mechanism = {
		CKM_SHA1_RSA_PKCS, NULL_PTR, 0
	};


	if (_hpriv == NULL_PTR) {
		throw std::runtime_error("Private key == NULL");
	}

	rc = _flist->C_SignInit(_session, &mechanism, _hpriv);
	if (rc != CKR_OK) {
		throwCKR("C_SignInit() failed", rc);
	}

	rc = _flist->C_Sign(_session, (CK_BYTE_PTR)data, len,
			NULL, &signed_len);
	if (rc != CKR_OK) {
		throwCKR("C_Sign() failed", rc);
	}

	signed_data = (CK_BYTE_PTR) malloc(signed_len);
	rc = _flist->C_Sign(_session, (CK_BYTE_PTR)data, len,
			signed_data, &signed_len);
	if (rc != CKR_OK) {
		throwCKR("C_Sign() failed", rc);
	}

	ret = std::string((char *)signed_data, signed_len);
	delete signed_data;
	signed_data = NULL;

	return ret;
}



std::string Session::decrypt(const char *data, size_t len, CK_BYTE_PTR ctx, CK_ULONG_PTR ctx_len)
{
	CK_RSA_PKCS_OAEP_PARAMS params = {
		CKM_SHA_1,
		CKG_MGF1_SHA1,
		CKZ_DATA_SPECIFIED,
		NULL_PTR,
		0
	};

	CK_MECHANISM mechanism = {
		CKM_RSA_PKCS_OAEP, &params, sizeof(params)
	};

	if (_hpriv == NULL_PTR) {
		throw std::runtime_error("Private key == NULL");
	}

	CK_RV rc = _flist->C_DecryptInit(_session, &mechanism, _hpriv);
	if (rc != CKR_OK) {
		throwCKR("C_DecryptInit() failed", rc);
	}

	rc = _flist->C_Decrypt(_session, (CK_BYTE_PTR)data, len, ctx, ctx_len);
	if (rc != CKR_OK) {
		throwCKR("C_Decrypt() failed", rc);
	}
	return std::string((char *)ctx, (unsigned int)(*ctx_len));
}

void Session::listObjects(FILE *out)
{
	CK_RV rc;
	CK_OBJECT_HANDLE objects[64];
	CK_ULONG objects_num;
	char value[65536];
	CK_ATTRIBUTE tmpl[] = {
		{ CKA_LABEL, value, sizeof(value) - 1 },
	};
	static struct {
		CK_ATTRIBUTE_TYPE type;
		const char *name;
	} attrlist[] = {
		{ CKA_CLASS, "Class" },
		{ CKA_LABEL, "Label" },
		{ CKA_ID, "ID" },
		{ 0, 0 }
	};
	bool isprintable;

	fprintf(out, "\n");
	_objects.clear();
	rc = _flist->C_FindObjectsInit(_session, NULL_PTR, 0);
	if (rc != CKR_OK) {
		throwCKR("C_FindObjectsInit() failed", rc);
	}
	for (;;) {
		rc = _flist->C_FindObjects(_session, objects, 64, &objects_num);
		if (rc != CKR_OK) {
			throwCKR("C_FindObjects() failed", rc);
		}
		if (objects_num == 0) {
			break;
		}
		for (CK_ULONG i = 0; i < objects_num; ++i) {
			_objects.push_back(objects[i]);
			fprintf(out, "Object no. %ld:\n", _objects.size());
			for (int j = 0; attrlist[j].name; ++j) {
				tmpl[0].pValue = NULL_PTR;
				tmpl[0].ulValueLen = 0;
				tmpl[0].type = attrlist[j].type;
				rc = _flist->C_GetAttributeValue(_session, objects[i],
								  tmpl, 1);
				if (tmpl[0].ulValueLen == 0) {
					continue;
				}
				tmpl[0].pValue = value;
				tmpl[0].ulValueLen = sizeof(value) - 1;
				tmpl[0].type = attrlist[j].type;
				rc = _flist->C_GetAttributeValue(_session, objects[i],
								  tmpl, 1);
				if (rc == CKR_ATTRIBUTE_SENSITIVE) {
					fprintf(out, "  %s: *** sensitive!!! ***\n", attrlist[j].name);
					continue;
				}
				if (rc != CKR_OK) {
					throwCKR("C_GetAttributeValue() failed", rc);
				}
				if (tmpl[0].ulValueLen < 0) {
					// printf("%s: *** does not exist!!! ***\n");
					continue;
				}
				value[tmpl[0].ulValueLen] = 0;
				isprintable = true;
				for (CK_ULONG k = 0; k < tmpl[0].ulValueLen; ++k) {
					if (!isprint(value[k])) {
						isprintable = false;
						break;
					}
				}
				if (isprintable) {
					fprintf(out, "  %s: \"%s\"\n", attrlist[j].name, value);
				} else {
					const char *v = "*** not printable ***";
					if (attrlist[j].type == CKA_CLASS) {
						switch (*((CK_OBJECT_CLASS_PTR)value)) {
						case CKO_DATA:
							v = "data";
							break;
						case CKO_CERTIFICATE:
							v = "certificate";
							break;
						case CKO_PUBLIC_KEY:
							v = "public key";
							break;
						case CKO_PRIVATE_KEY:
							v = "private key";
							break;
						case CKO_SECRET_KEY:
							v = "secret key";
							break;
						default:
							v = "unknown class";
						}
					}
					fprintf(out, "  %s: %s\n", attrlist[j].name, v);
				}
				if (tmpl[0].ulValueLen > 0) {
					std::string asciirep;
					fprintf(out, "    ");
					CK_ULONG m = 0;
					for (m = 0; m < tmpl[0].ulValueLen; ++m) {
						if ((m % 16) == 0 && m > 0) {
							fprintf(out, "  %s\n    ", asciirep.c_str());
							asciirep = "";
						}
						fprintf(out, "%2.2X ", (unsigned char) value[m]);
						asciirep += isprint(value[m]) ? value[m] : '.';
					}
					while (m % 16) {
						fprintf(out, "   ");
						++m;
					}
					fprintf(out, "  %s\n", asciirep.c_str());
				}
			}
			fprintf(out, "\n");
		}
	}
	rc = _flist->C_FindObjectsFinal(_session);
	if (rc != CKR_OK) {
		throwCKR("C_FindObjectsFinal() failed", rc);
	}
}

void Session::deleteObject(unsigned int onum)
{
	CK_RV rc;

	if (onum < 1 || onum > _objects.size()) {
		throw std::runtime_error("No object with the given number");
	}

	rc = _flist->C_DestroyObject(_session, _objects[onum - 1]);
	if (rc != CKR_OK) {
		throwCKR("C_DestroyObject() failed", rc);
	}
}

void Session::deleteAllObjects()
{
	CK_RV rc;
	CK_OBJECT_HANDLE objects[64];
	CK_ULONG objects_num;

	_objects.clear();

	rc = _flist->C_FindObjectsInit(_session, NULL_PTR, 0);
	if (rc != CKR_OK) {
		throwCKR("C_FindObjectsInit() failed", rc);
	}
	for (;;) {
		rc = _flist->C_FindObjects(_session, objects, 64, &objects_num);
		if (rc != CKR_OK) {
			throwCKR("C_FindObjects() failed", rc);
		}
		if (objects_num == 0) {
			break;
		}

		for (CK_ULONG i = 0; i < objects_num; ++i) {
			_objects.push_back(objects[i]);
			printf("Del object nr %ld\n", i + 1);
			deleteObject(i + 1);
		}
	}
	rc = _flist->C_FindObjectsFinal(_session);
	if (rc != CKR_OK) {
		throwCKR("C_FindObjectsFinal() failed", rc);
	}
}

void Session::genRSA(int bits, const std::string &label, unsigned char id)
{
	CK_OBJECT_HANDLE hpub, hpriv;
	CK_MECHANISM mechanism = {
		CKM_RSA_PKCS_KEY_PAIR_GEN, NULL_PTR, 0
	};
	CK_ULONG modulus_bits = bits;
	CK_BYTE public_exponent[] = { 3 };
	CK_BYTE key_id[] = { id };
	CK_BBOOL true_value = TRUE;
	CK_BBOOL false_value = FALSE;
	CK_CHAR key_label[256];
	CK_RV rc;

	strncpy((char*) key_label, label.c_str(), sizeof(key_label));
	key_label[sizeof(key_label) - 1] = 0;

	CK_ATTRIBUTE pub_key_tmpl[] = {
		{ CKA_TOKEN, &true_value, sizeof(true_value) },
		{ CKA_ID, &key_id, sizeof(key_id) },
		{ CKA_LABEL, key_label, strlen((const char*) key_label) },
		{ CKA_ENCRYPT, &true_value, sizeof(true_value) },
		{ CKA_WRAP, &true_value, sizeof(true_value) },
		{ CKA_MODULUS_BITS, &modulus_bits, sizeof(modulus_bits) },
		{ CKA_PUBLIC_EXPONENT, &public_exponent, sizeof(public_exponent) }
	};
	int pub_key_tmpl_size = sizeof(pub_key_tmpl) / sizeof(CK_ATTRIBUTE);

	CK_ATTRIBUTE priv_key_tmpl[] = {
		{ CKA_TOKEN, &true_value, sizeof(true_value) },
		{ CKA_PRIVATE, &true_value, sizeof(true_value) },
		{ CKA_ID, &key_id, sizeof(key_id) },
		{ CKA_LABEL, key_label, strlen((const char*) key_label) },
		{ CKA_SENSITIVE, &false_value, sizeof(false_value) },
		{ CKA_DECRYPT, &true_value, sizeof(true_value) },
		{ CKA_EXTRACTABLE, &false_value, sizeof(false_value) },
		{ CKA_UNWRAP, &true_value, sizeof(true_value) }
	};
	int priv_key_tmpl_size = sizeof(priv_key_tmpl) / sizeof(CK_ATTRIBUTE);

	if (id < 0 || id > 255) {
		throw std::runtime_error("ID must be between 0 and 255");
	}

	rc = _flist->C_GenerateKeyPair(_session, &mechanism,
					pub_key_tmpl, pub_key_tmpl_size,
					priv_key_tmpl, priv_key_tmpl_size,
					&hpub, &hpriv);
	if (rc != CKR_OK) {
		throwCKR("C_GenerateKeyPair() failed", rc);
	}
}

void Session::exportRsaPrivKey(const std::string &pub_key_label,
			      const std::string &priv_key_label,
		const char *output)
{
	setCurrentPrivKey(priv_key_label);
	setCurrentPubKey(pub_key_label);

	if (&_hpriv == NULL || &_hpub == NULL) {
		return;
	}

	RSA *rsa = NULL;
	rsa = RSA_new();
	if (rsa == NULL) {
		throw std::runtime_error("RSA_new() == NULL");
	}

	CK_RV rc;

	CK_ATTRIBUTE pubTemplate[] = {
		{CKA_MODULUS, NULL, 0},
		{CKA_PUBLIC_EXPONENT, NULL, 0}
	};

	CK_ATTRIBUTE privTemplate[] = {
		{CKA_MODULUS, NULL, 0},
		{CKA_PRIVATE_EXPONENT, NULL, 0},
		{CKA_PRIME_1, NULL, 0},
		{CKA_PRIME_2, NULL, 0},
		{CKA_EXPONENT_1, NULL, 0},
		{CKA_EXPONENT_2, NULL, 0},
		{CKA_COEFFICIENT, NULL, 0}
	};

	rc = _flist->C_GetAttributeValue(_session, _hpriv, privTemplate, 7);
	if (rc != CKR_OK) {
		throwCKR("C_GetAttributeValue() failed 1", rc);
	}

	privTemplate[0].pValue =
		(CK_BYTE_PTR)malloc((unsigned int)privTemplate[0].ulValueLen);
	privTemplate[1].pValue =
		(CK_BYTE_PTR)malloc((unsigned int)privTemplate[1].ulValueLen);
	privTemplate[2].pValue =
		(CK_BYTE_PTR)malloc((unsigned int)privTemplate[2].ulValueLen);
	privTemplate[3].pValue =
		(CK_BYTE_PTR)malloc((unsigned int)privTemplate[3].ulValueLen);
	privTemplate[4].pValue =
		(CK_BYTE_PTR)malloc((unsigned int)privTemplate[4].ulValueLen);
	privTemplate[5].pValue =
		(CK_BYTE_PTR)malloc((unsigned int)privTemplate[5].ulValueLen);
	privTemplate[6].pValue =
		(CK_BYTE_PTR)malloc((unsigned int)privTemplate[6].ulValueLen);

	rc = _flist->C_GetAttributeValue(_session, _hpriv, privTemplate, 7);
	if (rc != CKR_OK) {
		throwCKR("C_GetAttributeValue() failed", rc);
	}

	rsa->n = BN_bin2bn((const unsigned char*)privTemplate[0].pValue,
			privTemplate[0].ulValueLen, NULL);
	rsa->d = BN_bin2bn((const unsigned char*)privTemplate[1].pValue,
			privTemplate[1].ulValueLen, NULL);
	rsa->p = BN_bin2bn((const unsigned char*)privTemplate[2].pValue,
			privTemplate[2].ulValueLen, NULL);
	rsa->q = BN_bin2bn((const unsigned char*)privTemplate[3].pValue,
			privTemplate[3].ulValueLen, NULL);
	rsa->dmp1 = BN_bin2bn((const unsigned char*)privTemplate[4].pValue,
			privTemplate[4].ulValueLen, NULL);
	rsa->dmq1 = BN_bin2bn((const unsigned char*)privTemplate[5].pValue,
			privTemplate[5].ulValueLen, NULL);
	rsa->iqmp = BN_bin2bn((const unsigned char*)privTemplate[6].pValue,
			privTemplate[6].ulValueLen, NULL);

	free(privTemplate[0].pValue);
	free(privTemplate[1].pValue);
	free(privTemplate[2].pValue);
	free(privTemplate[3].pValue);
	free(privTemplate[4].pValue);
	free(privTemplate[5].pValue);
	free(privTemplate[6].pValue);

	rc = _flist->C_GetAttributeValue(_session, _hpub, pubTemplate, 2);
	if (rc != CKR_OK) {
		throwCKR("C_GetAttributeValue() failed", rc);
	}

	pubTemplate[0].pValue =
			(CK_BYTE_PTR)malloc((unsigned int)pubTemplate[0].ulValueLen);
	pubTemplate[1].pValue =
			(CK_BYTE_PTR)malloc((unsigned int)pubTemplate[1].ulValueLen);

	rc = _flist->C_GetAttributeValue(_session, _hpub, pubTemplate, 2);
	if (rc != CKR_OK) {
		throwCKR("C_GetAttributeValue() failed", rc);
	}

	rsa->n = BN_bin2bn((const unsigned char*)pubTemplate[0].pValue,
			pubTemplate[0].ulValueLen, NULL);
	rsa->e = BN_bin2bn((const unsigned char*)pubTemplate[1].pValue,
			pubTemplate[1].ulValueLen, NULL);
	free(pubTemplate[0].pValue);
	free(pubTemplate[1].pValue);

	FILE *out = fopen(output, "w");
	if (out  == NULL) {
		fprintf(stderr,  "Error: %s\n", strerror(errno));
		exit(1);
	}

	PEM_write_RSAPrivateKey(out, rsa, NULL, NULL, 0, 0, NULL);

	RSA_free(rsa);
}

