#!/usr/bin/env python3 

import hmac
import hashlib
import base64
import requests
import datetime
import json
import argparse
import time

from urllib.parse import urlparse
from typing import Optional

# Based On: https://support.bloodhoundenterprise.io/hc/en-us/article_attachments/24776286827547
                                                                                                     
BHE_TOKEN_ID = "xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"                                                                              
BHE_TOKEN_KEY = ""

class Credentials(object):
    def __init__(self, token_id: str, token_key: str) -> None:
        self.token_id = token_id
        self.token_key = token_key

    def __repr__(self):
        return f"Credentials(token_id={self.token_id}, token_key={self.token_key})"


class APIVersion(object):
    def __init__(self, api_version: str, server_version: str) -> None:
        self.api_version = api_version
        self.server_version = server_version


class Client(object):
    def __init__(self, scheme: str, host: str, port: int, credentials: Credentials) -> None:
        self._scheme = scheme
        self._host = host
        self._port = port
        self._credentials = credentials

    def _format_url(self, uri: str) -> str:
        formatted_uri = uri
        if uri.startswith("/"):
            formatted_uri = formatted_uri[1:]

        return f"{self._scheme}://{self._host}:{self._port}/{formatted_uri}"

    def _request(self, method: str, uri: str, body: Optional[bytes] = None) -> requests.Response:
        digester = hmac.new(self._credentials.token_key.encode(), None, hashlib.sha256)

        digester.update(f"{method}{uri}".encode())

        digester = hmac.new(digester.digest(), None, hashlib.sha256)

        datetime_formatted = datetime.datetime.now().astimezone().isoformat("T")
        digester.update(datetime_formatted[:13].encode())

        digester = hmac.new(digester.digest(), None, hashlib.sha256)

        if body is not None:
            digester.update(body)

        return requests.request(
            method=method,
            url=self._format_url(uri),
            headers={
                "User-Agent": "bhe-python-sdk 0001",
                "Authorization": f"bhesignature {self._credentials.token_id}",
                "RequestDate": datetime_formatted,
                "Signature": base64.b64encode(digester.digest()),
                "Content-Type": "application/json",
            },
            data=body,
        )

    def get_version(self) -> APIVersion:
        response = self._request("GET", "/api/version")
        payload = response.json()
        try: 
            t = APIVersion(api_version=payload["data"]["API"]["current_version"], server_version=payload["data"]["server_version"])
        except Exception as e:
            print(f"Check your credentials!")
            exit()
        return 


    def post_query(self, query_name, query, include_properties=False) -> requests.Response:
        """ Create a User saved query

        Parameters:
        name (string): The name of the Cypher query
        query (string): The Cypher query to save

        """

        data = {
            "name": query_name,
            "query": query
        }
        body = json.dumps(data).encode('utf8')
        response = self._request("POST", "/api/v2/saved-queries", body)
        
        if response.status_code == 201:
            print(f"Query '{query_name}' posted successfully.")
            return response
        else:
            print(f"Failed to post query '{query_name}'. Status code: {response.status_code}")
            print(response.text)
            return response

def parse_url(url):
    """ Parse a URL and return scheme, host, and port. """

    parsed_url = urlparse(url)
    scheme = parsed_url.scheme
    host = parsed_url.hostname
    port = parsed_url.port if parsed_url.port else (443 if scheme == 'https' else 80)
    
    return scheme, host, port

def validate_query_names(queries):
    """Validate that all query names are unique."""
    name_counts = {}
    
    for query in queries:
        name = query['name']
        if name in name_counts:
            name_counts[name] += 1
        else:
            name_counts[name] = 1
    
    duplicates = [name for name, count in name_counts.items() if count > 1]
    
    if duplicates:
        print("Duplicate names found in the provided JSON file:")
        for duplicate in duplicates:
            print(f" - {duplicate}")
        raise ValueError("Duplicate names found! The API will reject duplicate names.")
    
    print("All query names are unique.")

def main():
    
    parser = argparse.ArgumentParser(description='Posts BloodHound custom queries to a BloodHound CE API.')
    parser.add_argument('--json-file', required=True, help='Path to the JSON file containing the queries.')
    parser.add_argument('--endpoint', required=True, help='Endpoint to post the queries to (e.g., https://10.10.10.199:8080)')
    parser.add_argument('--key', required=False, help='Key for generating the bearer token')
    parser.add_argument('--id', required=False, help='ID for generating the bearer token')
    args = parser.parse_args()
 
    # May implement loading this from a local file as an option. TBD. 
    credentials = Credentials(
        token_id=args.id if args.id else BHE_TOKEN_ID,
        token_key=args.key if args.key else BHE_TOKEN_KEY,
    )

    if args.endpoint:
        scheme, host, port = parse_url(args.endpoint)

    client = Client(scheme, host, port, credentials=credentials)
    version = client.get_version()

    print("BloodHound User Query Upload Tool")
    print(f"API version: {version.api_version} - Server version: {version.server_version}\n")

    with open(args.json_file, 'r') as file:
        data = json.load(file)
        queries = data['queries']

    try:
        validate_query_names(queries)
    except ValueError as e:
        print(e)
        return  

    call_limit = 54
    call_count = 0

    for query in queries:
        client.post_query(query['name'], query['query'])
        call_count += 1

        if call_count % call_limit == 0:
            print(f"Reached {call_count} calls. Pausing for 1 second...")
            time.sleep(1)  

if __name__ == "__main__":
    main()
