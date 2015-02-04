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

#include <stdio.h>
#include <iostream>
#include <openssl/err.h>
#include <openssl/pem.h>
#include <openssl/rsa.h>
#include <string.h>
#include <string>
#include "SignatureVerifierImpl.h"

#define RSA_SIGNATURE_LENGTH	256
#define SHA256_DIGEST_LENGTH	32
#define RSA_DECRYPT_OUT_LEN	 51

SignatureVerifierImpl::SignatureVerifierImpl()
	: pubkey(), signature(), hash(), error()
{
}

SignatureVerifierImpl::~SignatureVerifierImpl()
{
}

RSA* getRSA(unsigned char* unspubkey, int pubkeyLen) {
	BIO *pkey = NULL;
	EVP_PKEY *sigkey = NULL;
	RSA *rsa = NULL;

	pkey = BIO_new_mem_buf(unspubkey, pubkeyLen);
	if (!pkey) {
		goto end;
	}

	sigkey = PEM_read_bio_PUBKEY(pkey, NULL, NULL, NULL);
	if (!sigkey) {
		goto end;
	}

	rsa = EVP_PKEY_get1_RSA(sigkey);
	if (!rsa) {
		goto end;
	}

end:

	if (pkey) BIO_free (pkey);
	if (sigkey) EVP_PKEY_free(sigkey);
	return rsa;
}

bool checkSignature(unsigned char* raw_hash_a, int raw_hash_a_len,
        unsigned char* hash_b, int hash_b_len) {
	unsigned char hash_a[RSA_DECRYPT_OUT_LEN] = {
	0x30, 0x31, 0x30, 0x0d, 0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65,
	0x03, 0x04, 0x02, 0x01, 0x05, 0x00, 0x04, 0x20, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

    int hdr_len = RSA_DECRYPT_OUT_LEN - SHA256_DIGEST_LENGTH;
    bool ret = false;

    if ((raw_hash_a == NULL) || (hash_b == NULL)) goto error;
    if (hdr_len + raw_hash_a_len != RSA_DECRYPT_OUT_LEN) goto error;
    if (hash_b_len != RSA_DECRYPT_OUT_LEN) goto error;

	memcpy(&hash_a[hdr_len], raw_hash_a, raw_hash_a_len);

	if (memcmp (hash_a, hash_b, hash_b_len) == 0) {
		ret = true;
	}

error:

    return ret;
}

int message_decrypt(unsigned char *from, int flen, RSA *key,
        unsigned char** out) {
	int ret = -1;
	unsigned char *tmp = NULL;
    int ksize;

    if ((from == NULL) || (flen <= 0) ||
            (key == NULL) || (out == NULL)) goto error;

    ksize = RSA_size(key);

	tmp = (unsigned char*) OPENSSL_malloc(ksize - 11);
	if (tmp == NULL) {
		goto error;
	}

	ret = RSA_public_decrypt(flen, from, tmp, key, RSA_PKCS1_PADDING);
    if (ret < 0) goto error;

    *out = tmp;
    tmp = NULL;

error:

    OPENSSL_free(tmp);

	return ret;
}

bool SignatureVerifierImpl::isSignatureOk() {
	bool ok = false;
	unsigned char *rsa_out = NULL;
    int rsa_out_len = 0;
	RSA *rsa = NULL;

	if (hash.len() != SHA256_DIGEST_LENGTH) {
		error = "Input hash is of unsuitable size";
		goto end;
	}

	if (signature.len() != RSA_SIGNATURE_LENGTH) {
		error = "Input signature is of unsuitable length";
		goto end;
	}

	rsa = getRSA((unsigned char *)pubkey.peek(), pubkey.len());
	if (!rsa) {
		error = "Error decoding RSA key: ";
		error += ERR_reason_error_string(ERR_get_error());
		goto end;
	}

	if (RSA_size(rsa) != RSA_SIGNATURE_LENGTH) {
		error = "Input public key is of unsuitable size";
		goto end;
	}

	rsa_out_len = message_decrypt((unsigned char *)signature.peek(),
            signature.len(), rsa, &rsa_out);
    if (rsa_out_len < 0) {
		error = "Error in decrypting: ";
		error += ERR_reason_error_string(ERR_get_error());
		goto end;
	}

	ok = checkSignature((unsigned char *)hash.peek(), hash.len(),
            rsa_out, rsa_out_len);
	if (!ok) {
		error = "Error in verification";
	}

end:
	RSA_free(rsa);
	OPENSSL_free(rsa_out);
	return ok;
}

