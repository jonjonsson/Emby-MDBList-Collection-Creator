"""
This script can restore a backup to another Emby server from previously using app_backup.py.

The script assumes that the new Emby server does not have the same item ID as the old Emby server and
will lookup all items by IMDB or TVDB ID.

Execute the script from the command line with the required arguments:

--host: The Emby server host.
--user_id: The user ID for the Emby server (ID string, not the user name).
--api_key: The API key for accessing the Emby server.
--source_file: The path to the backup file.
You can use this if you don't have access to the Emby database but you do have access to the API.
Example command: 
    
    python3 restore_backup.py -host http://xxx.xxx.xxx.xxx:xxxx -user_id abc123 -api_key abc123 -source_file "backup\IsPlayed_SomeUsername.json"

Json file exmple:
    {
    "user_name": "Jason",
    "user_id": "abc123",
    "filter": "IsPlayed", // or "IsFavorite"
    "Items": [
        {
            "Id": "15172942",
            "Name": "The Matrix",
            "ProviderIds": {
                "Imdb": "tt21215388",
                "Tmdb": "1090446",
                "Tvdb": "357485"
            },
            "Type": "Movie"
        },
    etc
"""

from src.emby import Emby
import ast
import sys
from argparse import ArgumentParser

backup_filters = ["IsPlayed", "IsFavorite"]


def get_provider_id(provider_ids, key):
    # Normalize keys to lowercase since some providers return keys in different cases
    normalized_dict = {k.lower(): v for k, v in provider_ids.items()}
    return normalized_dict.get(key.lower())


def add_error(error):
    print(f"\nERROR: {error}")


def main(args):
    emby = Emby(args.host, args.user_id, args.api_key)
    emby.seconds_between_requests = 0.1
    backup_file = args.source_file

    with open(backup_file, "r") as file:
        backup_data = file.read()

    filter = ast.literal_eval(backup_data)["filter"]
    items = ast.literal_eval(backup_data)["Items"]
    user_id = args.user_id

    for item in items:

        if "Id" not in item or "Name" not in item:
            add_error(f"{item} is missing Id or Name")
            continue

        item_id = int(item["Id"])
        new_item_ids = None
        item_name = item["Name"]
        item_type = item["Type"]

        imdb_id = None
        tvdb_id = None

        provider_ids = item.get("ProviderIds", None)

        if provider_ids is None:
            add_error(f"{item_id}:{item_name} is missing ProviderIds")
            continue

        imdb_id = get_provider_id(provider_ids, "imdb")
        tvdb_id = get_provider_id(provider_ids, "tvdb")

        if imdb_id is None and tvdb_id is None:
            add_error(f"Can not find IMDB or TVDB ID for: {item_id}: {item_name}")
            continue

        if item_type not in ["Series", "Episode", "Movie"]:
            add_error(f"{item_id}:{item_name} has invalid type {item_type}")
            continue

        if item_type == "Episode":

            if tvdb_id is None:
                add_error(f"Can not find TVDB ID for episode {item_id}: {item_name}")
                continue

            new_item_ids = emby.get_items_with_tvdb_id([tvdb_id], [item_type])

        elif item_type == "Series" or item_type == "Movie":

            if imdb_id is not None:  # Prefer IMDB first I guess
                new_item_ids = emby.get_items_with_imdb_id([imdb_id], [item_type])
            elif tvdb_id is not None:
                new_item_ids = emby.get_items_with_tvdb_id([tvdb_id], [item_type])

        if new_item_ids is None or new_item_ids == []:
            add_error(
                f"Can not find new Item for TVDB: {tvdb_id} IMDB: {imdb_id} Name: {item_name}. "
            )
            continue

        for new_item_id in new_item_ids:
            if filter == "IsPlayed":
                set_as_played = emby.set_item_as_played(user_id, new_item_id)
                if not set_as_played:
                    add_error(f"Cannot set to IsPlayed {new_item_id}: {item_name}")
            elif filter == "IsFavorite":
                set_as_favorite = emby.set_item_as_favorite(user_id, new_item_id)
                if not set_as_favorite:
                    add_error(f"Cannot set to IsFavorite {item_id}: {item_name}")


if __name__ == "__main__":

    parser = ArgumentParser()

    if len(sys.argv) == 1:
        parser.print_help()
        quit()

    parser.add_argument("-host", dest="host", help="Destination Emby host")
    parser.add_argument("-user_id", dest="user_id", help="Destination user ID")
    parser.add_argument(
        "-api_key",
        dest="api_key",
        help="Destination Emby API key",
    )
    parser.add_argument(
        "-source_file",
        dest="source_file",
        help="Source file to restore from",
    )
    args = parser.parse_args()
    main(args)
