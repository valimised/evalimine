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

#include <openssl/err.h>
#include "../StackException.h"
#include "Digest.h"

std::auto_ptr<bdoc::Digest> bdoc::Digest::create(int method)
{
	switch(method) {
	default:
		THROW_STACK_EXCEPTION("Digest method '%s' is not supported.", OBJ_nid2sn(method));
	case NID_sha1: return std::auto_ptr<Digest>(new SHA1Digest);
	case NID_sha224: return std::auto_ptr<Digest>(new SHA224Digest);
	case NID_sha256: return std::auto_ptr<Digest>(new SHA256Digest);
	case NID_sha384: return std::auto_ptr<Digest>(new SHA384Digest);
	case NID_sha512: return std::auto_ptr<Digest>(new SHA512Digest);
	}
}

std::auto_ptr<bdoc::Digest> bdoc::Digest::create(const std::string& methodUri)
{
	return create(toMethod(methodUri));
}

int bdoc::Digest::toMethod(const std::string& methodUri)
{
	if (methodUri == URI_SHA1) return NID_sha1;
	if (methodUri == URI_SHA224) return NID_sha224;
	if (methodUri == URI_SHA256) return NID_sha256;
	if (methodUri == URI_SHA384) return NID_sha384;
	if (methodUri == URI_SHA512) return NID_sha512;
	return 0;
}

bool bdoc::Digest::isSupported(const std::string& methodUri)
{
	if (toMethod(methodUri) != 0) {
		return true;
	}

	return false;
}

void bdoc::Digest::update(std::vector<unsigned char> data)
{
	update(&data[0], data.size());
}

///

bdoc::SHA1Digest::SHA1Digest()
{
	if (SHA1_Init(&ctx) != 1) {
		THROW_STACK_EXCEPTION("Failed to initialize SHA1 digest calculator: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

void bdoc::SHA1Digest::update(const unsigned char* data, unsigned long length)
{
	if (data == NULL) {
		THROW_STACK_EXCEPTION("Can not update digest value from NULL pointer.");
	}

	if (!digest.empty()) {
		THROW_STACK_EXCEPTION("Digest is already finalized, can not update it.");
	}

	if (SHA1_Update(&ctx, static_cast<const void*>(data), length) != 1) {
		THROW_STACK_EXCEPTION("Failed to update SHA1 digest value: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

std::vector<unsigned char> bdoc::SHA1Digest::getDigest()
{
	if (!digest.empty()) {
		return digest;
	}

	unsigned char buf[SHA_DIGEST_LENGTH];
	if (SHA1_Final(buf, &ctx) != 1) {
		THROW_STACK_EXCEPTION("Failed to create SHA1 digest: %s", ERR_reason_error_string(ERR_get_error()));
	}

	for (unsigned int i = 0; i < SHA_DIGEST_LENGTH; i++) {
		digest.push_back(buf[i]);
	}

	return digest;
}

///

bdoc::SHA224Digest::SHA224Digest()
{
	if (SHA224_Init(&ctx) != 1) {
		THROW_STACK_EXCEPTION("Failed to initialize SHA224 digest calculator: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

void bdoc::SHA224Digest::update(const unsigned char* data, unsigned long length)
{
	if (data == NULL) {
		THROW_STACK_EXCEPTION("Can not update digest value from NULL pointer.");
	}

	if (!digest.empty()) {
		THROW_STACK_EXCEPTION("Digest is already finalized, can not update it.");
	}

	if (SHA224_Update(&ctx, static_cast<const void*>(data), length) != 1) {
		THROW_STACK_EXCEPTION("Failed to update SHA224 digest value: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

std::vector<unsigned char> bdoc::SHA224Digest::getDigest()
{
	if (!digest.empty()) {
		return digest;
	}

	unsigned char buf[SHA224_DIGEST_LENGTH];
	if (SHA224_Final(buf, &ctx) != 1) {
		THROW_STACK_EXCEPTION("Failed to create SHA224 digest: %s", ERR_reason_error_string(ERR_get_error()));
	}

	for (unsigned int i = 0; i < SHA224_DIGEST_LENGTH; i++) {
		digest.push_back(buf[i]);
	}

	return digest;
}

///

bdoc::SHA256Digest::SHA256Digest()
{
	if (SHA256_Init(&ctx) != 1) {
		THROW_STACK_EXCEPTION("Failed to initialize SHA256 digest calculator: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

void bdoc::SHA256Digest::update(const unsigned char* data, unsigned long length)
{
	if (data == NULL) {
		THROW_STACK_EXCEPTION("Can not update digest value from NULL pointer.");
	}

	if (!digest.empty()) {
		THROW_STACK_EXCEPTION("Digest is already finalized, can not update it.");
	}

	if (SHA256_Update(&ctx, static_cast<const void*>(data), length) != 1) {
		THROW_STACK_EXCEPTION("Failed to update SHA256 digest value: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

std::vector<unsigned char> bdoc::SHA256Digest::getDigest()
{
	if (!digest.empty()) {
		return digest;
	}

	unsigned char buf[SHA256_DIGEST_LENGTH];
	if (SHA256_Final(buf, &ctx) != 1) {
		THROW_STACK_EXCEPTION("Failed to create SHA256 digest: %s", ERR_reason_error_string(ERR_get_error()));
	}

	for (unsigned int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
		digest.push_back(buf[i]);
	}

	return digest;
}

///

bdoc::SHA384Digest::SHA384Digest()
{
	if (SHA384_Init(&ctx) != 1) {
		THROW_STACK_EXCEPTION("Failed to initialize SHA384 digest calculator: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

void bdoc::SHA384Digest::update(const unsigned char* data, unsigned long length)
{
	if (data == NULL) {
		THROW_STACK_EXCEPTION("Can not update digest value from NULL pointer.");
	}

	if (!digest.empty()) {
		THROW_STACK_EXCEPTION("Digest is already finalized, can not update it.");
	}

	if (SHA384_Update(&ctx, static_cast<const void*>(data), length) != 1) {
		THROW_STACK_EXCEPTION("Failed to update SHA384 digest value: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

std::vector<unsigned char> bdoc::SHA384Digest::getDigest()
{
	if (!digest.empty()) {
		return digest;
	}

	unsigned char buf[SHA384_DIGEST_LENGTH];
	if (SHA384_Final(buf, &ctx) != 1) {
		THROW_STACK_EXCEPTION("Failed to create SHA384 digest: %s", ERR_reason_error_string(ERR_get_error()));
	}

	for (unsigned int i = 0; i < SHA384_DIGEST_LENGTH; i++) {
		digest.push_back(buf[i]);
	}

	return digest;
}

///

bdoc::SHA512Digest::SHA512Digest()
{
	if (SHA512_Init(&ctx) != 1) {
		THROW_STACK_EXCEPTION("Failed to initialize SHA512 digest calculator: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

void bdoc::SHA512Digest::update(const unsigned char* data, unsigned long length)
{
	if (data == NULL) {
		THROW_STACK_EXCEPTION("Can not update digest value from NULL pointer.");
	}

	if (!digest.empty()) {
		THROW_STACK_EXCEPTION("Digest is already finalized, can not update it.");
	}

	if (SHA512_Update(&ctx, static_cast<const void*>(data), length) != 1) {
		THROW_STACK_EXCEPTION("Failed to update SHA512 digest value: %s", ERR_reason_error_string(ERR_get_error()));
	}
}

std::vector<unsigned char> bdoc::SHA512Digest::getDigest()
{
	if (!digest.empty()) {
		return digest;
	}

	unsigned char buf[SHA512_DIGEST_LENGTH];
	if (SHA512_Final(buf, &ctx) != 1) {
		THROW_STACK_EXCEPTION("Failed to create SHA512 digest: %s", ERR_reason_error_string(ERR_get_error()));
	}

	for (unsigned int i = 0; i < SHA512_DIGEST_LENGTH; i++) {
		digest.push_back(buf[i]);
	}

	return digest;
}

