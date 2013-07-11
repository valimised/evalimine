
noinst_LTLIBRARIES = libbdocxml.la

libbdocxml_la_SOURCES = XAdES.cxx xmldsig-core-schema.cxx XAdES111.cxx

BUILT_SOURCES = XAdES.cxx xmldsig-core-schema.cxx XAdES111.cxx

CLEANFILES = XAdES.cxx XAdES.hxx XAdES111.cxx XAdES111.hxx \
	xmldsig-core-schema.cxx xmldsig-core-schema.hxx

XSD_EXECUTABLE = xsdcxx

XSD_COMMON_OPTIONS = --type-naming ucc --function-naming lcc \
	--root-element-first \
	--output-dir ../../src/xml

SCHEMA_DIR = ../../etc/schema

XAdES.cxx: $(SCHEMA_DIR)/XAdES.xsd
	cd $(SCHEMA_DIR) && $(XSD_EXECUTABLE) cxx-tree $(XSD_COMMON_OPTIONS) \
	--namespace-map http://www.w3.org/2000/09/xmldsig\#=bdoc::dsig \
	--namespace-map http://uri.etsi.org/01903/v1.1.1\#=bdoc::xades111 \
	--namespace-map http://uri.etsi.org/01903/v1.3.2\#=bdoc::xades132 \
	$(XSD_NS2) XAdES.xsd

xmldsig-core-schema.cxx: $(SCHEMA_DIR)/xmldsig-core-schema.xsd
	cd $(SCHEMA_DIR) && $(XSD_EXECUTABLE) cxx-tree $(XSD_COMMON_OPTIONS) \
	--namespace-map http://www.w3.org/2000/09/xmldsig\#=bdoc::dsig \
	--namespace-map http://uri.etsi.org/01903/v1.1.1\#=bdoc::xades111 \
	--namespace-map http://uri.etsi.org/01903/v1.3.2\#=bdoc::xades132 \
	$(XSD_NS1) xmldsig-core-schema.xsd

XAdES111.cxx: $(SCHEMA_DIR)/XAdES111.xsd
	cd $(SCHEMA_DIR) && $(XSD_EXECUTABLE) cxx-tree $(XSD_COMMON_OPTIONS) \
	--namespace-map http://www.w3.org/2000/09/xmldsig\#=bdoc::dsig \
	--namespace-map http://uri.etsi.org/01903/v1.1.1\#=bdoc::xades111 \
	--namespace-map http://uri.etsi.org/01903/v1.3.2\#=bdoc::xades132 \
	$(XSD_NS2) XAdES111.xsd

