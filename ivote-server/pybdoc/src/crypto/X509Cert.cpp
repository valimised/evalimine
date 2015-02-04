/*
 * Copyright: Eesti Vabariigi Valimiskomisjon
 * (Estonian National Electoral Committee), www.vvk.ee
 * Derived work from libdicidocpp library
 * https://svn.eesti.ee/projektid/idkaart_public/trunk/libdigidocpp/
 * Written in 2011-2014 by Cybernetica AS, www.cyber.ee
 *
 * This work is licensed under the Creative Commons
 * Attribution-NonCommercial-NoDerivs 3.0 Unported License.
 * To view a copy of this license, visit
 * http://creativecommons.org/licenses/by-nc-nd/3.0/.
 * */

#pragma GCC diagnostic warning "-Wunused-parameter"

#include "X509Cert.h"
#include "OpenSSLHelpers.h"
#include "../StackException.h"

#include <sstream>
#include <openssl/bio.h>
#include <openssl/bn.h>
#include <openssl/pem.h>
#include <openssl/ecdsa.h>
#include <openssl/err.h>
#include <openssl/x509v3.h>
#include <string.h>

bdoc::X509Cert::X509Cert(): cert(NULL)
{
}

bdoc::X509Cert::X509Cert(X509* cert) : cert(NULL)
{
	this->cert = copyX509(cert);
}

bdoc::X509Cert::X509Cert(const unsigned char* bytes, size_t len) :
	cert(NULL)
{
	if (bytes == NULL) {
		THROW_STACK_EXCEPTION("No bytes given to parse X509.");
	}

	d2i_X509(&cert, &bytes, len);
	if (cert == NULL) {
		THROW_STACK_EXCEPTION("Failed to parse X509 certificate from bytes given: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

bdoc::X509Cert::X509Cert(const X509Cert& copy) :
	cert(NULL)
{
	this->cert = copyX509(copy.cert);
}

bdoc::X509Cert::~X509Cert()
{
	X509_free(cert);
}

bdoc::X509Cert& bdoc::X509Cert::operator=(const X509Cert& copy)
{
	this->cert = copyX509(copy.cert);
	return *this;
}

X509* bdoc::X509Cert::getX509() const
{
	return copyX509(cert);
}

X509* bdoc::X509Cert::copyX509(X509* cert)
{
	X509* copy = X509_dup(cert);
	if (copy == NULL) {
		THROW_STACK_EXCEPTION("Failed to copy X509 certificate: %s", ERR_reason_error_string(ERR_get_error()));
	}

	return copy;
}

X509* bdoc::X509Cert::loadX509(const std::string& path)
{
	BIO* file = BIO_new(BIO_s_file());
	BIO_scope fileScope(&file);
	if (file == NULL) {
		THROW_STACK_EXCEPTION("Failed to open X.509 certificate file '%s': %s",
				path.c_str(), ERR_reason_error_string(ERR_get_error()));
	}

	if (BIO_read_filename(file, path.c_str()) <= 0) {
		THROW_STACK_EXCEPTION("Failed to open X.509 certificate file '%s': %s",
				path.c_str(), ERR_reason_error_string(ERR_get_error()));
	}

	// Parse X.509 certificate from file.
	return PEM_read_bio_X509(file, NULL, NULL, NULL);
}

STACK_OF(X509)* bdoc::X509Cert::loadX509Stack(const std::string& path)
{
	STACK_OF(X509)* stack = sk_X509_new_null();
	if (stack == NULL) {
		THROW_STACK_EXCEPTION("Failed to create X.509 certificate stack.");
	}

	BIO* file = BIO_new(BIO_s_file());
	BIO_scope fileScope(&file);
	if (file == NULL) {
		THROW_STACK_EXCEPTION("Failed to open X.509 certificates file '%s': %s",
				path.c_str(), ERR_reason_error_string(ERR_get_error()));
	}

	if (BIO_read_filename(file, path.c_str()) <= 0) {
		THROW_STACK_EXCEPTION("Failed to open X.509 certificates file '%s': %s",
				path.c_str(), ERR_reason_error_string(ERR_get_error()));
	}

	STACK_OF(X509_INFO)* certsInfo = PEM_X509_INFO_read_bio(file, NULL, NULL, NULL);
	if (certsInfo == NULL) {
		THROW_STACK_EXCEPTION("Failed to read X.509 certificates from file '%s': %s",
				path.c_str(), ERR_reason_error_string(ERR_get_error()));
	}

	for (int i = 0; i < sk_X509_INFO_num(certsInfo); i++) {
		X509_INFO* xi = sk_X509_INFO_value(certsInfo, i);
		if (xi->x509 != NULL) {
			sk_X509_push(stack, xi->x509);
			xi->x509 = NULL;
		}
	}

	sk_X509_INFO_pop_free(certsInfo, X509_INFO_free);

	return stack;
}

std::vector<unsigned char> bdoc::X509Cert::encodeDER() const
{
	int bufSize = i2d_X509(cert, NULL);
	if (bufSize < 0) {
		THROW_STACK_EXCEPTION("Failed to encode X509 cert to DER.");
	}

	std::vector<unsigned char> derEncodedX509(bufSize, 0);

	unsigned char* pBuf = &derEncodedX509[0];
	bufSize = i2d_X509(cert, &pBuf);
	if (bufSize < 0) {
		THROW_STACK_EXCEPTION("Failed to encode X509 cert to DER.");
	}

	return derEncodedX509;
}

std::string bdoc::X509Cert::getSerial() const
{
	std::string serial;
	ASN1_INTEGER* bs = NULL;
	if (!(bs = X509_get_serialNumber(cert))) {
		THROW_STACK_EXCEPTION("Failed to read certificate serial number from X.509 certificate: %s", ERR_reason_error_string(ERR_get_error()));
	}

	BIGNUM *bn = ASN1_INTEGER_to_BN(bs, NULL);

	char *str = BN_bn2dec(bn);
	serial = std::string(str);

	BN_free(bn);
	OPENSSL_free(str);

	return serial;
}

X509_NAME* bdoc::X509Cert::getIssuerNameAsn1() const
{
	return X509_get_issuer_name(cert);
}

std::string bdoc::X509Cert::getIssuerName() const
{
	X509_NAME* issuerName = X509_get_issuer_name(cert);
	if (issuerName == NULL) {
		THROW_STACK_EXCEPTION("Failed to convert X.509 certificate issuer name: %s", ERR_reason_error_string(ERR_get_error()));
	}

	return toString(issuerName);
}

std::string bdoc::X509Cert::getSubject() const
{
	X509_NAME* subject = X509_get_subject_name(cert);
	if (subject == NULL) {
	   THROW_STACK_EXCEPTION("Failed to convert X.509 certificate subject: %s", ERR_reason_error_string(ERR_get_error()));
	}

	return toString(subject);
}

std::string bdoc::X509Cert::toString(X509_NAME* name)
{
	BIO* mem = BIO_new(BIO_s_mem());
	BIO_scope memScope(&mem);
	if (mem == NULL) {
		THROW_STACK_EXCEPTION("Failed to allocate memory for X509_NAME conversion: %s", ERR_reason_error_string(ERR_get_error()));
	}

	if (X509_NAME_print_ex(mem, name, 0, XN_FLAG_RFC2253) < 0) {
		THROW_STACK_EXCEPTION("Failed to convert X509_NAME struct to string: %s", ERR_reason_error_string(ERR_get_error()));
	}

	// Read the converted string from buffer.
	char buf[128];
	int bytesRead;
	std::string str;
	while ((bytesRead = BIO_gets(mem, &buf[0], sizeof(buf))) > 0) {
		str.append(buf);
	}

	return str;
}

EVP_PKEY* bdoc::X509Cert::getPublicKey() const
{
	EVP_PKEY* pubKey = X509_get_pubkey(cert);
	if (pubKey == NULL) {
		EVP_PKEY_free(pubKey);
		THROW_STACK_EXCEPTION("Unable to load public key: %s",
				ERR_reason_error_string(ERR_get_error()));
	}
	return pubKey;
}

std::string bdoc::X509Cert::getRsaModulus() const
{
	EVP_PKEY* pubKey = getPublicKey();
	if (EVP_PKEY_type(pubKey->type) != EVP_PKEY_RSA) {
		EVP_PKEY_free(pubKey);
		THROW_STACK_EXCEPTION("Public key is not a RSA key.");
	}


	int bufSize = BN_num_bytes(pubKey->pkey.rsa->n);

	if (bufSize <= 0) {
		EVP_PKEY_free(pubKey);
		THROW_STACK_EXCEPTION("Failed to extract RSA modulus.");
	}

	std::string modulus(bufSize, '\0');

	if (BN_bn2bin(pubKey->pkey.rsa->n, (unsigned char*)&modulus[0]) <= 0) {
		EVP_PKEY_free(pubKey);
		THROW_STACK_EXCEPTION("Failed to extract RSA modulus.");
	}

	EVP_PKEY_free(pubKey);
	return modulus;
}

std::string bdoc::X509Cert::getRsaExponent() const
{
	EVP_PKEY* pubKey = getPublicKey();
	if (EVP_PKEY_type(pubKey->type) != EVP_PKEY_RSA) {
		EVP_PKEY_free(pubKey);
		THROW_STACK_EXCEPTION("Public key is not a RSA key.");
	}

	int bufSize = BN_num_bytes(pubKey->pkey.rsa->e);

	if (bufSize <= 0) {
		EVP_PKEY_free(pubKey);
		THROW_STACK_EXCEPTION("Failed to extract RSA exponent.");
	}

	std::string exp(bufSize, '\0');

	if (BN_bn2bin(pubKey->pkey.rsa->e, (unsigned char *)&exp[0]) <= 0) {
		EVP_PKEY_free(pubKey);
		THROW_STACK_EXCEPTION("Failed to extract RSA exponent.");
	}

	EVP_PKEY_free(pubKey);
	return exp;
}

bool bdoc::X509Cert::isValid() const
{
	int notBefore = X509_cmp_current_time(cert->cert_info->validity->notBefore);
	int notAfter = X509_cmp_current_time(cert->cert_info->validity->notAfter);
	if (notBefore == 0 || notAfter == 0) {
		THROW_STACK_EXCEPTION("Failed to validate cert", ERR_reason_error_string(ERR_get_error()));
	}
	return notBefore < 0 && notAfter > 0;
}

bool bdoc::X509Cert::verify(X509_STORE* aStore, struct tm* tm) const
{
	if (aStore == NULL) {
		THROW_STACK_EXCEPTION("Invalid argument to verify");
	}

	X509_STORE* store = aStore;
	X509_STORE** ppStore = NULL;
	X509_STORE_scope xst(ppStore);

	X509_STORE_CTX *csc = X509_STORE_CTX_new();
	X509_STORE_CTX_scope csct(&csc);
	if (csc == NULL) {
		THROW_STACK_EXCEPTION("Failed to create X509_STORE_CTX %s",ERR_reason_error_string(ERR_get_error()));
	}

	X509* x = getX509();
	X509_scope xt(&x);
	if (!X509_STORE_CTX_init(csc, store, x, NULL)) {
		THROW_STACK_EXCEPTION("Failed to init X509_STORE_CTX %s",ERR_reason_error_string(ERR_get_error()));
	}

	if (tm != NULL) {
		time_t t = timegm(tm);
		if (t == -1) {
			THROW_STACK_EXCEPTION("Given time cannot be represented as calendar time");
		}

		X509_VERIFY_PARAM *param = X509_STORE_CTX_get0_param(csc);
		if (param == NULL) {
			THROW_STACK_EXCEPTION("Failed to retrieve X509_STORE_CTX verification parameters %s",
				ERR_reason_error_string(ERR_get_error()));
		}
		X509_VERIFY_PARAM_set_time(param, t);
	}

	int ok = X509_verify_cert(csc);

	if (ok != 1) {
		int err = X509_STORE_CTX_get_error(csc);
		X509Cert cause(X509_STORE_CTX_get_current_cert (csc));
		std::ostringstream s;
		s << "Unable to verify " << cause.getSubject();
		s << ". Cause: " << X509_verify_cert_error_string(err);
		switch (err) {
			case X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY:
				{
					THROW_STACK_EXCEPTION("Certificate issuer missing: %s", s.str().c_str());
				}
			default: THROW_STACK_EXCEPTION(s.str().c_str()); break;
		}
	}

	return (ok == 1);
}

int bdoc::X509Cert::compareIssuerToString(std::string in) const  {

	return 0;
}

bool bdoc::X509Cert::verifySignature(int digestMethod, int digestSize,
		std::vector<unsigned char> digest,
		std::vector<unsigned char> signature)
{
	int result = 0;
	EVP_PKEY* key = getPublicKey();

	switch (EVP_PKEY_type(key->type)) {
	case EVP_PKEY_RSA:
	{
		if (digest.size() > static_cast<size_t>(digestSize)) {
			// The digest already has an ASN.1 DigestInfo header.
			break;
		}
		X509_SIG *sig = X509_SIG_new();
		// Prefer set0 to set_md, so we don't have to initialize the
		// digest lookup table with OpenSSL_add_all_digests. None of
		// our supported digests have parameters anyway.
		X509_ALGOR_set0(sig->algor, OBJ_nid2obj(digestMethod), V_ASN1_NULL, NULL);
		ASN1_OCTET_STRING_set(sig->digest, &digest[0], digest.size());

		unsigned char *asn1 = NULL;
		size_t asn1_len = i2d_X509_SIG(sig, &asn1);
		digest = std::vector<unsigned char>(asn1, asn1 + asn1_len);
		X509_SIG_free(sig);
		break;
	}
	case EVP_PKEY_EC:
	{
		ECDSA_SIG *sig = ECDSA_SIG_new();
		// signature is just r and s concatenated, so split them.
		size_t n_len = signature.size() >> 1;
		BN_bin2bn(&signature[0],     n_len, sig->r);
		BN_bin2bn(&signature[n_len], n_len, sig->s);

		unsigned char *asn1 = NULL;
		size_t asn1_len = i2d_ECDSA_SIG(sig, &asn1);
		signature = std::vector<unsigned char>(asn1, asn1 + asn1_len);
		ECDSA_SIG_free(sig);
		break;
	}
	default:
		THROW_STACK_EXCEPTION("Certificate '%s' has an unsupported "
				"public key type, can not verify signature.",
				getSubject().c_str());
	}

	EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(key, NULL);
	if (!ctx) {
		EVP_PKEY_free(key);
		THROW_STACK_EXCEPTION("Creating signature verification "
				"context failed: %s",
				ERR_reason_error_string(ERR_get_error()));
	}

	if (EVP_PKEY_verify_init(ctx) <= 0) {
		EVP_PKEY_CTX_free(ctx);
		EVP_PKEY_free(key);
		THROW_STACK_EXCEPTION("Initializing signature "
				"verification context failed: %s",
				ERR_reason_error_string(ERR_get_error()));
	}
	result = EVP_PKEY_verify(ctx, &signature[0], signature.size(),
			&digest[0], digest.size());
	if (result < 0) {
		EVP_PKEY_CTX_free(ctx);
		EVP_PKEY_free(key);
		THROW_STACK_EXCEPTION("Error during signature verification: %s",
				ERR_reason_error_string(ERR_get_error()));
	}

	EVP_PKEY_CTX_free(ctx);
	EVP_PKEY_free(key);

	return (result == 1);
}
