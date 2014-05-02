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

#pragma once
#pragma GCC diagnostic warning "-Wunused-variable"
#include <stdexcept>
#include <sstream>
#include <string>
#include <stdarg.h>
#include "CallStack.h"

#define THROW_STACK_EXCEPTION(...) \
	{std::string _msg(bdoc::format(__VA_ARGS__)); \
	throw bdoc::StackRuntimeError(__FILE__, __LINE__, \
		__FUNCTION__, _msg, bdoc::show_stacktrace); }

#define DECLARE_STACK_EXCEPTION(...) \
	std::string _msg(bdoc::format(__VA_ARGS__)); \
	bdoc::StackRuntimeError exc(__FILE__, __LINE__, \
		__FUNCTION__, _msg, bdoc::show_stacktrace);

#include <iostream>

namespace bdoc {

static bool show_stacktrace = true;

std::string formatArgList(const char* fmt, va_list args);

std::string format(const char* fmt, ...);

class StackExceptionBase : public CallStack {

	public:
		StackExceptionBase (bool ss = true) :
			CallStack(2), show_stack(ss), causes() {
		}

		virtual ~StackExceptionBase () throw() {}

		virtual const char* what () const {
			whatstr = mywhat(std::string(""));
			return whatstr.c_str();
		}

		virtual std::string mywhat (const std::string& pre) const = 0;

		virtual void add() {
			causes.push_back(
				std::string("\tUnknown (...) exception"));
		}

		virtual void add(const StackExceptionBase& ex) {
			causes.push_back(ex.mywhat("\t"));
		}

		virtual void add(const std::exception& ex) {
			causes.push_back(std::string("\t") +
						std::string(ex.what()));
		}

		virtual bool hasCauses() const {
			return (causes.size() > 0);
		}

	protected:

		bool show_stack;
		std::vector<std::string> causes;
		mutable std::string whatstr;
};

template<class T>
class StackException : public T, public StackExceptionBase {

	public:
		StackException (const std::string& file,
				size_t line,
				const std::string& function,
				const std::string& msg,
				bool ss = true)
			: T(msg), StackExceptionBase(ss),
				_file(file), _line(line), _func(function) {
		}

		virtual ~StackException () throw() {}

		virtual std::string mywhat (const std::string& pre) const {
			std::stringstream _buffer;
			_buffer << "[FILE:(";
			_buffer << _file;
			_buffer << ") LINE:(";
			_buffer << _line;
			_buffer << ") FUNCTION:(";
			_buffer << _func;
			_buffer << ") MSG:(";
			_buffer << std::string(T::what());
			_buffer << ")]\n";
			std::string out = pre + _buffer.str();

			if (show_stack) {
				out += StackException::to_string(pre);
			}

			std::vector<std::string>::const_iterator it = causes.begin();
			while (it != causes.end()) {
				out += pre;
				out += *it;
				it++;
			}

			return out;
		}

	private:
		std::string _file;
		size_t _line;
		std::string _func;
};

typedef StackException<std::runtime_error> StackRuntimeError;
typedef StackException<std::range_error> StackRangeError;
typedef StackException<std::overflow_error> StackOverflowError;
typedef StackException<std::underflow_error> StackUnderflowError;
typedef StackException<std::logic_error> StackLogicError;
typedef StackException<std::domain_error> StackDomainError;
typedef StackException<std::invalid_argument> StackInvalidArgument;
typedef StackException<std::length_error> StackLengthError;
typedef StackException<std::out_of_range> StackOutOfRange;

} // namespace stacktrace
