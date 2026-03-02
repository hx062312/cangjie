// Package Declaration
package org.apache.commons.fileupload.disk

// Imports Begin
import org/apache/commons/fileupload/disk/DiskFileItem
import std.os.*
import std.io.*
// Imports End

class DiskFileItemFactory {
	// Class Fields Begin
	public static let DEFAULT_SIZE_THRESHOLD: Int64 = ?
	internal var repository:  = ?
	internal var sizeThreshold: Int64 = ?
	internal var defaultCharset: String = ?
	// Class Fields End

	// Class Methods Begin
	public func setDefaultCharset(pCharset: String): Unit {
		// TODO
	}
	public func getDefaultCharset(): String {
		// TODO
	}
	public func setSizeThreshold(sizeThreshold: Int64): Unit {
		// TODO
	}
	public func getSizeThreshold(): Int64 {
		// TODO
	}
	public func setRepository(repository: ): Unit {
		// TODO
	}
	public func getRepository():  {
		// TODO
	}
	public static func DiskFileItemFactory1(): DiskFileItemFactory {
		// TODO
	}
	public init(sizeThreshold: Int64, repository: ) {
		// TODO
	}
	// Class Methods End

}

