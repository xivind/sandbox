#!/usr/bin/env python3
"""
Module to get initial oauth2 secrets for Strava. Based on:
https://github.com/tekksparrow-programs/simple-api-strava/blob/main/simple-api-strava.py
"""

from requests_oauthlib import OAuth2Session

# Set local id, secret, and redirect_url variables, DO NOT PUSH TO REPOSITORY
client_id = ""
client_secret = ""
redirect_url = ""

# Create session variable
session = OAuth2Session(client_id=client_id, redirect_uri=redirect_url)

# Set auth url and scope variables
# Details about scopes https://developers.strava.com/docs/authentication/
auth_base_url = "https://www.strava.com/oauth/authorize"
session.scope = ["activity:read_all,activity:write"]
auth_link = session.authorization_url(auth_base_url)

# Print auth link and accept input
print(f"Click Here: {auth_link[0]}")
redirect_response = input("Paste redirect url here: ")

# Get oauth token
token_url = "https://www.strava.com/api/v3/oauth/token"
tokens = session.fetch_token(
    token_url=token_url,
    client_id=client_id,
    client_secret=client_secret,
    authorization_response=redirect_response,
    include_client_id=True
    )

# Print tokens
print("\nToken information:\n")
print(tokens)
