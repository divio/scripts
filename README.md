# Scripts

A collection of helpful scripts for automating tasks and enhancing workflows on the Divio cloud platform.

## Export logs script

The `export-logs.py` script in this repository allows you to retrieve and display logs from a specified Divio environment for a given
 date range. It uses the Divio API to fetch the logs and displays them on the console and saves them to a text file for easy search 
and analysis.

Copy and run the `export-logs.py` script with the following command, replacing with the desired starting and ending date and time, and
 providing the required command-line arguments, the environment slug, the application uuid, and your API token:

`python export-logs.py "2023-08-13T00:00" "2023-08-13T23:00" "live" "APPLICATION_UUID" "YOUR_API_TOKEN"`

For detailed instructions on how to use the `export-logs.py` script, please refer to the [How to Export Logs guide in the documentation](https://docs.divio.com/en/latest/how-to/export-logs/). 


## CI-CD workflow script

The CI-CD workflow script included in this repository simplifies the deployment process of your Divio applications using a single Python script. It offers flexibility in deploying your code while supporting various deployment scenarios, such as creating new environments in existing or creating new branches, and more.

### Requirements

Before using the CI-CD workflow script, ensure you have the following prerequisites:

1. Python 3.x

2. Dependencies: Install the necessary Python libraries by running the following command:

   ```bash
   pip install requests gitpython

To deploy your Divio application using the CI-CD workflow script, run the script with the following command:

`python ci-cd.py "APPLICATION_UUID" "YOUR_API_TOKEN" [--env_slug ENV_SLUG] [--branch BRANCH] [--repository_path REPO_PATH] [--source_env_slug SOURCE_ENV_SLUG]`

Replace the placeholders with the appropriate values:

* `"APPLICATION_UUID"`: The UUID of your Divio application.
* `"YOUR_API_TOKEN"`: Your Divio API token.
* `ENV_SLUG` (optional): The environment slug (default: "test").
* `BRANCH` (optional): The branch name.
* `REPO_PATH` (optional): The local repository path (required when creating a new branch).
* `SOURCE_ENV_SLUG` (optional): The source environment slug for copying (default: "live").

Refer to the [Simplify your Divio application deployment with a Python script](https://docs.divio.com/en/latest/how-to/ci-cd/) for detailed instructions on how to use the `ci-cd.py` script.
