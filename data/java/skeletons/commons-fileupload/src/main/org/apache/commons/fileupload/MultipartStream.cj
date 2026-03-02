// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import org/apache/commons/fileupload/ProgressListener
import org/apache/commons/fileupload/util/Closeable
import org/apache/commons/fileupload/FileItemStream
import org/apache/commons/fileupload/FileUploadBase
import std.os.*
import std.collection.*
import std.io.*
// Imports End

class MultipartStream {
	// Class Fields Begin
	public static let CR: Int8 = ?
	public static let LF: Int8 = ?
	public static let DASH: Int8 = ?
	public static let HEADER_PART_SIZE_MAX: Int64 = ?
	static let DEFAULT_BUFSIZE: Int64 = ?
	static let HEADER_SEPARATOR: Array<Int8> = ?
	static let FIELD_SEPARATOR: Array<Int8> = ?
	static let STREAM_TERMINATOR: Array<Int8> = ?
	static let BOUNDARY_PREFIX: Array<Int8> = ?
	internal let input:  = ?
	internal var boundaryLength: Int64 = 0
	internal let keepRegion: Int64 = 0
	internal let boundary: Array<Int8> = []
	internal let boundaryTable: Array<Int64> = []
	internal let bufSize: Int64 = 0
	internal let buffer: Array<Int8> = []
	internal var head: Int64 = 0
	internal var tail: Int64 = 0
	internal var headerEncoding: String = ""
	internal let notifier: ProgressNotifier = ?
	// Class Fields End

	// Class Methods Begin
	public static func MultipartStream3(input_: , boundary: Array<Int8>): MultipartStream {
		// TODO
	}
	public static func MultipartStream1(input_: , boundary: Array<Int8>, bufSize: Int64): MultipartStream {
		// TODO
	}
	public static func MultipartStream0(): MultipartStream {
		// TODO
	}
	protected func findSeparator(): Int64 {
		// TODO
	}
	protected func findByte(value: Int8, pos: Int64): Int64 {
		// TODO
	}
	public static func arrayequals(a: Array<Int8>, b: Array<Int8>, count: Int64): Bool {
		// TODO
	}
	public func readHeaders(): String {
		// TODO
	}
	public func setBoundary(boundary: Array<Int8>): Unit {
		// TODO
	}
	public func readBoundary(): Bool {
		// TODO
	}
	public func readByte(): Int8 {
		// TODO
	}
	public func setHeaderEncoding(encoding: String): Unit {
		// TODO
	}
	public func getHeaderEncoding(): String {
		// TODO
	}
	public static func MultipartStream2(input_: , boundary: Array<Int8>, pNotifier: ProgressNotifier): MultipartStream {
		// TODO
	}
	public init(input_: , boundary: Array<Int8>, bufSize: Int64, pNotifier: ProgressNotifier) {
		// TODO
	}
	internal func computeBoundaryTable(): Unit {
		// TODO
	}
	internal func newInputStream(): ItemInputStream {
		// TODO
	}
	// Class Methods End

}

class ItemInputStream <: {
	// Class Fields Begin
	internal var total: Int64 = 0
	internal var pad: Int64 = 0
	internal var pos: Int64 = 0
	internal var closed: Bool = false
	static let BYTE_POSITIVE_OFFSET: Int64 = ?
	// Class Fields End

	// Class Methods Begin
	public func isClosed(): Bool {
		// TODO
	}
	public func skip(bytes_: Int64): Int64 {
		// TODO
	}
	public func read(): Int64 {
		// TODO
	}
	public func available(): Int64 {
		// TODO
	}
	public func close1(pCloseUnderlying: Bool): Unit {
		// TODO
	}
	public func close0(): Unit {
		// TODO
	}
	public func read1(b: Array<Int8>, off: Int64, len_: Int64): Int64 {
		// TODO
	}
	public func read0(): Int64 {
		// TODO
	}
	public func getBytesRead(): Int64 {
		// TODO
	}
	internal func makeAvailable(): Int64 {
		// TODO
	}
	internal func findSeparator(): Unit {
		// TODO
	}
	internal init() {
		// TODO
	}
	// Class Methods End

}

class IllegalBoundaryException <: {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	// Class Fields End

	// Class Methods Begin
	public init(message: String) {
		// TODO
	}
	// Class Methods End

}

class MalformedStreamException <: {
	// Class Fields Begin
	static let serialVersionUID: Int64 = ?
	// Class Fields End

	// Class Methods Begin
	public init(message: String) {
		// TODO
	}
	// Class Methods End

}

class ProgressNotifier {
	// Class Fields Begin
	internal let listener: ProgressListener = ?
	internal let contentLength: Int64 = 0
	internal var bytesRead: Int64 = 0
	internal var items: Int64 = 0
	// Class Fields End

	// Class Methods Begin
	internal func notifyListener(): Unit {
		// TODO
	}
	internal func noteItem(): Unit {
		// TODO
	}
	internal func noteBytesRead(pBytes: Int64): Unit {
		// TODO
	}
	internal init(pListener: ProgressListener, pContentLength: Int64) {
		// TODO
	}
	// Class Methods End

}

