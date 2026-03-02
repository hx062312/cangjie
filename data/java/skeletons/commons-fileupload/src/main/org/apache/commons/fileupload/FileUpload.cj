// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import org/apache/commons/fileupload/FileUploadBase
import org/apache/commons/fileupload/FileItemFactory
import std.io.*
// Imports End

class FileUpload <:FileUploadBase {
	// Class Fields Begin
	internal var fileItemFactory: FileItemFactory = ?
	// Class Fields End

	// Class Methods Begin
	public func setFileItemFactory(factory: FileItemFactory): Unit {
		// TODO
	}
	public func getFileItemFactory(): FileItemFactory {
		// TODO
	}
	public init(constructorId: Int64, fileItemFactory: FileItemFactory) {
		// TODO
	}
	// Class Methods End

}

