import random
import time
import requests  # pip install requests
import configparser

## Helpful URLS for dev:
# https://swagger.emby.media/?staticview=true#/
# https://github.com/MediaBrowser/Emby/wiki
# https://dev.emby.media/doc/restapi/Browsing-the-Library.html
# https://dev.emby.media/home/sdk/apiclients/Python/README.html

config_parser = configparser.ConfigParser()

# Check if config_hidden.cfg exists, if so, use that, otherwise use config.cfg
if config_parser.read("config_hidden.cfg") == []:
    config_parser.read("config.cfg")

emby_server_url = config_parser.get("admin", "emby_server_url")
emby_user_id = config_parser.get("admin", "emby_user_id")
emby_api_key = config_parser.get("admin", "emby_api_key")
mdblist_api_key = config_parser.get("admin", "mdblist_api_key")

download_manually_added_lists = config_parser.getboolean(
    "admin", "download_manually_added_lists"
)

download_my_mdblist_lists_automatically = config_parser.getboolean(
    "admin", "download_my_mdblist_lists_automatically"
)

seconds_between_emby_requests = 10
hours_between_refresh = config_parser.getint("admin", "hours_between_refresh")

# Get all section from config file that are not "admin" and add to mdblist_lists
mdblist_lists = []
for section in config_parser.sections():
    if section == "admin":
        continue
    try:
        mdblist_lists.append(
            {
                "Name": section,
                "Id": config_parser.get(section, "Id"),
                "Source": config_parser.get(section, "Source", fallback=""),
                "Frequency": config_parser.get(section, "Frequency"),
            }
        )
    except configparser.NoOptionError as e:
        print(f"Error in config file, section: {section}: {e}")

emby_api_batch_size = 50  # To prevent too long URLs, queries are done in batches of n

mbdList_my_lists_url = "https://mdblist.com/api/lists/user/?apikey=" + mdblist_api_key
mdbList_url = "https://mdblist.com/api/lists/{list_id}/items/?apikey=" + mdblist_api_key
headers = {"X-MediaBrowser-Token": emby_api_key}

newly_added = 0
newly_removed = 0


def get_system_info():
    endpoint = "/emby/System/Info"
    url = emby_server_url + endpoint
    response = requests.get(url, headers=headers)
    return response.json()


def get_users():
    user_list_endpoint = "/emby/Users"
    user_list_url = emby_server_url + user_list_endpoint
    user_list_response = requests.get(user_list_url, headers=headers)
    user_list = user_list_response.json()
    return user_list


def get_items_with_imdb_id(imdb_ids: list) -> list:
    """
    Accepts IMDB IDs as a list and returns a list of Emby Item IDs.
    Processed in batches of n to prevent too long URLs.
    """
    batch_size = emby_api_batch_size
    emby_items = []
    num_batches = len(imdb_ids) // batch_size + (len(imdb_ids) % batch_size > 0)
    gotten_item_names = []

    print(f"Retrieving IMDB IDs from Emby library in {num_batches} batches.")

    for i in range(num_batches):
        start_index = i * batch_size
        end_index = (i + 1) * batch_size
        batch_imdb_ids = imdb_ids[start_index:end_index]
        imdb_ids_str = ",".join(["imdb." + imdb_id for imdb_id in batch_imdb_ids])
        endpoint = f"/emby/users/{emby_user_id}/items?Fields=ChildCount,RecursiveItemCount&Recursive=true&IncludeItemTypes=Movie,Series&AnyProviderIdEquals={imdb_ids_str}"
        url = emby_server_url + endpoint
        response = requests.get(url, headers=headers)
        items = response.json()
        for item in items["Items"]:
            if item["Name"] in gotten_item_names:
                continue
            emby_items.append(item["Id"])
            gotten_item_names.append(item["Name"])
        print(
            f"Found {len(items['Items'])} items in batch {i+1} that need to be added Emby Collection. Waiting {seconds_between_emby_requests} seconds."
        )
        time.sleep(seconds_between_emby_requests)
    return emby_items


def get_all_collections(include_contents=True):
    """
    Retrieves all collections from the Emby server.

    Parameters:
    - include_contents (bool): Flag to indicate whether to include the items within each collection.

    Returns:
    - collections_list (list): List of dictionaries representing each collection, including its name, ID, and items (if include_contents is True).
    """
    endpoint = f"/emby/users/{emby_user_id}/items?Fields=ChildCount,RecursiveItemCount&Recursive=true&IncludeItemTypes=boxset"
    url = emby_server_url + endpoint
    response = requests.get(url, headers=headers)
    items = response.json()
    collections_list = []

    for item in items["Items"]:
        items_in_collection = None
        if include_contents:
            items_in_collection = get_items_in_collection(item["Id"])
        collections_list.append(
            {"Name": item["Name"], "Id": item["Id"], "items": items_in_collection}
        )

    return collections_list


def get_items_in_collection(collection_id):
    """
    Retrieves items in a collection based on the provided collection ID.

    Args:
        collection_id (str or int): The ID of the collection.

    Returns:
        list: A list of dictionaries containing the structured items in the collection.
              Each dictionary contains the item ID and the IMDb ID (if available).
    """
    endpoint = (
        f"/emby/users/{emby_user_id}/items?Parentid={collection_id}&Fields=ProviderIds"
    )
    url = emby_server_url + endpoint
    response = requests.get(url, headers=headers)
    items = response.json()
    structred_items = []
    for item in items["Items"]:
        imdb_id = item["ProviderIds"].get("Imdb") or item["ProviderIds"].get(
            "IMDB"
        )  # "Imdb" is sometimes all caps and sometimes not!
        structred_items.append({"Id": item["Id"], "Imdb": imdb_id})
    return structred_items


def create_collection(collection_name, item_ids) -> bool:
    """
    Check if collection exists, creates if not, then adds items to it.
    Must add at least one item when creating collection.

    Args:
        collection_name (str): The name of the collection to be created.
        item_ids (list): A list of item IDs to be added to the collection.

    Returns:
        bool: True if the collection is created successfully, False otherwise.
    """
    if item_ids is None or len(item_ids) == 0:
        print("Can't create collection, no items to add to it.")
        return False

    response = requests.post(
        f"{emby_server_url}/Collections?api_key={emby_api_key}&IsLocked=true&Name={collection_name}&Ids={ids_to_str(item_ids)}"
    )

    if response.status_code != 200:
        print(f"Error creating {collection_name}, response: {response}")
        return

    print(f"Successfully created collection {collection_name}")


def ids_to_str(ids: list) -> str:
    item_ids = [str(item_id) for item_id in ids]
    return ",".join(item_ids)


def get_collection_id(collection_name):
    all_collections = get_all_collections(False)
    collection_found = False

    for collection in all_collections:
        if collection_name == collection["Name"]:
            collection_found = True
            collection_id = collection["Id"]
            break

    if collection_found is False:
        print(f"Collection ID for {collection_name} not found")
        return None

    return collection_id


def add_remove_from_collection(collection_name, item_ids, operation):
    global newly_added
    global newly_removed

    if len(item_ids) == 0:
        return

    collection_id = get_collection_id(collection_name)

    if collection_id is None:
        return

    batch_size = emby_api_batch_size
    num_batches = (len(item_ids) + batch_size - 1) // batch_size

    for i in range(num_batches):
        start_index = i * batch_size
        end_index = min((i + 1) * batch_size, len(item_ids))
        batch_item_ids = item_ids[start_index:end_index]

        print(
            f"Processing Collection with operation {operation} batch {i+1} of {num_batches} with {len(batch_item_ids)} items"
        )

        if operation == "add":
            response = requests.post(
                f"{emby_server_url}/Collections/{collection_id}/Items/?api_key={emby_api_key}&Ids={ids_to_str(batch_item_ids)}"
            )
            newly_added += len(batch_item_ids)
        elif operation == "delete":
            response = requests.delete(
                f"{emby_server_url}/Collections/{collection_id}/Items/?api_key={emby_api_key}&Ids={ids_to_str(batch_item_ids)}"
            )
            newly_removed += len(batch_item_ids)

        if response.status_code != 204:
            print(
                f"Error processing collection with operation '{operation}', response: {response}"
            )
            return

        print(
            f"Successfully processed batch {i+1} of {num_batches} with {len(batch_item_ids)} items"
        )
        time.sleep(seconds_between_emby_requests)

    print(
        f"Completed Collection operation '{operation}' with {len(item_ids)} items in collection {collection_name}"
    )


def add_to_collection(collection_name, item_ids):
    add_remove_from_collection(collection_name, item_ids, "add")


def delete_from_collection(collection_name, item_ids):
    add_remove_from_collection(collection_name, item_ids, "delete")


def get_mdblist_user_info():
    url = "https://mdblist.com/api/user/?apikey=" + mdblist_api_key
    response = requests.get(url)
    mdblist_user_info = response.json()
    return mdblist_user_info


def get_mdblist_list(list_id):
    url = mdbList_url.format(list_id=list_id)
    response = requests.get(url)
    if response.text:
        mdblist_list = response.json()
        imdb_ids = [item["imdb_id"] for item in mdblist_list]
        if len(imdb_ids) == 0:
            print(
                f"ERROR! Cannot find any items in list id {list_id} with api url {url} and public url https://mdblist.com/?list={list_id}."
            )
        return imdb_ids
    else:
        print(f"No response received from {url}")
        return None


def get_my_mdblists_lists() -> list:
    # Example return
    # [{"id": 45811, "name": "Trending Movies", "slug": "trending-movies", "items": 20, "likes": null, "dynamic": true, "private": false, "mediatype": "movie", "description": ""}]
    response = requests.get(mbdList_my_lists_url)
    mdblist_list = response.json()
    return mdblist_list


def find_missing_entries_in_list(list_to_check, list_to_find):
    return [item for item in list_to_find if item not in list_to_check]


def process_list(mdblist_list: dict, frequency=100):
    # Example return
    # [{"id": 45811, "name": "Trending Movies", "slug": "trending-movies", "items": 20, "likes": null, "dynamic": true, "private": false, "mediatype": "movie", "description": ""}]
    list_name = mdblist_list["name"]
    list_id = mdblist_list["id"]
    collection_id = get_collection_id(list_name)

    if collection_id is None:
        frequency = 100  # If collection doesn't exist, download every time

    print()
    print("=========================================")

    if random.randint(0, 100) > frequency:
        print(f"Skipping mdblist {list_name} since frequency is {frequency}")
        print("=========================================")
        return

    mdblist_imdb_ids = get_mdblist_list(list_id)

    if mdblist_imdb_ids is None:
        print(f"ERROR! No items in mdblist {list_name}. Will not process this list.")
        print("=========================================")
        return

    remove_emby_ids = []
    missing_imdb_ids = []

    if len(mdblist_imdb_ids) == 0:
        print(f"ERROR! No items in mdblist {list_name}. Will not process this list.")
        print("=========================================")
        return

    print(f"Processing {list_name}. List has {len(mdblist_imdb_ids)} IMDB IDs.")
    collection_id = get_collection_id(list_name)

    if collection_id is None:
        missing_imdb_ids = mdblist_imdb_ids
    else:
        collection_items = get_items_in_collection(collection_id)
        collection_imdb_ids = [item["Imdb"] for item in collection_items]
        missing_imdb_ids = find_missing_entries_in_list(
            collection_imdb_ids, mdblist_imdb_ids
        )

        for item in collection_items:
            if item["Imdb"] not in mdblist_imdb_ids:
                remove_emby_ids.append(item["Id"])

    # Need Emby Item Ids instead of IMDB IDs to add to collection
    add_emby_ids = get_items_with_imdb_id(missing_imdb_ids)

    print(
        f"Added {len(add_emby_ids)} new items to Collection and removed {len(remove_emby_ids)}."
    )

    if collection_id is None:
        if len(add_emby_ids) == 0:
            print(f"ERROR! No items to put in mdblist {list_name}. Will not process.")
            print("=========================================")
            return
        create_collection(
            list_name, [add_emby_ids[0]]
        )  # Create the collection with the first item since you have to create with an item
        add_emby_ids.pop(0)

    add_to_collection(list_name, add_emby_ids)
    delete_from_collection(list_name, remove_emby_ids)
    print("=========================================")


def process_my_lists_on_mdblist():
    my_lists = get_my_mdblists_lists()
    if len(my_lists) == 0:
        print("ERROR! No lists returned from MDBList API. Will not process any lists.")
        return

    for mdblist_list in my_lists:
        process_list(mdblist_list)


def process_hardcoded_lists():
    for mdblist_list in mdblist_lists:
        frequency = 100
        if "Frequency" in mdblist_list:
            frequency = int(mdblist_list["Frequency"])
        process_list(
            {"name": mdblist_list["Name"], "id": mdblist_list["Id"]}, frequency
        )


def main():
    global newly_added
    global newly_removed
    iterations = 0

    # print(f"Emby System Info: {get_system_info()}")
    # print()
    # print(f"Emby Users: {get_users()}")
    # print()
    # print(f"MDBList User Info: {get_mdblist_user_info()}")
    # print()

    while True:
        if download_manually_added_lists:
            process_hardcoded_lists()

        if download_my_mdblist_lists_automatically:
            process_my_lists_on_mdblist()

        print()
        print(
            f"SUMMARY: Added {newly_added} items in total to collections and removed {newly_removed} items."
        )
        print(
            f"Waiting {hours_between_refresh} hours for next refresh. Iteration {iterations}"
        )
        newly_added = 0
        newly_removed = 0

        if hours_between_refresh == 0:
            break

        time.sleep(hours_between_refresh * 3600)
        iterations += 1


if __name__ == "__main__":
    main()
