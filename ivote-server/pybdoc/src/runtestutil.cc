#if 0
set -ex
[ testutil -nt $0 ] || cc -o testutil $0 -L.libs -lbdoc
echo Usage: sh $0 -doc testzip/test.txt test.txt -verifyOnline testzip/META-INF/signatures0.xml
LD_LIBRARY_PATH=.libs ./testutil -schema ../etc/schema -certdir ../etc/certs "$@"
exit $?
#endif

extern int pybdoc_test_main(int argc, char **argv);

int main(int argc, char **argv) {
	return pybdoc_test_main(argc, argv);
}
