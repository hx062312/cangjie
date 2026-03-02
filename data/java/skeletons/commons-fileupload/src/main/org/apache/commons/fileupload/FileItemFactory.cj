// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import org/apache/commons/fileupload/FileItem
import std.reflect.*
import std.io.*
// Imports End

interface FileItemFactory {
	// Class Fields Begin
	// Class Fields End

	// Class Methods Begin
	public func createItem(fieldName: String, contentType: String, isFormField: Bool, fileName: String): FileItem {
		// TODO
	}
	// Class Methods End

}

