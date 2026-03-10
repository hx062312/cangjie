// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import ProgressListener
import std.io.*
// Imports End

class ProgressListenerTest {
	// Class Fields Begin
	// Class Fields End

	// Class Methods Begin
	// Class Methods End

}

	// Empty class body
class ProgressListenerImpl <:ProgressListener {
	// Class Fields Begin
	internal let expectedContentLength: Int64 = 0
	internal let expectedItems: Int64 = 0
	internal var bytesRead: Int64 = 0
	internal var items: Int64 = 0
	// Class Fields End

	// Class Methods Begin
	public func update(pBytesRead: Int64, pContentLength: Int64, pItems: Int64): Unit {
		// TODO
	}
	internal func checkFinished(): Unit {
		// TODO
	}
	internal init(pContentLength: Int64, pItems: Int64) {
		// TODO
	}
	// Class Methods End

}

