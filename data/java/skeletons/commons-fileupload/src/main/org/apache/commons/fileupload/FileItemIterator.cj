// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import org/apache/commons/fileupload/FileUploadException
import org/apache/commons/fileupload/FileItemStream
import std.iterator.*
import std.io.*
// Imports End

interface FileItemIterator {
	// Class Fields Begin
	// Class Fields End

	// Class Methods Begin
	public func next_(): FileItemStream {
		// TODO
	}
	public func hasNext(): Bool {
		// TODO
	}
	// Class Methods End

}

