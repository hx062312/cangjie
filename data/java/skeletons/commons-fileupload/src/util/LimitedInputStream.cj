// Package Declaration
package fileupload.util

// Imports Begin
import util.Closeable
import std.os.*
import std.collection.*
import std.io.*
// Imports End

class LimitedInputStream <:Closeable,  {
	// Class Fields Begin
	internal let sizeMax: Int64 = 0
	internal var count: Int64 = 0
	internal var closed: Bool = false
	// Class Fields End

	// Class Methods Begin
	public func close(): Unit {
		// TODO
	}
	public func isClosed(): Bool {
		// TODO
	}
	public func read1(b: Array<Int8>, off: Int64, len_: Int64): Int64 {
		// TODO
	}
	public func read0(): Int64 {
		// TODO
	}
	public init(inputStream: , pSizeMax: Int64) {
		// TODO
	}
	internal func checkLimit(): Unit {
		// TODO
	}
	protected func raiseError(pSizeMax: Int64, pCount: Int64): Unit {
		// TODO
	}
	// Class Methods End

}

