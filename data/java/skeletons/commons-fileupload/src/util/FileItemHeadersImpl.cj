// Package Declaration
package org.apache.commons.fileupload.util

// Imports Begin
import FileItemHeaders
import std.iterator.*
import std.any.*
import std.io.*
// Imports End

class FileItemHeadersImpl <:Any, FileItemHeaders {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	internal let headerNameToValueListMap:  = [:]
	// Class Fields End

	// Class Methods Begin
	public func getHeaders(name: String): Iterator<String> {
		// TODO
	}
	public func getHeaderNames(): Iterator<String> {
		// TODO
	}
	public func getHeader(name: String): String {
		// TODO
	}
	public func addHeader(name: String, value: String): Unit {
		// TODO
	}
	// Class Methods End

}

