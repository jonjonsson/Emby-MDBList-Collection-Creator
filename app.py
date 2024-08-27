import random
import time
import configparser
from emby import Emby
from item_sorting import ItemSorting
from refresher import Refresher
from mdblist import Mdblist
from datetime import datetime

## Helpful URLS for dev:
# https://swagger.emby.media/?staticview=true#/
# https://github.com/MediaBrowser/Emby/wiki
# https://dev.emby.media/doc/restapi/Browsing-the-Library.html
# https://docs.mdblist.com/docs/api

config_parser = configparser.ConfigParser()

# Check if config_hidden.cfg exists, if so, use that, otherwise use config.cfg
if config_parser.read("config_hidden.cfg") == []:
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

hours_between_refresh = config_parser.getint("admin", "hours_between_refresh")

newly_added = 0
newly_removed = 0
collection_ids_with_custom_sorting = []
all_collections_ids = []

emby = Emby(emby_server_url, emby_user_id, emby_api_key)
mdblist = Mdblist(mdblist_api_key)
item_sorting = ItemSorting(emby)
refresher = Refresher(emby)


def find_missing_entries_in_list(list_to_check, list_to_find):
    """
    Finds the missing entries in a list.

    Args:
        list_to_check (list): The list to check against.
        list_to_find (list): The list to find missing entries in.

    Returns:
        list: A list of missing entries found in list_to_find.
    """
    return [item for item in list_to_find if item not in list_to_check]


def minutes_until_2100():
    """
    Used for sorting collection so that the newest show up first in Emby.
    Returns:
        int: The number of minutes remaining until the year 2100.
    """
    today = datetime.now()
    year_2100 = datetime(2100, 1, 1)
    delta = year_2100 - today
    minutes = delta.days * 24 * 60 + delta.seconds // 60
    return minutes


def process_list(mdblist_list: dict):
    global newly_added
    global newly_removed
    collection_name = mdblist_list["name"]
    frequency = int(mdblist_list.get("frequency", 100))
    list_id = mdblist_list.get("id", None)
    source = mdblist_list.get("source", None)
    mdblist_name = mdblist_list.get("mdblist_name", None)
    user_name = mdblist_list.get("user_name", None)
    update_collection_items_sort_names = mdblist_list.get(
        "update_items_sort_names", update_items_sort_names_default_value
    )

    collection_id = emby.get_collection_id(collection_name)
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
            print(
                f"ERROR! Could not find list {mdblist_name} by user {user_name}. Will not process this list."
            )
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
        print(
            f"ERROR! Must provide either list_id or both list_name and user_name for mdblist {collection_name}. Will not process this list."
        )
        print("=========================================")
        return

    if mdblist_imdb_ids is None:
        print(
            f"ERROR! No items in mdblist {collection_name}. Will not process this list."
        )
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
    print(
        f"Added {len(add_emby_ids)} new items to Collection and removed {len(remove_emby_ids)}"
    )

    if collection_id is None:
        if len(add_emby_ids) == 0:
            print(
                f"ERROR! No items to put in mdblist {collection_name}. Will not process."
            )
            print("=========================================")
            return
        collection_id = emby.create_collection(
            collection_name, [add_emby_ids[0]]
        )  # Create the collection with the first item since you have to create with an item
        add_emby_ids.pop(0)

    if collection_id not in all_collections_ids:
        all_collections_ids.append(collection_id)

    if update_collection_items_sort_names is True:
        collection_ids_with_custom_sorting.append(collection_id)

    items_added = emby.add_to_collection(collection_name, add_emby_ids)
    newly_added += items_added
    newly_removed += emby.delete_from_collection(collection_name, remove_emby_ids)

    # Change sort name so that it shows up first.
    if update_collection_sort_name is True and items_added > 0:
        collection_sort_name = f"!{minutes_until_2100()} {collection_name}"
        emby.set_item_property(collection_id, "ForcedSortName", collection_sort_name)
        print(f"Updated sort name for {collection_name} to {collection_sort_name}")

    print("=========================================")


def process_my_lists_on_mdblist():
    my_lists = mdblist.get_my_lists()
    if len(my_lists) == 0:
        print("ERROR! No lists returned from MDBList API. Will not process any lists.")
        return

    for mdblist_list in my_lists:
        process_list(mdblist_list)


def process_hardcoded_lists():
    # Get all section from config file that are not "admin" and add to mdblist_lists
    collections = []
    for section in config_parser.sections():
        if section == "admin":
            continue
        try:
            collections.append(
                {
                    "name": section,
                    "id": config_parser.get(section, "Id", fallback=None),
                    "source": config_parser.get(section, "Source", fallback=""),
                    "frequency": config_parser.get(section, "Frequency", fallback=100),
                    "mdblist_name": config_parser.get(
                        section, "List_Name", fallback=None
                    ),
                    "user_name": config_parser.get(section, "User_Name", fallback=None),
                    "update_items_sort_names": config_parser.getboolean(
                        section, "update_items_sort_names", fallback=False
                    ),
                }
            )
        except configparser.NoOptionError as e:
            print(f"Error in config file, section: {section}: {e}")

    for mdblist_list in collections:
        process_list(mdblist_list)


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
    #    "https://mdblist.com/lists/amything/external/26503/"
    # )
    # print(mdblist_list)
    # return

    while True:
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
