// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import std.io.*
// Imports End

class SizeException <:FileUploadException {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	internal let actual: Int64 = 0
	internal let permitted: Int64 = 0
	// Class Fields End

	// Class Methods Begin
	public func getPermittedSize(): Int64 {
		// TODO
	}
	public func getActualSize(): Int64 {
		// TODO
	}
	protected init(message: String, actual: Int64, permitted: Int64) {
		// TODO
	}
	// Class Methods End

}

class FileSizeLimitExceededException <:SizeException {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	internal var fileName: String = ""
	internal var fieldName: String = ""
	// Class Fields End

	// Class Methods Begin
	public func setFieldName(pFieldName: String): Unit {
		// TODO
	}
	public func getFieldName(): String {
		// TODO
	}
	public func setFileName(pFileName: String): Unit {
		// TODO
	}
	public func getFileName(): String {
		// TODO
	}
	public init(message: String, actual: Int64, permitted: Int64) {
		// TODO
	}
	// Class Methods End

}

class SizeLimitExceededException <:SizeException {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	// Class Fields End

	// Class Methods Begin
	public static func SizeLimitExceededException1(message: String): SizeLimitExceededException {
		// TODO
	}
	public static func SizeLimitExceededException0(): SizeLimitExceededException {
		// TODO
	}
	public init(message: String, actual: Int64, permitted: Int64) {
		// TODO
	}
	// Class Methods End

}

