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

#include <string.h>
#include <openssl/pem.h>

#include "ChallengeVerifierImpl.h"

#define ASN_DIGEST_INFO_LEN	15
#define CHALLENGE_LEN		20

ChallengeVerifierImpl::ChallengeVerifierImpl()
	: certificate(), challenge(), signature(), error()
{
}

ChallengeVerifierImpl::~ChallengeVerifierImpl()
{
}

bool ChallengeVerifierImpl::isChallengeOk()
{
	// PKCS#1 DigestInfo ASN1, in case of obj-id sha1
	unsigned char asn1[ASN_DIGEST_INFO_LEN] = {
		0x30, 0x21, 0x30, 0x09, 0x06, 0x05, 0x2b, 0x0e,
		0x03, 0x02, 0x1a, 0x05, 0x00, 0x04, 0x14
	};

	bool ret = false;
	EVP_PKEY *pkey = NULL;
	RSA *rsa = NULL;
	unsigned char *rsa_out = NULL;
	int rsa_outlen = 0;
	int keysize = 0;
		X509 *x = NULL;

	const unsigned char *buf = certificate.peek();
	x = d2i_X509(NULL, &buf, certificate.len());
	if (x == NULL) {
		error = "Error decoding certificate";
		goto end;
		}

	pkey = X509_get_pubkey(x);
	if (pkey == NULL) {
		error = "Error decoding public key";
		goto end;
	}

	rsa = EVP_PKEY_get1_RSA(pkey);
	if (rsa == NULL) {
		error = "Error extracting RSA from public key";
		goto end;
	}

	keysize = RSA_size(rsa);
	rsa_out = (unsigned char*)OPENSSL_malloc(keysize);
	if (rsa_out == NULL) {
		error = "Out of memory";
		goto end;
	}

	rsa_outlen  = RSA_public_decrypt(signature.len(), \
						signature.peek(), rsa_out, \
						rsa, RSA_PKCS1_PADDING);
	if (rsa_outlen <= 0) {
		error = "Error in decryption";
		goto end;
	}

	if (rsa_outlen != (ASN_DIGEST_INFO_LEN + CHALLENGE_LEN)) {
		error = "Result length not correct";
		goto end;
	}

	if (memcmp(rsa_out, asn1, ASN_DIGEST_INFO_LEN)) {
		error = "Result ASN not correct";
		goto end;
	}

	if (challenge.len() != CHALLENGE_LEN) {
		error = "Invalid input challenge";
		goto end;
	}

	if (memcmp(rsa_out + ASN_DIGEST_INFO_LEN, \
					challenge.peek(), CHALLENGE_LEN)) {
		error = "Invalid challenge verification result";
		goto end;
	}

	ret = true;
	end:
	if (x) X509_free(x);
	if (rsa) RSA_free(rsa);
	if (rsa_out) OPENSSL_free(rsa_out);
	if (pkey) EVP_PKEY_free(pkey);
	return ret;
}

