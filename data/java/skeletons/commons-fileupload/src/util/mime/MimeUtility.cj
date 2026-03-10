// Package Declaration
package org.apache.commons.fileupload.util.mime

// Imports Begin
import util.mime.QuotedPrintableDecoder
import util.mime.ParseException
import util.mime.Base64Decoder
import std.io.*
// Imports End

class MimeUtility {
	// Class Fields Begin
	static let US_ASCII_CHARSET: String = ?
	static let BASE64_ENCODING_MARKER: String = ?
	static let QUOTEDPRINTABLE_ENCODING_MARKER: String = ?
	static let ENCODED_TOKEN_MARKER: String = ?
	static let ENCODED_TOKEN_FINISHER: String = ?
	static let LINEAR_WHITESPACE: String = ?
	static let MIME2JAVA:  = [:]
	// Class Fields End

	// Class Methods Begin
	public static func decodeText(text: String): String {
		// TODO
	}
	internal static func javaCharset(charset: String): String {
		// TODO
	}
	internal static func decodeWord(word: String): String {
		// TODO
	}
	internal init() {
		// TODO
	}
	// Class Methods End

}

