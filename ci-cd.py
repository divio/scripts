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
def create_and_push_branch(repo, branch_name):
    if branch_exists(repo, branch_name):
        print(f"Branch '{branch_name}' already exists.")
    else:
        new_branch = repo.create_head(branch_name)
        repo.git.checkout(new_branch)
        print(f"Branch '{branch_name}' created and switched to.")
        repo.git.push("origin", new_branch.name)

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
    deploy_post_response = requests.post(url=DEPLOY_URL, data=deploy_data, headers=headers)
    deploy_uuid = deploy_post_response.json()['uuid']
    return deploy_uuid

# Function to get deployment status
def get_deployment_status(deploy_uuid, headers):
    get_deployment_url = f"{DEPLOY_URL}{deploy_uuid}/"
    
    while True:
        # Continuously check the deployment status by sending a GET request to the deployment URL
        # Retrieve the response JSON and extract the deployment status and success status
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


def deploy_with_branch(repo, app_uuid, env_slug, source_env_slug, branch, headers):
    create_and_push_branch(repo, branch)
    env_uuid = get_environment_uuid(app_uuid, env_slug, headers)
    
    if env_uuid is None:
        source_env_uuid = get_environment_uuid(app_uuid, source_env_slug, headers)
        if source_env_uuid is None:
            print(f"Could not find the source environment {source_env_slug} to copy from.")
            exit(1)
        
        new_env_uuid = copy_environment(app_uuid, source_env_uuid, env_slug, headers)
        print("New environment UUID:", new_env_uuid)  # Add this line
        update_environment_branch(new_env_uuid, branch, headers)
        deploy_uuid = trigger_deployment(new_env_uuid, headers)
    else:
        print(f"Environment with {env_slug} exists. Please do not provide a branch argument")
        exit(1)
    
    return deploy_uuid

def deploy_without_branch(app_uuid, env_slug, source_env_slug, headers):
    env_uuid = get_environment_uuid(app_uuid, env_slug, headers)
    
    if env_uuid is None:
        source_env_uuid = get_environment_uuid(app_uuid, source_env_slug, headers)
        if source_env_uuid is None:
            print(f"Could not find the source environment {source_env_slug} to copy from.")
            exit(1)
        
        new_env_uuid = copy_environment(app_uuid, source_env_uuid, env_slug, headers)
        deploy_uuid = trigger_deployment(new_env_uuid, headers)
    else:
        deploy_uuid = trigger_deployment(env_uuid, headers)
    
    return deploy_uuid

def deploy_default_environment(app_uuid, env_slug, headers):
    default_env_uuid = get_environment_uuid(app_uuid, env_slug, headers)
    
    if default_env_uuid is None:
        print(f"Could not find the default environment {env_slug}")
        exit(1)
    
    deploy_uuid = trigger_deployment(env_uuid, headers)
    return deploy_uuid

def main():
    parser = argparse.ArgumentParser(description="Deploy script for Divio application")
    parser.add_argument("app_uuid", help="Application UUID")
    parser.add_argument("api_token", help="API Token")
    parser.add_argument("--env_slug", help="Environment slug", default="test")
    parser.add_argument("--branch", help="Branch name")
    parser.add_argument("--repository_path", help="Local repository path")
    parser.add_argument("--source_env_slug", help="Source environment slug for copying", default="live")

    args = parser.parse_args()
    
    # Parse command-line arguments
    app_uuid = args.app_uuid
    api_token = args.api_token
    env_slug = args.env_slug
    branch = args.branch
    repository_path = args.repository_path
    source_env_slug = args.source_env_slug
    
    headers = {"Authorization": f"Token {api_token}"}
    
    deploy_uuid = None
    
    if env_slug:
        if branch:
            repo = git.Repo(repository_path)
            deploy_uuid = deploy_with_branch(repo, app_uuid, env_slug, source_env_slug, branch, headers)
        else:
            deploy_uuid = deploy_without_branch(app_uuid, env_slug, source_env_slug, headers)
    else:
        deploy_uuid = deploy_default_environment(app_uuid, env_slug, headers)
    
    deployment_status = get_deployment_status(deploy_uuid, headers)
    print(deployment_status)

if __name__ == "__main__":
    main()
