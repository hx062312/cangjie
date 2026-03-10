// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import FileUploadException
import std.io.*
// Imports End

class FileCountLimitExceededException <:FileUploadException {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	internal let limit: Int64 = 0
	// Class Fields End

	// Class Methods Begin
	public func getLimit(): Int64 {
		// TODO
	}
	public init(message: String, limit: Int64) {
		// TODO
	}
	// Class Methods End

}

