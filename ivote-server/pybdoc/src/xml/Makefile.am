
noinst_LTLIBRARIES = libbdocxml.la

libbdocxml_la_SOURCES = XAdES.cxx xmldsig-core-schema.cxx \
                        xades-signatures.cxx

BUILT_SOURCES = XAdES.cxx xmldsig-core-schema.cxx \
                xades-signatures.cxx

CLEANFILES = XAdES.cxx XAdES.hxx \
	xmldsig-core-schema.cxx xmldsig-core-schema.hxx \
	xades-signatures.cxx xades-signatures.hxx

XSD_EXECUTABLE = xsdcxx

XSD_COMMON_OPTIONS = --type-naming ucc --function-naming lcc \
	--root-element-first \
	--output-dir ../../src/xml

SCHEMA_DIR = ../../etc/schema

XAdES.cxx: $(SCHEMA_DIR)/XAdES.xsd
	cd $(SCHEMA_DIR) && $(XSD_EXECUTABLE) cxx-tree $(XSD_COMMON_OPTIONS) \
	--namespace-map http://www.w3.org/2000/09/xmldsig\#=bdoc::dsig \
	--namespace-map http://uri.etsi.org/01903/v1.3.2\#=bdoc::xades132 \
	$(XSD_NS2) XAdES.xsd

xmldsig-core-schema.cxx: $(SCHEMA_DIR)/xmldsig-core-schema.xsd
	cd $(SCHEMA_DIR) && $(XSD_EXECUTABLE) cxx-tree $(XSD_COMMON_OPTIONS) \
	--namespace-map http://www.w3.org/2000/09/xmldsig\#=bdoc::dsig \
	--namespace-map http://uri.etsi.org/01903/v1.3.2\#=bdoc::xades132 \
	$(XSD_NS1) xmldsig-core-schema.xsd

xades-signatures.cxx: $(SCHEMA_DIR)/xades-signatures.xsd
	cd $(SCHEMA_DIR) && $(XSD_EXECUTABLE) cxx-tree $(XSD_COMMON_OPTIONS) \
	--namespace-map http://uri.etsi.org/02918/v1.2.1#=bdoc::asic \
	--namespace-map http://www.w3.org/2000/09/xmldsig\#=bdoc::dsig \
	--namespace-map http://uri.etsi.org/01903/v1.3.2\#=bdoc::xades132 \
	$(XSD_NS1) xades-signatures.xsd

