// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import FileItemHeadersSupport
import std.reflect.*
import std.io.*
// Imports End

interface FileItemStream {
	// Class Fields Begin
	// Class Fields End

	// Class Methods Begin
	public func isFormField(): Bool {
		// TODO
	}
	public func getFieldName(): String {
		// TODO
	}
	public func getName(): String {
		// TODO
	}
	public func getContentType(): String {
		// TODO
	}
	public func openStream():  {
		// TODO
	}
	// Class Methods End

}

class ItemSkippedException <: {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	// Class Fields End

	// Class Methods Begin
	// Class Methods End

}

