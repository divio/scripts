#!/usr/bin/env python3

import argparse
import requests
from time import sleep
import git  # Import the GitPython library

# Constants and Configuration
ENV_URL = "https://api.divio.com/apps/v3/environments/"
DEPLOY_URL = "https://api.divio.com/apps/v3/deployments/"
SLEEP_INTERVAL = 5  # Sleep interval between deployment status checks

# Check if a branch exists in the Git repository
def branch_exists(repo, branch_name):
    try:
        repo.git.rev_parse("--verify", f"refs/heads/{branch_name}")
        return True
    except git.exc.GitCommandError:
        return False


# Create a new branch and push it to the remote repository
def create_and_push_branch(repo, branch_name, repository_path):
    if branch_exists(repo, branch_name):
        print(f"Branch '{branch_name}' already exists.")
    else:
        # Check if the repository_path is provided when creating a new branch
        if not repository_path:
            print("Error: repository_path must be provided when creating a new branch.")
            exit(1)

        new_branch = repo.create_head(branch_name)
        repo.git.checkout(new_branch)
        print(f"Branch '{branch_name}' created and switched to.")
        repo.git.push("origin", new_branch.name)
        sleep(SLEEP_INTERVAL)


# Check if an environment with the given slug exists for the specified application
def environment_exists(app_uuid, env_slug, headers):
    # Prepare parameters for the API request
    env_params = {"application": app_uuid}

    # Send a GET request to retrieve the list of environments for the application
    env_response = requests.get(url=ENV_URL, params=env_params, headers=headers)

    # Iterate through the list of environments to find a match with the provided slug
    for env in env_response.json()["results"]:
        if env["slug"] == env_slug:
            return True  # Found a matching environment slug

    return False  # No matching environment slug was found

# Get the environment uuid for the given environment slug
def get_environment_uuid(app_uuid, env_slug, headers):
    env_params = {"application": app_uuid}
    env_response = requests.get(url=ENV_URL, params=env_params, headers=headers)

    for env in env_response.json()["results"]:
        if env["slug"] == env_slug:
            return env["uuid"]

    return None


# Copy source environment to a new environment with the specified slug
def copy_environment(app_uuid, source_env_uuid, env_slug, headers):
    copy_url = f"{ENV_URL}{source_env_uuid}/copy/"

    env_data = {"new_slug": env_slug}
    copy_response = requests.post(url=copy_url, data=env_data, headers=headers)

    # Check if the limit of the number of environments is reached
    if "non_field_errors" in copy_response.json():
        if "Can not add another Environment." in copy_response.json()["non_field_errors"]:
            print("Error: Maximum number of environments reached.")
            exit(1)
            
    new_env_uuid = copy_response.json()["uuid"]
    return new_env_uuid


# Update the environment to switch to a different branch
def update_environment_branch(env_uuid, branch, headers):
    env_data = {"branch": branch}
    update_env_url = f"{ENV_URL}{env_uuid}/"
    requests.patch(url=update_env_url, data=env_data, headers=headers)


# Trigger deployment for a specific environment and return the deployment UUID
def trigger_deployment(env_uuid, headers):
    deploy_data = {"environment": env_uuid}
    deploy_post_response = requests.post(
        url=DEPLOY_URL, data=deploy_data, headers=headers
    )
    deploy_uuid = deploy_post_response.json()["uuid"]
    return deploy_uuid


# Function to get deployment status
def get_deployment_status(deploy_uuid, headers):
    get_deployment_url = f"{DEPLOY_URL}{deploy_uuid}/"

    while True:
        # Continuously check the deployment status and success status
        get_deploy_response = requests.get(url=get_deployment_url, headers=headers)
        response_json = get_deploy_response.json()
        status = response_json.get("status")
        success = response_json.get("success")

        # If the success status is not None, it indicates the final deployment status
        # If success is True, the deployment has completed successfully
        # If success is False, the deployment has failed, so return the appropriate message
        if success is not None:
            if success:
                return "Deployment has completed successfully"
            else:
                return "Deployment has failed, please check the Deployment logs"

        # Print the current deployment status and wait for a specified interval before checking again
        print("Deployment", status)
        sleep(SLEEP_INTERVAL)


def deploy_environment(
    app_uuid, env_slug, branch, repository_path, source_env_slug, headers
):
    # Initialize the Git repository if a branch is provided
    if branch:
        repo = git.Repo(repository_path)
        create_and_push_branch(repo, branch, repository_path)

    # Get the UUID of the environment using the provided environment slug
    env_uuid = get_environment_uuid(app_uuid, env_slug, headers)

    # If the environment with the given slug does not exist
    if env_uuid is None:
        # Get the UUID of the source environment using the provided source_env_slug
        source_env_uuid = get_environment_uuid(app_uuid, source_env_slug, headers)

        # If the source environment does not exist, print an error message and exit
        if source_env_uuid is None:
            print(
                f"Could not find the source environment {source_env_slug} to copy from."
            )
            exit(1)

        # Copy the source environment to a new environment with the specified slug
        new_env_uuid = copy_environment(app_uuid, source_env_uuid, env_slug, headers)

        # If a branch is provided, update the new environment to switch to the newly created branch
        if branch:
            update_environment_branch(new_env_uuid, branch, headers)

        # Trigger deployment for the new environment
        deploy_uuid = trigger_deployment(new_env_uuid, headers)
    else:
        # If no branch is provided, trigger deployment for the existing environment
        if not branch:
            deploy_uuid = trigger_deployment(env_uuid, headers)
        else:
            # If a branch is provided and the environment with the given slug already exists
            print(
                f"Environment with {env_slug} exists. Please do not provide a branch argument"
            )
            exit(1)

    return deploy_uuid


# Deploy default environment
def deploy_default_environment(app_uuid, env_slug, headers):
    # Get the UUID of the default environment using the provided environment slug
    default_env_uuid = get_environment_uuid(app_uuid, env_slug, headers)

    # If the default environment does not exist, print an error message and exit
    if default_env_uuid is None:
        print(f"Could not find the default environment {env_slug}")
        exit(1)

    # Trigger deployment for the default environment
    deploy_uuid = trigger_deployment(default_env_uuid, headers)
    return deploy_uuid


# Main function for deploying Divio application
def main():
    # Define command-line argument parser with description for the script
    parser = argparse.ArgumentParser(description="Deploy script for Divio application")

    # Define command-line arguments
    parser.add_argument("app_uuid", help="Application UUID")
    parser.add_argument("api_token", help="API Token")
    parser.add_argument("--env_slug", help="Environment slug", default="test")
    parser.add_argument("--branch", help="Branch name")
    parser.add_argument("--repository_path", help="Local repository path")
    parser.add_argument(
        "--source_env_slug", help="Source environment slug for copying", default="live"
    )

    # Parse the provided command-line arguments
    args = parser.parse_args()

    # Define headers for API requests using the provided API token
    headers = {"Authorization": f"Token {args.api_token}"}

    deploy_uuid = None

    # Check if the environment slug is provided
    if args.env_slug:
        deploy_uuid = deploy_environment(
            args.app_uuid, args.env_slug, args.branch, args.repository_path, args.source_env_slug, headers
        )

    else:
        # Deploy default environment
        deploy_uuid = deploy_default_environment(args.app_uuid, args.env_slug, headers)

    # Get and print the deployment status
    deployment_status = get_deployment_status(deploy_uuid, headers)
    print(deployment_status)


if __name__ == "__main__":
    main()
