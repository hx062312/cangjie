// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import FileItemHeadersSupport
import std.collection.*
import std.reflect.*
import std.io.*
// Imports End

interface FileItem {
	// Class Fields Begin
	// Class Fields End

	// Class Methods Begin
	public func getOutputStream():  {
		// TODO
	}
	public func setFormField(state: Bool): Unit {
		// TODO
	}
	public func isFormField(): Bool {
		// TODO
	}
	public func setFieldName(name: String): Unit {
		// TODO
	}
	public func getFieldName(): String {
		// TODO
	}
	public func delete(): Unit {
		// TODO
	}
	public func write(file: ): Unit {
		// TODO
	}
	public func getString1(): String {
		// TODO
	}
	public func getString0(encoding: String): String {
		// TODO
	}
	public func get(): Array<Int8> {
		// TODO
	}
	public func getSize(): Int64 {
		// TODO
	}
	public func isInMemory(): Bool {
		// TODO
	}
	public func getName(): String {
		// TODO
	}
	public func getContentType(): String {
		// TODO
	}
	public func getInputStream():  {
		// TODO
	}
	// Class Methods End

}

