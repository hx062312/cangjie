// Package Declaration
package fileupload

// Imports Begin
import std.iterator.*
import std.io.*
// Imports End

interface FileItemHeaders {
	// Class Fields Begin
	// Class Fields End

	// Class Methods Begin
	public func getHeaderNames(): Iterator<String> {
		// TODO
	}
	public func getHeaders(name: String): Iterator<String> {
		// TODO
	}
	public func getHeader(name: String): String {
		// TODO
	}
	// Class Methods End

}

