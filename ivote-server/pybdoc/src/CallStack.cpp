/* Copyright (c) 2009, Fredrik Orderud
   License: BSD licence (http://www.opensource.org/licenses/bsd-license.php)
   Based on: http://stupefydeveloper.blogspot.com/2008/10/cc-call-stack.html */

/* Liux/gcc implementation of the CallStack class. */
#ifdef __GNUC__

#include <stdio.h>
#include <execinfo.h>
#include <cxxabi.h>
#include <dlfcn.h>
#include <stdlib.h>
#include "CallStack.h"

#define MAX_DEPTH 32

namespace bdoc {

CallStack::CallStack (const size_t num_discard /*= 0*/) {

	void * trace[MAX_DEPTH];
	int stack_depth = backtrace(trace, MAX_DEPTH);

	for (int i = num_discard+1; i < stack_depth; i++) {
		Dl_info dlinfo;
		if (!dladdr(trace[i], &dlinfo)) {
			break;
		}

		const char *symname = dlinfo.dli_sname;

		int status;
		char *demangled = abi::__cxa_demangle(symname, NULL, 0, &status);
		if (status == 0 && demangled) {
			symname = demangled;
		}

		if (dlinfo.dli_fname && symname) {
			CallStackEntry e;
			e.file = dlinfo.dli_fname;
			e.function = symname;
			stack.push_back(e);
		} 
		else {
			break; // skip last entries below main
		}

		if (demangled) {
			free(demangled);
		}
	}
}

CallStack::~CallStack () throw() {
}

} // namespace stacktrace

#endif // __GNUC__
