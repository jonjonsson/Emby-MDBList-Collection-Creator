import random
import time
import configparser
import requests
from src.emby import Emby
from src.item_sorting import ItemSorting
from src.refresher import Refresher
from src.mdblist import Mdblist
from src.date_parser import inside_period
from src.db import Db
from src.utils import find_missing_entries_in_list
from src.utils import minutes_until_2100

config_parser = configparser.ConfigParser()
config_parser.optionxform = str.lower

# Check if config_hidden.cfg exists, if so, use that, otherwise use config.cfg
if config_parser.read("config_hidden.cfg", encoding="utf-8") == []:
    config_parser.read("config.cfg")

emby_server_url = config_parser.get("admin", "emby_server_url")
emby_user_id = config_parser.get("admin", "emby_user_id")
emby_api_key = config_parser.get("admin", "emby_api_key")
mdblist_api_key = config_parser.get("admin", "mdblist_api_key")
download_manually_added_lists = config_parser.getboolean(
    "admin", "download_manually_added_lists", fallback=True
)
download_my_mdblist_lists_automatically = config_parser.getboolean(
    "admin", "download_my_mdblist_lists_automatically", fallback=True
)
update_collection_sort_name = config_parser.getboolean(
    "admin", "update_collection_sort_name", fallback=True
)
update_items_sort_names_default_value = config_parser.getboolean(
    "admin", "update_items_sort_names_default_value", fallback=False
)
refresh_items = config_parser.getboolean(
    "admin", "refresh_items_in_collections", fallback=False
)
refresh_items_max_days_since_added = config_parser.getint(
    "admin", "refresh_items_in_collections_max_days_since_added", fallback=10
)
refresh_items_max_days_since_premiered = config_parser.getint(
    "admin", "refresh_items_in_collections_max_days_since_premiered", fallback=30
)
use_mdblist_collection_description = config_parser.getboolean(
    "admin", "use_mdblist_collection_description", fallback=False
)

hours_between_refresh = config_parser.getint("admin", "hours_between_refresh")

newly_added = 0
newly_removed = 0
collection_ids_with_custom_sorting = []
all_collections_ids = []

emby = Emby(emby_server_url, emby_user_id, emby_api_key)
mdblist = Mdblist(mdblist_api_key)
item_sorting = ItemSorting(emby)
refresher = Refresher(emby)
db_manager = Db()


def process_list(mdblist_list: dict):
    global newly_added
    global newly_removed
    collection_name = mdblist_list["name"]
    frequency = int(mdblist_list.get("frequency", 100))
    list_id = mdblist_list.get("id", None)
    source = mdblist_list.get("source", None)
    poster = mdblist_list.get("poster", None)
    mdblist_name = mdblist_list.get("mdblist_name", None)
    user_name = mdblist_list.get("user_name", None)
    update_collection_items_sort_names = mdblist_list.get(
        "update_items_sort_names", update_items_sort_names_default_value
    )
    collection_sort_name = mdblist_list.get("collection_sort_name", None)
    description = mdblist_list.get("description", None)  # Description from mdblist
    overwrite_description = mdblist_list.get("overwrite_description", None)  # From cfg

    collection_id = emby.get_collection_id(collection_name)
    active_period_str = config_parser.get(
        collection_name, "active_between", fallback=None
    )

    if active_period_str:
        if not inside_period(active_period_str):
            all_items_in_collection = emby.get_items_in_collection(
                collection_id, ["Id"]
            )
            item_ids = (
                [item["Id"] for item in all_items_in_collection]
                if all_items_in_collection is not None
                else []
            )
            newly_removed += emby.delete_from_collection(collection_name, item_ids)
            if newly_removed > 0:
                print(f"Collection {collection_name} is not active. Removed all items.")
                print("=========================================")
            return

    if collection_id is None:
        print(f"Collection {collection_name} does not exist. Will create it.")
        frequency = 100  # If collection doesn't exist, download every time

    print()
    print("=========================================")

    if random.randint(0, 100) > frequency:
        print(f"Skipping mdblist {collection_name} since frequency is {frequency}")
        print("=========================================")
        return

    mdblist_imdb_ids = []
    mdblist_mediatypes = []
    if list_id is not None:
        mdblist_imdb_ids, mdblist_mediatypes = mdblist.get_list(list_id)
    elif mdblist_name is not None and user_name is not None:
        found_list_id = mdblist.find_list_id_by_name_and_user(mdblist_name, user_name)
        if found_list_id is None:
            print(f"ERROR! List {mdblist_name} by {user_name} not found. Skipping.")
            print("=========================================")
            return
        mdblist_imdb_ids, mdblist_mediatypes = mdblist.get_list(found_list_id)
    elif source is not None:
        source = source.replace(" ", "")
        sources = source.split(",http")
        # Add http back to all but the first source
        sources = [sources[0]] + [f"http{url}" for url in sources[1:]]
        for url in sources:
            imdb_ids, mediatypes = mdblist.get_list_using_url(url.strip())
            mdblist_imdb_ids.extend(imdb_ids)
            mdblist_mediatypes.extend(mediatypes)
    else:
        print(f"ERROR! Must provide either id or source for {collection_name}.")
        print("=========================================")
        return

    if mdblist_imdb_ids is None:
        print(f"ERROR! No items in {collection_name}. Will not process this list.")
        print("=========================================")
        return

    remove_emby_ids = []
    missing_imdb_ids = []

    if len(mdblist_imdb_ids) == 0:
        print(
            f"ERROR! No items in mdblist {collection_name}. Will not process this list. Perhaps you need to wait for it to populate?"
        )
        print("=========================================")
        return

    mdblist_imdb_ids = list(set(mdblist_imdb_ids))  # Remove duplicates
    print(f"Processing {collection_name}. List has {len(mdblist_imdb_ids)} IMDB IDs")
    collection_id = emby.get_collection_id(collection_name)

    if collection_id is None:
        missing_imdb_ids = mdblist_imdb_ids
    else:
        try:
            collection_items = emby.get_items_in_collection(
                collection_id, ["ProviderIds"]
            )
        except Exception as e:
            print(f"Error getting items in collection: {e}")
            print("=========================================")
            return

        collection_imdb_ids = [item["Imdb"] for item in collection_items]
        missing_imdb_ids = find_missing_entries_in_list(
            collection_imdb_ids, mdblist_imdb_ids
        )

        for item in collection_items:
            if item["Imdb"] not in mdblist_imdb_ids:
                remove_emby_ids.append(item["Id"])

    # Need Emby Item Ids instead of IMDB IDs to add to collection
    add_emby_ids = emby.get_items_with_imdb_id(missing_imdb_ids, mdblist_mediatypes)

    print()
    print(f"Added {len(add_emby_ids)} new items and removed {len(remove_emby_ids)}")

    if collection_id is None:
        if len(add_emby_ids) == 0:
            print(f"ERROR! No items to put in mdblist {collection_name}.")
            print("=========================================")
            return
        # Create the collection with the first item since you have to create with an item
        collection_id = emby.create_collection(collection_name, [add_emby_ids[0]])
        add_emby_ids.pop(0)

    if collection_id not in all_collections_ids:
        all_collections_ids.append(collection_id)

    if update_collection_items_sort_names is True:
        collection_ids_with_custom_sorting.append(collection_id)

    items_added = emby.add_to_collection(collection_name, add_emby_ids)
    newly_added += items_added
    newly_removed += emby.delete_from_collection(collection_name, remove_emby_ids)

    set_poster(collection_id, collection_name, poster)

    if collection_sort_name is not None:
        emby.set_item_property(collection_id, "ForcedSortName", collection_sort_name)

    # Change sort name so that it shows up first.
    # TODO If True previously and now False, it will not reset the sort name
    elif (
        update_collection_sort_name is True
        and collection_sort_name is None
        and items_added > 0
    ):
        collection_sort_name = f"!{minutes_until_2100()} {collection_name}"
        emby.set_item_property(collection_id, "ForcedSortName", collection_sort_name)
        print(f"Updated sort name for {collection_name} to {collection_sort_name}")

    if (
        use_mdblist_collection_description is True
        and bool(description)
        and overwrite_description is None
    ):
        emby.set_item_property(collection_id, "Overview", description)
    elif overwrite_description is not None:
        emby.set_item_property(collection_id, "Overview", overwrite_description)

    print("=========================================")


def process_my_lists_on_mdblist():
    my_lists = mdblist.get_my_lists()
    if len(my_lists) == 0:
        print("ERROR! No lists returned from MDBList API. Will not process any lists.")
        return

    for mdblist_list in my_lists:
        process_list(mdblist_list)


def process_hardcoded_lists():
    collections = []
    for section in config_parser.sections():
        if section == "admin":
            continue
        try:
            collections.append(
                {
                    "name": section,
                    "id": config_parser.get(section, "id", fallback=None),
                    "source": config_parser.get(section, "source", fallback=""),
                    "poster": config_parser.get(section, "poster", fallback=None),
                    "frequency": config_parser.get(section, "frequency", fallback=100),
                    "mdblist_name": config_parser.get(
                        section, "list_name", fallback=None
                    ),
                    "user_name": config_parser.get(section, "user_name", fallback=None),
                    "update_items_sort_names": config_parser.getboolean(
                        section, "update_items_sort_names", fallback=False
                    ),
                    "collection_sort_name": config_parser.get(
                        section, "collection_sort_name", fallback=None
                    ),
                    "overwrite_description": config_parser.get(
                        section, "description", fallback=None
                    ),
                }
            )
        except configparser.NoOptionError as e:
            print(f"Error in config file, section: {section}: {e}")

    for mdblist_list in collections:
        process_list(mdblist_list)


def set_poster(collection_id, collection_name, poster_path=None):
    """
    Sets the poster for a collection. Will not upload if temp config file
    shows that it been uploaded before.

    Args:
        collection_id (str): The ID of the collection.
        collection_name (str): The name of the collection. Only used for logging.
        poster_path (str): The path or URL to the new poster image.

    Returns:
        None
    """

    if poster_path is None:
        return

    if poster_path == db_manager.get_config_for_section(collection_id, "poster_path"):
        print(f"Poster for {collection_name} is already set to the specified path.")
        return

    if emby.set_image(collection_id, poster_path):
        db_manager.set_config_for_section(collection_id, "poster_path", poster_path)
        print(f"Poster for {collection_name} has been set successfully.")
    else:
        print(f"Failed to set poster for {collection_name}.")


def main():
    global newly_added
    global newly_removed
    iterations = 0

    # print(f"Emby System Info: {emby.get_system_info()}")
    # print()
    # print(f"Emby Users: {emby.get_users()}")
    # print()
    # print(f"MDBList User Info: {mdblist.get_mdblist_user_info()}")
    # print()

    # Test getting a list via url
    # mdblist_list = mdblist.get_list_using_url(
    #    "https://mdblist.com/lists/amything/best-documentaries"
    # )
    # print(mdblist_list)
    # return

    # Test getting all Emby collections
    # print(emby.get_all_collections(False))
    # return

    while True:

        try:
            response = requests.get("http://www.google.com/", timeout=5)
        except requests.RequestException:
            print("No internet connection. Check your connection. Retrying in 5 min...")
            time.sleep(300)
            continue

        emby_info = emby.get_system_info()
        if emby_info is False:
            print("Error connecting to Emby. Retrying in 5 min...")
            time.sleep(300)
            continue

        mdblist_user_info = mdblist.get_user_info()
        if mdblist_user_info is False:
            print("Error connecting to MDBList. Retrying in 5 min...")
            time.sleep(300)
            continue

        if download_manually_added_lists:
            process_hardcoded_lists()

        if download_my_mdblist_lists_automatically:
            process_my_lists_on_mdblist()

        print(
            f"\nSUMMARY: Added {newly_added} to collections and removed {newly_removed}\n"
        )
        newly_added = 0
        newly_removed = 0

        if len(collection_ids_with_custom_sorting) > 0:
            print("Setting sort names for new items in collections")
            for collection_id in collection_ids_with_custom_sorting:
                item_sorting.process_collection(collection_id)

            print(
                "\n\nReverting sort names that are no longer in collections, fetching items:"
            )

        item_sorting.reset_items_not_in_custom_sort_categories()

        if refresh_items is True:
            print(
                f"\nRefreshing metadata for items that were added within {refresh_items_max_days_since_added} days AND premiered within {refresh_items_max_days_since_premiered} days."
            )

        for collection_id in all_collections_ids:
            if refresh_items is True:
                refresher.process_collection(
                    collection_id,
                    refresh_items_max_days_since_added,
                    refresh_items_max_days_since_premiered,
                )

        if hours_between_refresh == 0:
            break

        print(f"\n\nWaiting {hours_between_refresh} hours for next refresh.\n\n")
        time.sleep(hours_between_refresh * 3600)
        iterations += 1


if __name__ == "__main__":
    main()
