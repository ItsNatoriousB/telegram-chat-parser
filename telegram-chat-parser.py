import re
import sys
import csv
import json
import os
import string
from datetime import datetime
from pathvalidate import sanitize_filename
from emoji import replace_emoji
import logging
from argparse import ArgumentParser

COLUMNS = [
    "msg_id",
    "date",
    "msg_type",
    "strain_name",
    "type",
    "genetics",
    "crosses",
    "flavor"
]

class TelegramChatParser:
    def __init__(self):
        self.photos_found = set(os.listdir("photos"))
        self.videos_found = set(os.listdir("video_files"))
        self.photos_renamed = set()
        self.videos_renamed = set()
        self.message_ids = set()

    def generate_filename(strain_name, type_info, quality, config):
      """Generates a filename based on user-defined configuration.

      Args:
        strain_name: The strain name.
        type_info: Information extracted from the "Type" field.
        quality: Quality information (e.g., "A", "B").
        config: A dictionary containing user-defined naming preferences.

      Returns:
        The generated filename.
      """

      # Implement custom naming logic based on config
    base_filename = f"{strain_name}-{type_info}"
        if quality:
            base_filename += f"-{quality}"
        return f"{base_filename}{config['file_extension']}"

def process_message(self, message):
        if message["type"] != "message":
            return None

        msg_id = message["id"]

        # Check if the message has already been processed
        if msg_id in self.message_ids:
            logging.warning(f"Message already processed - {msg_id}")
            return None

        sender = message["from"]
        sender_id = message["from_id"]
        date = message["date"].replace("T", " ")
        dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

        msg_content = ""
        msg_type = "text"
        file_name = ""

        if "text_entities" in message:
            for entity in message["text_entities"]:
                if entity["type"] == "plain":
                    msg_content += entity["text"]
        elif "text" in message:
            msg_content = "".join(message["text"])

        msg_content = replace_emoji(msg_content, replace="")
        msg_content = msg_content.replace("\n", " ")
        msg_content = msg_content.replace("#", "no_")

        has_strain = re.search(r"•\s*\S+\s*Strain:\s*(.*?)(?:\s*\n|</span>)", msg_content, re.IGNORECASE)
        has_type = re.search(r"•\s*\S+\s*Type:\s*(.*?)(?:\s*\n|</span>)", msg_content, re.IGNORECASE)
        has_genetics = re.search(r"Genetics:\s*(.*)", msg_content)
        has_crosses = re.search(r"•\s*\S+\s*Crosses:\s*(.*?)(?:\s*\n|</span>)", msg_content, re.IGNORECASE)
        has_flavor = re.search(r"•\s*\S+\s*Flavor:\s*(.*?)(?:\s*\n|</span>)", msg_content, re.IGNORECASE)
        has_video_coming_soon = re.search(r"VIDEO Coming Soon", msg_content, re.IGNORECASE)

        if has_strain and has_type and has_genetics:
            strain_name = has_strain.group(1).strip().lower()
            strain_name = re.sub(r"_\d+", "", strain_name)
            strain_name = sanitize_filename(strain_name)

            if has_video_coming_soon:
                strain_name += "-video_coming_soon"

            file_name = f"{strain_name}-(gg)"

            if has_type:
                quality = has_type.group(1).strip().lower()
                quality_letters_match = re.search(r"\b(A+)\b", quality)
                if quality_letters_match:
                    file_name += f"-{quality_letters_match.group(1).lower()}"

            msg_content = has_genetics.group(1)
            msg_type = "genetics"
            crosses_info = ""
            flavor_info = ""
            strain_type = has_type.group(1).strip() if has_type else ""

        elif has_type and has_crosses and has_flavor:
            strain_name_match = re.search(r"(.*?)\s*•\s*\S+\s*Type:", msg_content, re.IGNORECASE)
            if strain_name_match:
                strain_name = strain_name_match.group(1).strip().lower()
                strain_name = re.sub(r"_\d+", "", strain_name)
                strain_name = sanitize_filename(strain_name)
                file_name = f"{strain_name}-(gg)"

            msg_type = "strain_info"
            crosses_info = has_crosses.group(1).strip() if has_crosses else ""
            flavor_info = has_flavor.group(1).strip() if has_flavor else ""
            strain_type = has_type.group(1).strip() if has_type else ""
            genetics_info = ""

        else:
            return None

        if "photo" in message:
            original_file_path = message["photo"]
            original_file_name = os.path.basename(original_file_path)
            new_path = os.path.join("photos", file_name + os.path.splitext(original_file_name)[1])
            media_type = "photo"
            self.photos_found.add(original_file_name)

        elif "file" in message and "file_name" in message:
            original_file_path = message["file"]
            original_file_name = message["file_name"]
            new_path = os.path.join("video_files", file_name + ".mp4")
            media_type = "video"
            self.videos_found.add(original_file_name)

        if not ("photo" in message or "file" in message and "file_name" in message):
            pass
        else:
            if (media_type == "photo" and original_file_name in self.photos_renamed) or \
               (media_type == "video" and original_file_name in self.videos_renamed):
                logging.warning(f"File already renamed - {original_file_name}")
            else:
                if os.path.exists(original_file_path):
                    try:
                        os.rename(original_file_path, new_path)
                        if media_type == "photo":
                            self.photos_renamed.add(original_file_name)
                        else:
                            self.videos_renamed.add(original_file_name)
                        logging.info(f"Renamed {media_type}: {original_file_path} -> {new_path}")
                        self.message_ids.remove(msg_id)
                    except FileExistsError:
                        logging.warning(f"File already exists - {new_path}")

        return {
            "msg_id": msg_id,
            "date": date,
            "msg_type": msg_type,
            "strain_name": strain_name if strain_name else "",
            "type": strain_type if strain_type else "",
            "genetics": genetics_info if genetics_info else "",
            "crosses": crosses_info if crosses_info else "",
            "flavor": flavor_info if flavor_info else "",
        }

    def parse_telegram_to_csv(self, jdata, output_folder):
        os.makedirs(output_folder, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
        output_filepath = os.path.join(output_folder, base_name + ".csv")

        with open(output_filepath, "w", encoding="utf-8-sig", newline="") as output_file:
            writer = csv.DictWriter(output_file, COLUMNS, dialect="unix", quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()

            for message in jdata["messages"]:
                self.message_ids.add(message['id'])
                row = self.process_message(message)
                if row is not None:
                    writer.writerow(row)

        logging.info(f"CSV file created: {output_filepath}")
        self.export_files(output_folder)

    def export_files(self, output_folder):
        with open(os.path.join(output_folder, "photos_found.txt"), "w") as f:
            for filename in self.photos_found:
                f.write(f"{filename}\n")

        with open(os.path.join(output_folder, "photos_renamed.txt"), "w") as f:
            for filename in self.photos_renamed:
                f.write(f"{filename}\n")

        with open(os.path.join(output_folder, "videos_found.txt"), "w") as f:
            for filename in self.videos_found:
                f.write(f"{filename}\n")

        with open(os.path.join(output_folder, "videos_renamed.txt"), "w") as f:
            for filename in self.videos_renamed:
                f.write(f"{filename}\n")

        with open(os.path.join(output_folder, "message_ids.txt"), "w") as f:
            for msg_id in self.message_ids:
                f.write(f"{msg_id}\n")

if __name__ == "__main__":
    parser = ArgumentParser(description="Parse a Telegram chat history JSON file into a CSV format.")
    parser.add_argument("input_file", help="Path to the input chat history JSON file")
    args = parser.parse_args()

    backup_filepath = args.input_file

    parser_instance = TelegramChatParser()

    with open(backup_filepath, "r", encoding="utf-8-sig") as input_file:
        contents = input_file.read()
        jdata = json.loads(contents)

        if "chats" not in jdata:
            parser_instance.parse_telegram_to_csv(jdata, "parsed")
        else:
            for chat in jdata["chats"]["list"]:
                parser_instance.parse_telegram_to_csv(chat, "parsed")
