# scripts

A collection of helpful scripts for automating tasks and enhancing workflows on the Divio cloud platform.

Export Logs Script

The export-logs.py script in this repository allows you to retrieve and display logs from a specified Divio environment for a given
 date range. It uses the Divio API to fetch the logs and displays them on the console and saves them to a text file for easy search 
and analysis.

Run the script with the following command, replacing with the desired starting and ending date and time, and providing the required
 command-line arguments:

`python export-logs.py "2023-08-13T00:00" "2023-08-13T23:00" "live" "APPLICATION_UUID" "YOUR_API_TOKEN"`

For detailed instructions on how to use the export-logs.py script, please refer to the How to Export Logs guide in the documentation
 https://docs.divio.com/en/latest/how-to/export-logs/. 

