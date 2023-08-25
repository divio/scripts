#!/usr/bin/env python3

import sys
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

# # Check if an environment with the given slug exists
# def environment_exists(app_uuid, env_slug, headers):
#     env_params = {"application": app_uuid}
#     env_response = requests.get(url=ENV_URL, params=env_params, headers=headers)
    
#     for env in env_response.json()["results"]:
#         if env["slug"] == env_slug:
#             return True
    
#     return False

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

def main():
    # Check the number of command-line arguments to ensure the minimum required arguments are provided
    if len(sys.argv) < 3:
        print("Usage: script.py <APPLICATION_UUID> <API_TOKEN> [<ENVIRONMENT_SLUG>] [<BRANCH_NAME>]")
        sys.exit(1)
    
    # Parse command-line arguments
    app_uuid = sys.argv[1]
    api_token = sys.argv[2]
    
    # Define constants and configuration options
    repository_path = "/Users/mebzete/divioprojects/github-actions"  # local repository path
    headers = {"Authorization": f"Token {api_token}"}
    default_env_slug = "test"  # Default environment slug to deploy, if env_slug is not provided
    source_env_slug = "live" # Source environment slug for the environment to copy from
    
    # Check if an environment slug argument is provided (third argument) and parse env_slug accordingly
    if len(sys.argv) >= 4:
        env_slug = sys.argv[3]
    
        # Check if a branch argument is provided (fourth argument) and parse branch accordingly
        if len(sys.argv) >= 5:
            branch = sys.argv[4] 
        
            # Initialize the Git repository
            repo = git.Repo(repository_path)
            
            # Create and push the specified branch
            create_and_push_branch(repo, branch)
            
            # Get the UUID of the environment using the provided environment slug
            env_uuid = get_environment_uuid(app_uuid, env_slug, headers)
            
            if env_uuid is None:
                # The environment with the given slug does not exist,
                # Get the UUID of the source environment using the application UUID and its slug
                source_env_uuid = get_environment_uuid(app_uuid, source_env_slug, headers)
                
                # Check if the UUID is None, the source environment could not be found, so print an error message and exit the script
                if source_env_uuid is None:
                    print(f"Could not find the source environment {source_env_slug} to copy from.")
                    sys.exit(1)
                
                # Copy the source environment to a new environment
                new_env_uuid = copy_environment(app_uuid, source_env_uuid, env_slug, headers)
                
                # Update the environment to switch to the newly created branch
                update_environment_branch(new_env_uuid, branch, headers)
                
                # Trigger deployment for the updated environment
                deploy_uuid = trigger_deployment(new_env_uuid, headers)
                print(f"Deployment triggered with UUID: {deploy_uuid}")
                
                # Get the deployment status
                deployment_status = get_deployment_status(deploy_uuid, headers)
                print(deployment_status)
            
            else:
                # An environment with the given slug exists, and a branch is also provided;
                # Exit the script to prevent overwriting the existing environment's branch.
                print(f"Environment with {env_slug} exists. Please do not provide a branch argument")
                sys.exit(1)
            
        else:
            # A branch argument is not provided 
            
            # Get the UUID of the environment using the provided environment slug
            env_uuid = get_environment_uuid(app_uuid, env_slug, headers)
            
            if env_uuid is None:
                # The environment with the given slug does not exist,
                # Get the UUID of the source environment using the application UUID and its slug
                source_env_uuid = get_environment_uuid(app_uuid, source_env_slug, headers)
                
                # Check if the UUID is None, the source environment could not be found, so print an error message and exit the script
                if source_env_uuid is None:
                    print(f"Could not find the source environment {source_env_slug} to copy from.")
                    sys.exit(1)
                
                # Copy the source environment to a new environment
                new_env_uuid = copy_environment(app_uuid, source_env_uuid, env_slug, headers)
                
                # Trigger deployment for the updated environment
                deploy_uuid = trigger_deployment(new_env_uuid, headers)
                print(f"Deployment triggered with UUID: {deploy_uuid}")
                
                # Get the deployment status
                deployment_status = get_deployment_status(deploy_uuid, headers)
                print(deployment_status)
            
            else:
                # An environment with the given slug exists, and a branch is not provided;
            
                # deploy the environment with given uuid
                deploy_uuid = trigger_deployment(env_uuid, headers)
                print(f"Deployment triggered with UUID: {deploy_uuid}")
                
                # Get the deployment status
                deployment_status = get_deployment_status(deploy_uuid, headers)
                print(deployment_status)
        
    else:
        # Only application UUID and API token are given
        
        # Get the UUID of the default environment using the application UUID
        default_env_uuid = get_environment_uuid(app_uuid, default_env_slug, headers)
        
        # Check if the UUID is None, the default environment could not be found, so print an error message and exit the script
        if default_env_uuid is None:
            print(f"Could not find the default environment {default_env_slug}")
            sys.exit(1)
            
        # Get the UUID of the default environment using the application uuid and the default environment slug 
        default_env_uuid = get_environment_uuid(app_uuid, default_env_slug, headers)
        
        # Trigger deployment for the newly copied environment
        deploy_uuid = trigger_deployment(default_env_uuid, headers)
        print(f"Deployment triggered with UUID: {deploy_uuid}")
        
        # Get the deployment status
        deployment_status = get_deployment_status(deploy_uuid, headers)
        print(deployment_status)

if __name__ == "__main__":
    main()
