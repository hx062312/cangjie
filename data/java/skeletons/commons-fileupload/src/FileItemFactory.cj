// Package Declaration
package fileupload

// Imports Begin
import FileItem
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

