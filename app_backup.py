"""
Run this file to backup of Watch history and Favorites for all users to text files.
You can use this if you don't have access to the Emby database but you do have access to the API.
"""

import configparser
import json
from emby import Emby
import os

directory = "backup"
backup_filters = ["IsPlayed", "IsFavorite"]
seconds_between_requests = 10

config_parser = configparser.ConfigParser()
if config_parser.read("config_hidden.cfg") == []:
    config_parser.read("config.cfg")
emby_server_url = config_parser.get("admin", "emby_server_url")
emby_user_id = config_parser.get("admin", "emby_user_id")
emby_api_key = config_parser.get("admin", "emby_api_key")
emby = Emby(emby_server_url, emby_user_id, emby_api_key)
emby.seconds_between_requests = seconds_between_requests


def get_all_items(user_id, filter):

    items = emby.get_items(
        params={"userId": user_id},
        fields=["ProviderIds"],
        include_item_types=["Movie", "Series", "Episode"],
        filters=[filter],
    )

    returned_items = []
    for item in items:
        include_fields = [
            "Id",
            "Name",
            "ProviderIds",
            "Type",
        ]
        # remove any fields that are not in include_fields
        item = {key: item[key] for key in include_fields if key in item}
        # remove any item["ProviderIds"] that are not relevant
        include_provider_ids = ["imdb", "tmdb", "tvdb"]
        if "ProviderIds" in item:
            item["ProviderIds"] = {
                key: value
                for key, value in item["ProviderIds"].items()
                if key.lower() in include_provider_ids
            }
        returned_items.append(item)

    return returned_items


def main():
    all_users = emby.get_users()

    if not os.path.exists(directory):
        os.makedirs(directory)

    print(f"\nBacking up Watch history and Favorites for {len(all_users)} users\n")

    for filter in backup_filters:
        for user in all_users:
            user_id = user["Id"]
            user_name = user["Name"]
            data = {
                "user_name": user_name,
                "user_id": user_id,
                "filter": filter,
                "Items": [],
            }
            print(f"\nGetting {filter} items for {user_name}")
            data["Items"] = get_all_items(user_id, filter)
            file_name = f"{directory}/{filter}_{user_name}.json"
            print(f"\nWriting {len(data['Items'])} items to {file_name}")
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)


if __name__ == "__main__":
    main()
