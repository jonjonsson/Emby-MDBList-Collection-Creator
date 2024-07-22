"""
This script can restore a backup to another Emby server from previously using app_backup.py 
and saving Watched and Favorites to a json file.

Execute the script from the command line with the required arguments. The script requires the following arguments:

--host: The Emby server host.
--user_id: The user ID for the Emby server (ID not user name).
--api_key: The API key for accessing the Emby server.
--source_file: The path to the backup file.
You can use this if you don't have access to the Emby database but you do have access to the API.
Example command: 
    
    python3 restore_backup.py -host http://xxx.xxx.xxx.xxx:xxxx -user_id abc123 -api_key abc123 -source_file "backup\IsPlayed_SomeUsername.json"

"""

import time
from emby import Emby
import ast
import sys
from argparse import ArgumentParser

backup_filters = ["IsPlayed", "IsFavorite"]
seconds_between_requests = 1


def main(args):
    emby = Emby(args.host, args.user_id, args.api_key)
    backup_file = args.source_file

    with open(backup_file, "r") as file:
        backup_data = file.read()

    """
    Format of backup file is json:

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
    filter = ast.literal_eval(backup_data)["filter"]
    items = ast.literal_eval(backup_data)["Items"]

    for item in items:
        print(".", end="", flush=True)
        if filter == "IsPlayed":
            set_as_played = emby.set_item_as_played(args.user_id, item["Id"])
            if not set_as_played:
                print(f"    !!! ERROR: {item['Id']}:{item['Name']} !!!    ")
        elif filter == "IsFavorite":
            set_as_favorite = emby.set_item_as_favorite(args.user_id, item["Id"])
            if not set_as_favorite:
                print(f"    !!! ERROR: {item['Id']}:{item['Name']} !!!    ")

        time.sleep(seconds_between_requests)


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
