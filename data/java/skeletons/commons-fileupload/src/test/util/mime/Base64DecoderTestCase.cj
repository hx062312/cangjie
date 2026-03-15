// Package Declaration
package fileupload.util.mime

// Imports Begin
import util.mime.Base64Decoder
import std.io.*
// Imports End

@Test
class Base64DecoderTestCase {
	// Class Fields Begin
	static let US_ASCII_CHARSET: String = ?
	// Class Fields End

	// Class Methods Begin
	public func nonASCIIcharacter(): Unit {
		// TODO
	}
	public func badLength(): Unit {
		// TODO
	}
	public func badPaddingLeading2(): Unit {
		// TODO
	}
	public func badPaddingLeading1(): Unit {
		// TODO
	}
	public func badPadding(): Unit {
		// TODO
	}
	public func decodeTrailing3(): Unit {
		// TODO
	}
	public func decodeTrailing2(): Unit {
		// TODO
	}
	public func decodeTrailing1(): Unit {
		// TODO
	}
	public func decodeTrailingJunk(): Unit {
		// TODO
	}
	public func truncatedString(): Unit {
		// TODO
	}
	public func nonBase64Bytes(): Unit {
		// TODO
	}
	public func decodeWithInnerPad(): Unit {
		// TODO
	}
	public func rfc4648Section10Decode(): Unit {
		// TODO
	}
	internal static func assertIOException(messageText: String, encoded: String): Unit {
		// TODO
	}
	internal static func assertEncoded(clearText: String, encoded: String): Unit {
		// TODO
	}
	// Class Methods End

}

