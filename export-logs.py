#!/usr/bin/env python3

import os
import requests
import urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env-local file
load_dotenv('.env-local')

# Access the API token, stored in the .env-local file as API_TOKEN
api_token = os.getenv('API_TOKEN')

# Defining authentication headers
headers = {"Authorization": f"Token {api_token}"}

# API-endpoint for environments
ENV_URL = "https://api.divio.com/apps/v3/environments/"

# Customer-provided values for the script
from_ts = "YYYY-MM-DDThh:mm"  # Replace with desired start date and time
to_ts = "YYYY-MM-DDThh:mm"  # Replace with desired end date and time
env_slug = ""  # Replace with the environment slug (e.g., "live" or "test")
app_uuid = ""  # Replace with the application UUID

# Function to get the environment UUID for the given environment slug
def get_env_uuid(env_slug, app_uuid):
    """
    Retrieves the environment UUID for the given environment slug and application UUID.

    Parameters:
        env_slug (str): The slug of the environment (e.g., "live" or "test").
        app_uuid (str): The UUID of the application.

    Returns:
        str: The UUID of the environment, or None if not found.
    """
    # Defining a params dictionary with the application UUID
    env_params = {"application": app_uuid}

    # Listing the environments of the given application
    env_response = requests.get(url=ENV_URL, params=env_params, headers=headers)

    # Iterating through the list of environments to get the uuid with the given environment slug
    for env in env_response.json()["results"]:
        if env["slug"] == env_slug:
            return env["uuid"]

    return None

# Get the environment UUID for the given environment slug
env_uuid = get_env_uuid(env_slug, app_uuid)

# Function to truncate microseconds from a timestamp
def truncate_microseconds(timestamp):
    """
    Truncates the microseconds part from a timestamp string.

    Parameters:
        timestamp (str): The timestamp string to be truncated.

    Returns:
        str: The truncated timestamp without microseconds (up to milliseconds precision).
    """
    if "." in timestamp:
        return timestamp[:timestamp.index(".") + 3]  # Truncate to two decimal places
    return timestamp

# Function to export and display logs of a given environment
def get_all_logs(env_uuid):
    """
    Retrieves and displays logs from a specified environment for a given range of date and time.

    The function constructs the URL with the specified range of date and time and queries the Divio API to fetch the logs.

    The logs are displayed in reverse chronological order, printing each log's timestamp and message.
    The function paginates through the log data to fetch all the available logs.

    Parameters:
        env_uuid (str): The UUID of the environment.

    Returns:
        None
    """

    # Construct the URL with query parameters
    logs_params = {
        'from_ts': from_ts,
        'to_ts': to_ts,
    }
    query_string = urllib.parse.urlencode(logs_params)
    url = f"https://api.divio.com/apps/v3/environments/{env_uuid}/logs/?{query_string}"

    response = requests.get(url=url, headers=headers)

    # Open a file to save the logs (replace 'logs.txt' with your desired file name)
    with open('logs.txt', 'w') as log_file:

        # Main loop to retrieve and display logs
        while True:
            # Fetch the log data from the current URL
            data = response.json()

            # Check for any error messages in the response
            if not "results" in data:
                print(data)

            # Print each log entry in reverse chronological order and save to the file
            for line in data["results"][::-1]:
                # Truncate the microseconds part of the timestamp
                timestamp = truncate_microseconds(line["timestamp"])
                log_entry = f"{timestamp} - {line['message']}\n"
                print(log_entry, end='')  # Print the log entry without a newline
                log_file.write(log_entry)  # Write the log entry to the file

            # Check if there are more log entries in the previous page
            if url != data["previous"]:
                # Update the URL to fetch the previous page
                url = data["previous"]
                # Fetch the log data from the updated URL
                response = requests.get(url=url, headers=headers)
            else:
                # End the loop if there are no more log entries
                return

# Call the function to retrieve and display logs and save them to a file
get_all_logs(env_uuid)
