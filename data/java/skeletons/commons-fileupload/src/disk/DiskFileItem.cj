// Package Declaration
package org.apache.commons.fileupload.disk

// Imports Begin
import util.Streams
import ParameterParser
import FileItemHeaders
import std.os.*
import std.collection.*
import std.reflect.*
import std.io.*
// Imports End

class DiskFileItem {
	// Class Fields Begin
	internal var headers: FileItemHeaders = ?
	internal var defaultCharset: String = ?
	public static let DEFAULT_CHARSET: String = ?
	static let UID: String = ?
	static let COUNTER:  = ?
	internal var fieldName: String = ""
	internal let contentType: String = ""
	internal var isFormField: Bool = false
	internal let fileName: String = ""
	internal var size: Int64 = ?
	internal let sizeThreshold: Int64 = 0
	internal let repository:  = ?
	internal var cachedContent: Array<Int8> = []
	internal var tempFile:  = ?
	// Class Fields End

	// Class Methods Begin
	public func setDefaultCharset(charset: String): Unit {
		// TODO
	}
	public func getDefaultCharset(): String {
		// TODO
	}
	public func setHeaders(pHeaders: FileItemHeaders): Unit {
		// TODO
	}
	public func getHeaders(): FileItemHeaders {
		// TODO
	}
	protected func getTempFile():  {
		// TODO
	}
	public func setFormField(state: Bool): Unit {
		// TODO
	}
	public func isFormField(): Bool {
		// TODO
	}
	public func setFieldName(fieldName: String): Unit {
		// TODO
	}
	public func getFieldName(): String {
		// TODO
	}
	public func getName(): String {
		// TODO
	}
	public func getCharSet(): String {
		// TODO
	}
	public func getContentType(): String {
		// TODO
	}
	public init(fieldName: String, contentType: String, isFormField: Bool, fileName: String, sizeThreshold: Int64, repository: ) {
		// TODO
	}
	internal static func getUniqueId(): String {
		// TODO
	}
	// Class Methods End

}

