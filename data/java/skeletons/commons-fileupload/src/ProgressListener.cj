// Package Declaration
package fileupload

// Imports Begin
import std.io.*
// Imports End

interface ProgressListener {
	// Class Fields Begin
	// Class Fields End

	// Class Methods Begin
	public func update(pBytesRead: Int64, pContentLength: Int64, pItems: Int64): Unit {
		// TODO
	}
	// Class Methods End

}

