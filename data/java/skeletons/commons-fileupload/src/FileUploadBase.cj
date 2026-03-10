// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import util.FileItemHeadersImpl
import RequestContext
import ProgressListener
import ParameterParser
import FileUploadException
import FileItemHeaders
import FileItemFactory
import FileItem
import std.os.*
import std.collection.*
import std.iterator.*
import std.reflect.*
import std.io.*
// Imports End

class FileUploadBase {
	// Class Fields Begin
	public static let MAX_HEADER_SIZE: Int64 = ?
	internal var sizeMax: Int64 = ?
	internal var fileSizeMax: Int64 = ?
	internal var fileCountMax: Int64 = ?
	internal var headerEncoding: String = ""
	internal var listener: ProgressListener = ?
	public static let CONTENT_TYPE: String = ?
	public static let CONTENT_DISPOSITION: String = ?
	public static let CONTENT_LENGTH: String = ?
	public static let FORM_DATA: String = ?
	public static let ATTACHMENT: String = ?
	public static let MULTIPART: String = ?
	public static let MULTIPART_FORM_DATA: String = ?
	public static let MULTIPART_MIXED: String = ?
	// Class Fields End

	// Class Methods Begin
	protected func getHeader(headers: , name: String): String {
		// TODO
	}
	protected func parseHeaders(headerPart: String):  {
		// TODO
	}
	protected func createItem(headers: , isFormField: Bool): FileItem {
		// TODO
	}
	protected func getFieldName2(headers: ): String {
		// TODO
	}
	protected func getFileName0(headers: ): String {
		// TODO
	}
	public func setProgressListener(pListener: ProgressListener): Unit {
		// TODO
	}
	public func getProgressListener(): ProgressListener {
		// TODO
	}
	protected func newFileItemHeaders(): FileItemHeadersImpl {
		// TODO
	}
	protected func getParsedHeaders(headerPart: String): FileItemHeaders {
		// TODO
	}
	protected func getFieldName0(headers: FileItemHeaders): String {
		// TODO
	}
	protected func getFileName1(headers: FileItemHeaders): String {
		// TODO
	}
	protected func getBoundary(contentType: String): Array<Int8> {
		// TODO
	}
	public func setHeaderEncoding(encoding: String): Unit {
		// TODO
	}
	public func getHeaderEncoding(): String {
		// TODO
	}
	public func setFileCountMax(fileCountMax: Int64): Unit {
		// TODO
	}
	public func getFileCountMax(): Int64 {
		// TODO
	}
	public func setFileSizeMax(fileSizeMax: Int64): Unit {
		// TODO
	}
	public func getFileSizeMax(): Int64 {
		// TODO
	}
	public func setSizeMax(sizeMax: Int64): Unit {
		// TODO
	}
	public func getSizeMax(): Int64 {
		// TODO
	}
	public static func isMultipartContent(ctx: RequestContext): Bool {
		// TODO
	}
	internal func parseHeaderLine(headers: FileItemHeadersImpl, header: String): Unit {
		// TODO
	}
	internal func parseEndOfLine(headerPart: String, end: Int64): Int64 {
		// TODO
	}
	internal func getFieldName1(pContentDisposition: String): String {
		// TODO
	}
	internal func getFileName2(pContentDisposition: String): String {
		// TODO
	}
	public func setFileItemFactory(factory: FileItemFactory): Unit {
		// TODO
	}
	public func getFileItemFactory(): FileItemFactory {
		// TODO
	}
	// Class Methods End

}

class FileItemIteratorImpl {
	// Class Fields Begin
	internal var currentItem: FileItemStreamImpl = ?
	internal var currentFieldName: String = ""
	internal var skipPreamble: Bool = false
	internal var itemValid: Bool = false
	internal var eof: Bool = false
	// Class Fields End

	// Class Methods Begin
	internal func getContentLength(pHeaders: FileItemHeaders): Int64 {
		// TODO
	}
	// Class Methods End

}

class FileItemStreamImpl {
	// Class Fields Begin
	internal var opened: Bool = false
	internal var headers: FileItemHeaders = ?
	// Class Fields End

	// Class Methods Begin
	public func setHeaders(pHeaders: FileItemHeaders): Unit {
		// TODO
	}
	public func getHeaders(): FileItemHeaders {
		// TODO
	}
	// Class Methods End

}

class InvalidContentTypeException <:FileUploadException {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	// Class Fields End

	// Class Methods Begin
	public init(msg: String, cause: ) {
		// TODO
	}
	// Class Methods End

}

class UnknownSizeException <:FileUploadException {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	// Class Fields End

	// Class Methods Begin
	public init(message: String) {
		// TODO
	}
	// Class Methods End

}

class IOFileUploadException <:FileUploadException {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	internal let cause:  = ?
	// Class Fields End

	// Class Methods Begin
	public func getCause():  {
		// TODO
	}
	public init(pMsg: String, pException: ) {
		// TODO
	}
	// Class Methods End

}

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

class FileUploadIOException <: {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	internal let cause: FileUploadException = ?
	// Class Fields End

	// Class Methods Begin
	public func getCause():  {
		// TODO
	}
	public init(pCause: FileUploadException) {
		// TODO
	}
	// Class Methods End

}

