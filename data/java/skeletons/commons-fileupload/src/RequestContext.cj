// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import std.reflect.*
import std.io.*
// Imports End

interface RequestContext {
	// Class Fields Begin
	// Class Fields End

	// Class Methods Begin
	public func getInputStream():  {
		// TODO
	}
	public func getContentLength(): Int64 {
		// TODO
	}
	public func getContentType(): String {
		// TODO
	}
	public func getCharacterEncoding(): String {
		// TODO
	}
	// Class Methods End

}

