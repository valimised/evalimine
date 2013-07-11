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
#include "crypto/OCSP.h"
#include "crypto/X509Cert.h"
#include "crypto/X509CertStore.h"
#include "crypto/Digest.h"
#include "xml/xmldsig-core-schema.hxx"
#include "xml/XAdES.hxx"


namespace bdoc
{
	class ContainerInfo;
	class Configuration;

	class Signature {

		public:
			static const std::string DSIG_NAMESPACE;

			virtual ~Signature();

			static Signature* parse(const std::string& schema_dir,
					const char *xml_buf, size_t buf_len, ContainerInfo *ci);

			virtual void validateOffline(X509CertStore *store);
			virtual void getOCSPResponseValue(std::vector<unsigned char>& data) const = 0;

			virtual std::string getProducedAt() const = 0;

			virtual xml_schema::Uri ocspDigestAlgorithm() const = 0;

			virtual void getRevocationOCSPRef(
					std::vector<unsigned char>& data,
					std::string& digestMethodUri) const = 0;

			std::string getSubject() const;
			X509Cert getSigningCertificate() const;
			std::vector<unsigned char> getSignatureValue() const;

			std::auto_ptr<xercesc::DOMDocument> createDom() const;

		protected:

			virtual const std::string& xadesnamespace() = 0;

			virtual void checkKeyInfo() const = 0;
			virtual void checkSignedSignatureProperties() const = 0;
			virtual void checkQualifyingProperties() const = 0;

			Signature(dsig::SignatureType* signature, const char *xml, size_t xml_len, bdoc::ContainerInfo *ci);

			bdoc::dsig::KeyInfoType& keyInfo() const;


			dsig::X509DataType::X509CertificateType&
				getSigningX509CertificateType() const;

			dsig::SignatureMethodType::AlgorithmType&
				getSignatureMethodAlgorithmType() const;

			std::vector<unsigned char>
				calcDigestOnNode(Digest* calc,
						const std::string& ns,
						const std::string& tagName);

			void addCertificateValue(const std::string& certId,
						const X509Cert& x509);

			dsig::SignatureType* _sign;

		private:

			Signature& operator=( Signature const& that );

			void initQualifyingProperties();
			void validateIdentifier() const;


			// offline checks
			void checkSignature();
			void checkSignatureMethod() const;
			void checkReferences();
			void checkSignatureValue();
			void checkSigningCertificate(
					bdoc::X509CertStore *store) const;


			bool isReferenceToSigProps(const bdoc::dsig::ReferenceType& refType) const;
			void checkReferenceToSigProps(const bdoc::dsig::ReferenceType& refType);
			void checkReferencesToDocs(dsig::SignedInfoType::ReferenceSequence& refSeq) const;
			void checkDocumentRefDigest(const std::string& documentFileName, const dsig::ReferenceType& refType) const;


			const char *_xml;
			size_t _xml_len;
			bdoc::ContainerInfo *_bdoc;
	};


	class XAdES111Signature : public Signature {

		public:

			virtual ~XAdES111Signature();

			void getOCSPResponseValue(std::vector<unsigned char>& data) const;
			std::string getProducedAt() const;
			xml_schema::Uri ocspDigestAlgorithm() const;
			void getRevocationOCSPRef(
					std::vector<unsigned char>& data,
					std::string& digestMethodUri) const;

		protected:

			friend class Signature;

			static const std::string XADES111_NAMESPACE;
			const std::string& xadesnamespace();

			XAdES111Signature(
					dsig::SignatureType* signature,
					const char *signature_xml,
					size_t signature_xml_len,
					bdoc::ContainerInfo *bdoc);

			void checkKeyInfo() const;
			void checkSignedSignatureProperties() const;
			void checkQualifyingProperties() const;

		private:

			xades111::UnsignedPropertiesType::UnsignedSignaturePropertiesOptional& unsignSigProps() const;
	};

	class XAdES132Signature : public Signature {

		public:

			virtual ~XAdES132Signature();

			void getOCSPResponseValue(std::vector<unsigned char>& data) const;
			std::string getProducedAt() const;
			xml_schema::Uri ocspDigestAlgorithm() const;
			void getRevocationOCSPRef(
					std::vector<unsigned char>& data,
					std::string& digestMethodUri) const;

		protected:

			friend class Signature;

			static const std::string XADES132_NAMESPACE;
			const std::string& xadesnamespace();

			XAdES132Signature(
					dsig::SignatureType* signature,
					const char *signature_xml,
					size_t signature_xml_len,
					bdoc::ContainerInfo *bdoc);

			void checkKeyInfo() const;
			void checkSignedSignatureProperties() const;
			void checkQualifyingProperties() const;

		private:

			xades132::UnsignedPropertiesType::UnsignedSignaturePropertiesOptional& unsignSigProps() const;
	};

	class SignatureValidator {

		public:

			SignatureValidator(bdoc::Signature *sig, bdoc::Configuration *cf);
			~SignatureValidator();

			std::string getProducedAt() const;
			OCSP::CertStatus validateBESOnline();
			std::string getTMSignature();
			void validateTMOffline();

		protected:

			bdoc::OCSP* prepare();

		private:

			bdoc::Signature *_sig;
			bdoc::Configuration *_conf;

			X509Cert _signingCert;
			STACK_OF(X509)* _ocspCerts;
			X509* _issuerX509;
			std::vector<unsigned char> _ocspResponse;
			struct tm _producedAt;
	};

}

