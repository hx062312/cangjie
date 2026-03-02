// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import org/apache/commons/fileupload/util/mime/MimeUtility
import std.os.*
import std.collection.*
import std.io.*
// Imports End

class ParameterParser {
	// Class Fields Begin
	internal var chars: Array<Int8> = ?
	internal var pos: Int64 = ?
	internal var len: Int64 = ?
	internal var i1: Int64 = ?
	internal var i2: Int64 = ?
	internal var lowerCaseNames: Bool = ?
	// Class Fields End

	// Class Methods Begin
	public func parse3(charArray: Array<Int8>, offset: Int64, length: Int64, separator: ):  {
		// TODO
	}
	public func parse2(charArray: Array<Int8>, separator: ):  {
		// TODO
	}
	public func parse1(str_: String, separator: ):  {
		// TODO
	}
	public func parse0(str_: String, separators: Array<Int8>):  {
		// TODO
	}
	public func setLowerCaseNames(b: Bool): Unit {
		// TODO
	}
	public func isLowerCaseNames(): Bool {
		// TODO
	}
	public init() {
		// TODO
	}
	internal func parseQuotedToken(terminators: Array<Int8>): String {
		// TODO
	}
	internal func parseToken(terminators: Array<Int8>): String {
		// TODO
	}
	internal func isOneOf(ch: , charray: Array<Int8>): Bool {
		// TODO
	}
	internal func getToken(quoted: Bool): String {
		// TODO
	}
	internal func hasChar(): Bool {
		// TODO
	}
	// Class Methods End

}

