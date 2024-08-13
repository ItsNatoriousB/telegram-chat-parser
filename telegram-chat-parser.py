import csv
import json
import logging
import os
import re
import sys
import string
from datetime import datetime
from pathvalidate import sanitize_filename
from emoji import replace_emoji
from argparse import ArgumentParser

def clean_text(text):
    """Removes emojis, special characters, and unnecessary text formatting from a given string."""
    # Remove emojis and any non-word characters, except spaces, colons, hyphens, and slashes
    clean_text = re.sub(r'[^\w\s:/\-]', '', text)
    # Remove leading and trailing whitespaces and newlines
    return clean_text.strip()

# Checking and creating folders
def check_and_create_folders():
    """Checks if 'photos' and 'video_files' folders exist, creates them if not, and stores their paths."""

    required_folders = ["photos", "video_files"]
    for folder in required_folders:
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
                print(f"Folder '{folder}' created successfully.")
            except OSError as e:
                print(f"Error: Could not create folder '{folder}' - {e}")
                sys.exit(1)

    global photos_folder, videos_folder
    photos_folder = os.path.join(os.getcwd(), "photos")
    videos_folder = os.path.join(os.getcwd(), "video_files")

# Loading or creating file lists
def load_or_create_file_list(folder_path, filename):
    """Loads filenames from a text file if it exists, otherwise creates an empty set.
    Adds filenames from the folder that are not already in the set, sorts the list, and returns it."""

    file_path = os.path.join(folder_path, filename)
    filenames = set()

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            filenames = set(line.strip() for line in f)

    for file in os.listdir(folder_path):
        basename = os.path.basename(file)
        if basename not in filenames:
            filenames.add(basename)

    return sorted(list(filenames))

# Finding and processing the JSON file
def find_and_process_json():
    possible_files = ["result.json", "results.json"]
    json_file_path = None

    # Check if the JSON file exists in the current directory
    for filename in possible_files:
        if os.path.exists(filename):
            json_file_path = filename
            break

    if not json_file_path:
        print("No JSON file found. Please ensure 'result.json' or 'results.json' is in the current directory.")
        sys.exit(1)

    # Process the found JSON file
    process_json_messages(json_file_path)

# Handling the processing based on file existence
def handle_file_existence():
    """Handles processing based on the existence of msg_ids files."""
    photos_ids, videos_ids, all_msg_ids = set(), set(), set()

    files_check = {
        "photos_exists": os.path.exists("msg_ids-photos.txt"),
        "videos_exists": os.path.exists("msg_ids-videos.txt"),
        "all_ids_exists": os.path.exists("msg_ids.txt"),
    }

    if not files_check["all_ids_exists"]:
        print("msg_ids.txt does not exist. It will be created after processing.")

    if not files_check["photos_exists"]:
        print("msg_ids-photos.txt does not exist. It will be created after processing.")

    if not files_check["videos_exists"]:
        print("msg_ids-videos.txt does not exist. It will be created after processing.")

    # Find and process the JSON file
    find_and_process_json(photos_ids, videos_ids, all_msg_ids)

    # Write the sets to their respective files
    if not files_check["photos_exists"]:
        with open("msg_ids-photos.txt", "w") as photos_file:
            for photo_id in sorted(photos_ids):
                photos_file.write(f"{photo_id}\n")

    if not files_check["videos_exists"]:
        with open("msg_ids-videos.txt", "w") as videos_file:
            for video_id in sorted(videos_ids):
                videos_file.write(f"{video_id}\n")

    if not files_check["all_ids_exists"]:
        with open("msg_ids.txt", "w") as all_ids_file:
            for msg_id in sorted(all_msg_ids):
                all_ids_file.write(f"{msg_id}\n")

# Reading and processing the JSON file with messages
def process_json_messages(file_path, photos_ids, videos_ids, all_msg_ids):
    with open(file_path, "r") as f:
        messages = json.load(f)

    for message in messages:
        message_id = message.get("id")
        raw_date = message.get("date")
        mime_type = message.get("mime_type")
        text_blocks = message.get("text", [])

        # Convert date to MM/DD/YYYY
        try:
            formatted_date = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S").strftime("%m/%d/%Y")
        except ValueError:
            formatted_date = "Unknown Date"

        print(f"Message ID: {message_id}, Date: {formatted_date}")

        # Add to the global set of all message IDs
        all_msg_ids.add(message_id)

        # Separate message IDs based on mime_type
        if mime_type and "image" in mime_type:
            photos_ids.add(message_id)
        elif mime_type and "video" in mime_type:
            videos_ids.add(message_id)
        else:
            continue
        
        # Extract "Strain:", "Type:", and "Genetics:" information
        strain_name = strain_type = genetics = None

        for i, block in enumerate(text_blocks):
            if isinstance(block, dict) and "text" in block:
                clean_block = clean_text(block["text"])
                if "Strain:" in clean_block:
                    strain_name = clean_block.replace("Strain:", "").strip()
                elif "Type:" in clean_block:
                    strain_type = clean_block.replace("Type:", "").strip()
                elif "Genetics:" in clean_block:
                    genetics = clean_block.replace("Genetics:", "").strip()

if __name__ == "__main__":
    # Check and create folders
    check_and_create_folders()

    # Handle file existence and process messages
    handle_file_existence()
