# BloodHound CE Saved Query Tool
Simple script that interacts with a BloodHound CE API to post user-generated (custom) Cypher queries to be used within the BloodHound CE web app. The script will parse a JSON file containing the queries and post them to a BloodHound CE API. 

## ⚠️ Important
You will need to [obtain API credentials](https://support.bloodhoundenterprise.io/hc/en-us/articles/11311053342619-Working-with-the-BloodHound-API#h_01HQBFQX7EE8SZHPPFF0KMQ6NG) from within the application before using this script.

You have two options for implementing the credentials for use in the script:
- Pass them on the command line with the `--id` and `--key` arguments.
- Modify the script and place them in the provided hard-coded variables.

If the command line arguments for the API credentials are supplied, those will take precendence over the hard-coded variables.

### Other Notes
- The API endpoint is rate limited to 55 calls per second, which is why I implemented a short pause after the first 54 calls. You don't need to worry about this if you have less than 55 queries in your JSON file.
- This may be obvious, but your queries can't have the same name. If they do, the API will respond with an error for that call. Name your queries with unique names to prevent any issues. 

## Arguments
```shell
--json-file		Path to the JSON file containing the queries
--endpoint 		Endpoint to post the queries to (e.g., 10.10.10.199:8080)
--key			Key for generating the bearer token
--id			ID for generating the bearer token
```

## Example Usage
```shell
# Example with hardcoded credentials
python3 bh-query-tool.py --endpoint https://10.10.10.12:8080 --json-file user-queries.json 

# Example with id and key args
python3 bh-query-tool.py --endpoint https://10.10.10.12:8080 --json-file user-queries.json --id 8d2419e8-819d-4f5f-925d-a04ee817d78c --key V2h5IHdvdWxkIHlvdSBkZWNvZGUgdGhpcz8hPyE/ISEhISEhIQ==
```

## Expected Format of JSON File (See example file in repo.)
```json
{
    "queries": [
      {
        "name": "Domains",
        "query": "MATCH (d:Domain) RETURN d"
      }
    ]
}
```

If you'd like to expand on any functionality, PRs are open. 

Thank you to SpectorOps for providing BloodHound CE to the community.