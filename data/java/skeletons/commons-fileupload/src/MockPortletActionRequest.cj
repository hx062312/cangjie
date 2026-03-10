// Package Declaration
package org.apache.commons.fileupload.portlet

// Imports Begin
import FileUploadBase
import std.collection.*
import std.any.*
import std.reflect.*
import std.io.*
import std.fs.*
// Imports End

class MockPortletActionRequest {
	// Class Fields Begin
	internal let attributes:  = ?
	internal let parameters:  = [:]
	internal var characterEncoding: String = ""
	internal let length: Int64 = 0
	internal let contentType: String = ""
	internal let requestData:  = ?
	// Class Fields End

	// Class Methods Begin
	public func setCharacterEncoding(characterEncoding: String): Unit {
		// TODO
	}
	public func getReader():  {
		// TODO
	}
	public func getPortletInputStream():  {
		// TODO
	}
	public func getContentType(): String {
		// TODO
	}
	public func getContentLength(): Int64 {
		// TODO
	}
	public func getCharacterEncoding(): String {
		// TODO
	}
	public func setAttribute(key: String, value: Any): Unit {
		// TODO
	}
	public func removeAttribute(key: String): Unit {
		// TODO
	}
	public func isUserInRole(arg0: String): Bool {
		// TODO
	}
	public func isSecure(): Bool {
		// TODO
	}
	public func isRequestedSessionIdValid(): Bool {
		// TODO
	}
	public func getServerPort(): Int64 {
		// TODO
	}
	public func getServerName(): String {
		// TODO
	}
	public func getScheme(): String {
		// TODO
	}
	public func getResponseContentTypes():  {
		// TODO
	}
	public func getResponseContentType(): String {
		// TODO
	}
	public func getRequestedSessionId(): String {
		// TODO
	}
	public func getRemoteUser(): String {
		// TODO
	}
	public func getPropertyNames():  {
		// TODO
	}
	public func getProperty(arg0: String): String {
		// TODO
	}
	public func getProperties(arg0: String):  {
		// TODO
	}
	public func getParameterValues(arg0: String): Array<String> {
		// TODO
	}
	public func getParameterNames():  {
		// TODO
	}
	public func getParameterMap():  {
		// TODO
	}
	public func getParameter(key: String): String {
		// TODO
	}
	public func getLocales():  {
		// TODO
	}
	public func getLocale():  {
		// TODO
	}
	public func getContextPath(): String {
		// TODO
	}
	public func getAuthType(): String {
		// TODO
	}
	public func getAttributeNames():  {
		// TODO
	}
	public func getAttribute(key: String): Any {
		// TODO
	}
	public static func MockPortletActionRequest1(requestData: Array<Int8>, contentType: String): MockPortletActionRequest {
		// TODO
	}
	public init(requestLength: Int64, byteArrayInputStream: , contentType: String) {
		// TODO
	}
	// Class Methods End

}

