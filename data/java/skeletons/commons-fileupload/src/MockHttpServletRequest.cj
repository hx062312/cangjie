// Package Declaration
package org.apache.commons.fileupload

// Imports Begin
import FileUploadBase
import std.os.*
import std.collection.*
import std.any.*
import std.reflect.*
import std.io.*
import std.fs.*
// Imports End

class MockHttpServletRequest {
	// Class Fields Begin
	internal let m_requestData:  = ?
	internal var length: Int64 = 0
	internal let m_strContentType: String = ""
	internal var readLimit: Int64 = ?
	internal let m_headers:  = ?
	// Class Fields End

	// Class Methods Begin
	public func getRealPath(arg0: String): String {
		// TODO
	}
	public func getLocalAddr(): String {
		// TODO
	}
	public func getRemotePort(): Int64 {
		// TODO
	}
	public func getLocalPort(): Int64 {
		// TODO
	}
	public func getLocalName(): String {
		// TODO
	}
	public func isRequestedSessionIdFromUrl(): Bool {
		// TODO
	}
	public func isSecure(): Bool {
		// TODO
	}
	public func getLocales():  {
		// TODO
	}
	public func getLocale():  {
		// TODO
	}
	public func removeAttribute(arg0: String): Unit {
		// TODO
	}
	public func setAttribute(arg0: String, arg1: Any): Unit {
		// TODO
	}
	public func getRemoteHost(): String {
		// TODO
	}
	public func getRemoteAddr(): String {
		// TODO
	}
	public func getReader():  {
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
	public func getProtocol(): String {
		// TODO
	}
	public func getParameterMap():  {
		// TODO
	}
	public func getParameterValues(arg0: String): Array<String> {
		// TODO
	}
	public func getParameterNames():  {
		// TODO
	}
	public func getParameter(arg0: String): String {
		// TODO
	}
	public func setReadLimit(readLimit: Int64): Unit {
		// TODO
	}
	public func getContentType(): String {
		// TODO
	}
	public func setContentLength(length: Int64): Unit {
		// TODO
	}
	public func getContentLength(): Int64 {
		// TODO
	}
	public func setCharacterEncoding(arg0: String): Unit {
		// TODO
	}
	public func getCharacterEncoding(): String {
		// TODO
	}
	public func getAttributeNames():  {
		// TODO
	}
	public func getAttribute(arg0: String): Any {
		// TODO
	}
	public func isRequestedSessionIdFromURL(): Bool {
		// TODO
	}
	public func isRequestedSessionIdFromCookie(): Bool {
		// TODO
	}
	public func isRequestedSessionIdValid(): Bool {
		// TODO
	}
	public func getServletPath(): String {
		// TODO
	}
	public func getRequestURL():  {
		// TODO
	}
	public func getRequestURI(): String {
		// TODO
	}
	public func getRequestedSessionId(): String {
		// TODO
	}
	public func isUserInRole(arg0: String): Bool {
		// TODO
	}
	public func getRemoteUser(): String {
		// TODO
	}
	public func getQueryString(): String {
		// TODO
	}
	public func getContextPath(): String {
		// TODO
	}
	public func getPathTranslated(): String {
		// TODO
	}
	public func getPathInfo(): String {
		// TODO
	}
	public func getMethod(): String {
		// TODO
	}
	public func getHeaderNames():  {
		// TODO
	}
	public func getHeaders(arg0: String):  {
		// TODO
	}
	public func getHeader(headerName: String): String {
		// TODO
	}
	public func getDateHeader(arg0: String): Int64 {
		// TODO
	}
	public func getAuthType(): String {
		// TODO
	}
	public static func MockHttpServletRequest1(requestData: Array<Int8>, strContentType: String): MockHttpServletRequest {
		// TODO
	}
	public init(constructorId: Int64, requestData: , strContentType: String, requestLength: Int64) {
		// TODO
	}
	// Class Methods End

}

class MyServletInputStream {
	// Class Fields Begin
	internal let in:  = ?
	internal let readLimit: Int64 = 0
	// Class Fields End

	// Class Methods Begin
	public func read1(b: Array<Int8>, off: Int64, len_: Int64): Int64 {
		// TODO
	}
	public func read0(): Int64 {
		// TODO
	}
	public init(pStream: , readLimit: Int64) {
		// TODO
	}
	// Class Methods End

}

