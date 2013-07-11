/*
 * Copyright: Eesti Vabariigi Valimiskomisjon
 * (Estonian National Electoral Committee), www.vvk.ee
 * Derived work from libdicidocpp library
 * https://svn.eesti.ee/projektid/idkaart_public/trunk/libdigidocpp/
 * Written in 2011-2013 by Cybernetica AS, www.cyber.ee
 *
 * This work is licensed under the Creative Commons
 * Attribution-NonCommercial-NoDerivs 3.0 Unported License.
 * To view a copy of this license, visit
 * http://creativecommons.org/licenses/by-nc-nd/3.0/.
 * */

#pragma once

#include <openssl/objects.h>
#include <memory>
#include <openssl/sha.h>

#define URI_SHA1 "http://www.w3.org/2000/09/xmldsig#sha1"
#define URI_SHA224 "http://www.w3.org/2001/04/xmldsig-more#sha224"
#define URI_SHA256 "http://www.w3.org/2001/04/xmlenc#sha256"
#define URI_SHA384 "http://www.w3.org/2001/04/xmldsig-more#sha384"
#define URI_SHA512 "http://www.w3.org/2001/04/xmlenc#sha512"

namespace bdoc
{
	class Digest {

	public:
		virtual ~Digest() {}

		virtual void update(const unsigned char* data,
					unsigned long length) = 0;

		void update(std::vector<unsigned char> data);

		virtual std::vector<unsigned char> getDigest() = 0;

		virtual unsigned int getSize() const = 0;
		virtual int getMethod() const = 0;
		virtual std::string getUri() const = 0;

		static std::auto_ptr<Digest> create(int method);
		static std::auto_ptr<Digest> create(const std::string& methodUri);
		static int toMethod(const std::string& methodUri);
		static bool isSupported(const std::string& methodUri);

	protected:
		Digest() {}
		std::vector<unsigned char> digest;
	};

	class SHA1Digest : public Digest {

	public:
		SHA1Digest();
		virtual ~SHA1Digest() {}
		void update(const unsigned char* data, unsigned long length);
		std::vector<unsigned char> getDigest();

		virtual unsigned int getSize() const {
			return SHA_DIGEST_LENGTH;
		}

		virtual int getMethod() const {
			return NID_sha1;
		}

		virtual std::string getUri() const {
			return URI_SHA1;
		}

	private:
		SHA_CTX ctx;
	};

	class SHA224Digest : public Digest {

	public:
		SHA224Digest();
		virtual ~SHA224Digest() {}
		void update(const unsigned char* data, unsigned long length);
		std::vector<unsigned char> getDigest();

		virtual unsigned int getSize() const {
			return SHA224_DIGEST_LENGTH;
		}

		virtual int getMethod() const {
			return NID_sha224;
		}

		virtual std::string getUri() const {
			return URI_SHA224;
		}

	private:
		SHA256_CTX ctx;
	};

	class SHA256Digest : public Digest {

	public:
		SHA256Digest();
		virtual ~SHA256Digest() {}
		void update(const unsigned char* data, unsigned long length);
		std::vector<unsigned char> getDigest();

		virtual unsigned int getSize() const {
			return SHA256_DIGEST_LENGTH;
		}

		virtual int getMethod() const {
			return NID_sha256;
		}

		virtual std::string getUri() const {
			return URI_SHA256;
		}

	private:
		SHA256_CTX ctx;
	};

	class SHA384Digest : public Digest {

	public:
		SHA384Digest();
		virtual ~SHA384Digest() {}
		void update(const unsigned char* data, unsigned long length);
		std::vector<unsigned char> getDigest();

		virtual unsigned int getSize() const {
			return SHA384_DIGEST_LENGTH;
		}

		virtual int getMethod() const {
			return NID_sha384;
		}

		virtual std::string getUri() const {
			return URI_SHA384;
		}

	private:
		SHA512_CTX ctx;
	};

	class SHA512Digest : public Digest {

	public:
		SHA512Digest();
		virtual ~SHA512Digest() {}
		void update(const unsigned char* data, unsigned long length);
		std::vector<unsigned char> getDigest();

		virtual unsigned int getSize() const {
			return SHA512_DIGEST_LENGTH;
		}

		virtual int getMethod() const {
			return NID_sha512;
		}

		virtual std::string getUri() const {
			return URI_SHA512;
		}

	private:
		SHA512_CTX ctx;
	};
}

