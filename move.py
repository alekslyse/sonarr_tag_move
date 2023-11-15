import requests
import urllib3
import logging

# Setup logging
LOG_LEVEL = logging.INFO  # Change this to your desired log level
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')


# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
SONARR_API_URL = 'https://url.to.sonarr/api/v3'  # Replace with your Sonarr URL
SONARR_API_KEY = 'sonarr_api_key'  # Replace with your Sonarr API key
TAG_NAME = 'tag_to_look_for'  # Replace with your desired tag name
NEW_ROOT_FOLDER = 'destination_root_folder' # Need to be a root folder that already exist in sonarr
TEST_SERIES_TITLE = ''  # Leave empty to check all series

# Headers for API requests
headers = {
    'X-Api-Key': SONARR_API_KEY
}

# Log request and response details
def log_request_response(response):
    logging.debug(f"Request URL: {response.request.url}")
    logging.debug(f"Request Method: {response.request.method}")
    logging.debug(f"Request Headers: {response.request.headers}")
    if response.request.body:
        logging.debug(f"Request Body: {response.request.body}")
    logging.debug(f"Response Status Code: {response.status_code}")
    logging.debug(f"Response Content: {response.text}")

# Get the list of series from Sonarr
def get_series():
    logging.info("Fetching series from Sonarr...")
    url = f"{SONARR_API_URL}/series"
    response = requests.get(url, headers=headers, verify=False)
    log_request_response(response)
    return response.json()

# Get the list of tags from Sonarr
def get_tags():
    logging.info("Fetching tags from Sonarr...")
    url = f"{SONARR_API_URL}/tag"
    response = requests.get(url, headers=headers, verify=False)
    log_request_response(response)
    return {tag['id']: tag['label'] for tag in response.json()}

# Get root folders from Sonarr
def get_root_folders():
    logging.info("Fetching root folders from Sonarr...")
    url = f"{SONARR_API_URL}/rootfolder"
    response = requests.get(url, headers=headers, verify=False)
    log_request_response(response)
    return response.json()

# Find the root folder id for a specific tag and root folder path
def find_tag_root_folder_id(root_folders, tag_name, new_root_folder_path):
    logging.info(f"Finding root folder ID for {new_root_folder_path}...")
    for folder in root_folders:
        if folder['path'] == new_root_folder_path:
            return folder['id']
    return None

# Update the series root folder and path
def update_series_root_folder(series, new_root_folder_id, new_root_folder_path):
    logging.info(f"Updating root folder for series: {series['title']}")
    series['rootFolderPath'] = new_root_folder_path
    series['rootFolderId'] = new_root_folder_id
    series['path'] = f"{new_root_folder_path}/{series['title']}"  # Update the path as well

    url = f"{SONARR_API_URL}/series/{series['id']}"
    response = requests.put(
        url,
        json=series,
        headers=headers,
        params={'moveFiles': True},
        verify=False
    )
    log_request_response(response)
    return response.status_code

# Main script execution
def main():
    series_list = get_series()
    tags = get_tags()
    root_folders = get_root_folders()
    tag_id = next((id for id, label in tags.items() if label == TAG_NAME), None)

    if tag_id is None:
        logging.error("Required configuration not found.")
        return

    for series in series_list:
        if not TEST_SERIES_TITLE or series['title'] == TEST_SERIES_TITLE:
            logging.debug(f"Processing series: {series['title']}")
            if tag_id in series.get('tags', []) and NEW_ROOT_FOLDER in series['rootFolderPath']:
                # Check if the new root folder path is contained in the existing root folder path
                logging.info(f"Series '{series['title']}' is already in the correct root folder.")
            elif tag_id in series.get('tags', []):
                status_code = update_series_root_folder(series, tag_id, NEW_ROOT_FOLDER)
                if status_code == 202:
                    logging.info(f"Successfully updated root folder for series: {series['title']}")
                else:
                    logging.error(f"Failed to update series: {series['title']} - Status Code: {status_code}")
            else:
                logging.warning(f"Series '{series['title']}' does not have the '{TAG_NAME}' tag.")

if __name__ == "__main__":
    main()
