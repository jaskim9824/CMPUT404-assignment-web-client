#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# Copyright 2023 Jason Kim
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body="", full_response=""):
        self.code = code
        self.body = body
        self.full_response = full_response
    
    def __str__(self) -> str:
        return self.full_response

class HTTPClient(object):

    # Checks the scheme of the provided URL, ensures that it is http:\\
    # Parameters:
    #   url - provided URL
    # Returns: True if scheme of URL is http:\\
    def check_url_scheme(self, url):
        schemeCheck = re.match("^(http:\/\/).*", url)
        if schemeCheck == None:
            return False
        return True

    # Checks if the URL has a provided host
    # Parameters:
    #   url - provided URL
    # Returns: True if URL has host
    def check_url_host(self, url):
        urlObject = urllib.parse.urlparse(url)
        return urlObject.hostname != None

    # Extracts the neccesary information from the URL and provided args
    # Parameters:
    #   url - provided URL
    #   args - provided args
    # Returns: host, port, path and query string of URL
    def extract_url_info(self, url, args):
        urlObject = urllib.parse.urlparse(url)
        host = urlObject.hostname
        port = self.get_host_port(urlObject.port)
        path = self.get_path(urlObject.path)
        query = self.get_query_string(urlObject.query, args)
        return host, port, path, query

    # Gets the port which the host is listening
    # Parameters:
    #   port - port returned from urllib.parse.urlparse
    # Returns: Port number
    def get_host_port(self,port):
        if port == None:
            return 80
        else:
            return port

    # Gets requested path 
    # Parameters:
    #   path - path returned from urllib.parse.urlparse
    # Returns: Path
    def get_path(self, path):
        if path == "":
            return "/"
        else:
            return path

    # Gets requested query string
    # Parameters:
    #   query - query returned from urllib.parse.urlparse
    #   args - provided args
    # Returns: Query string
    def get_query_string(self, query, args):
        if args != None:
            return "?" + self.extract_query_from_args(args) + query
        elif query != "":
            return "?" + query 
        else:
            return ""

    # Converts args into a query string
    # Parameters:
    #   args - provided args
    # Returns: Query string
    def extract_query_from_args(self, args):
        queryString = ""
        for arg in args:
            queryString += urllib.parse.quote(arg) + "=" + urllib.parse.quote(args[arg])+"&"
        return queryString[0:-1]

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        dataArray = data.split("\r\n")
        statusLineArray = dataArray[0].split()
        return statusLineArray[1]

    def get_headers(self,data):
        dataArray = data.split("\r\n")
        headers = ""
        for i in range(1, len(dataArray) - 2):
            headers += dataArray[i] + "\r\n"
        return headers

    def get_body(self, data):
        dataArray = data.split("\r\n")
        return dataArray[-1]
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

  
    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        host, port, path, query = self.extract_url_info(url, args)
        try:
            self.connect(host, port)
        except: 
            return "Failed to connect to host at specfied port"
        requestString = "{method} {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: httpclient/1.0\r\nAccept: */*\r\nConnection: close\r\n\r\n"
        self.sendall(requestString.format(method="GET", 
                                          path=path+query, 
                                          host=host))
        response = self.recvall(self.socket)
        self.close()
        code = int(self.get_code(response))
        body = self.get_body(response)
        return HTTPResponse(code, body, response)

    def POST(self, url, args=None):
        host, port, path, query = self.extract_url_info(url, None)
        try:
            self.connect(host, port)
        except: 
            return "Failed to connect to host at specfied port"
        requestBody = ""
        if args != None:
            requestBody = self.extract_query_from_args(args)
        contentLength = len(requestBody)
        requestString = "{method} {path} HTTP/1.1\r\nHost: {host}\r\nContent-Type: {contentType}; charset=utf-8\r\nContent-Length: {length}\r\nConnection: close\r\n\r\n"
        requestString = requestString.format(method="POST", 
                                             path=path+query, 
                                             host=host,
                                             contentType="application/x-www-form-urlencoded",
                                             length=contentLength)
        requestString += requestBody
        self.sendall(requestString)
        response = self.recvall(self.socket)
        self.close()
        code = int(self.get_code(response))
        body = self.get_body(response)
        return HTTPResponse(code, body, response)

    def command(self, url, command="GET", args=None):
        if (not self.check_url_scheme(url)):
            return "Wrong URL Scheme. Please enter the URL again"
        if (not self.check_url_host(url)):
            return "No host specfied. Please enter the URL again"
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
