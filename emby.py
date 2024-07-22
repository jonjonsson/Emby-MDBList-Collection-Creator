import time
import requests


class Emby:

    def __init__(self, server_url, user_id, api_key):
        self.server_url = server_url
        self.user_id = user_id
        self.api_key = api_key
        self.headers = {"X-MediaBrowser-Token": api_key}
        # To prevent too long URLs, queries are done in batches of n
        self.api_batch_size = 50
        self.seconds_between_requests = 1
        # get system info to see if it works
        self.system_info = self.get_system_info()

    def get_system_info(self):
        endpoint = "/emby/System/Info"
        url = self.server_url + endpoint
        response = requests.get(url, headers=self.headers)
        try:
            return response.json()
        except Exception as e:
            print(
                f"Error occurred while getting system info, check your configuration: {e}"
            )
            return None

    def get_users(self):
        user_list_endpoint = "/emby/Users"
        user_list_url = self.server_url + user_list_endpoint
        user_list_response = requests.get(user_list_url, headers=self.headers)
        user_list = user_list_response.json()
        return user_list

    def get_items_starting_with_sort_name(self, filter, limit=20):
        """
        Retrieves all movies and series whose SortName starts with the specified filter.
        Must be queried like this because it's not possible to search for SortName directly.

        Args:
            filter (str): The filter to match the SortName against.

        Returns:
            list: A list of items (movies and series) whose SortName starts with the filter.
        """
        limit = 50
        start_index = 0
        filtered_items = []
        found_sort_name = True

        while found_sort_name:

            items = self.get_items(
                fields=["SortName"],
                include_item_types=["Movie", "Series"],
                sort_by="SortName",
                limit=limit,
                start_index=start_index,
                getAll=False,
            )

            for item in items:
                if item["SortName"].startswith(filter):
                    filtered_items.append(item)
                else:
                    found_sort_name = False
                    break

            time.sleep(self.seconds_between_requests)
            start_index += limit

        return filtered_items

    def get_items_with_imdb_id(self, imdb_ids, item_types=None):
        batch_size = self.api_batch_size
        returned_items = []
        gotten_item_names = []

        if item_types is None:
            item_types = ["Movie", "Series"]
        else:
            item_types = [
                (
                    "Series"
                    if item_type.lower() in ["tv", "show"]
                    else "Movie" if item_type.lower() == "movie" else item_type
                )
                for item_type in item_types
            ]

        for i in range(0, len(imdb_ids), batch_size):
            batch_imdb_ids = imdb_ids[i : i + batch_size]
            imdb_ids_str = ",".join(["imdb." + imdb_id for imdb_id in batch_imdb_ids])

            items = self.get_items(
                params={"AnyProviderIdEquals": imdb_ids_str},
                fields=["ChildCount", "RecursiveItemCount"],
                include_item_types=item_types,
                limit=batch_size,
            )

            for item in items:
                if item["Name"] not in gotten_item_names:
                    returned_items.append(item["Id"])
                    gotten_item_names.append(item["Name"])

        return returned_items

    def get_all_collections(self, include_contents=True):
        """
        Retrieves all collections from the Emby server.

        Parameters:
        - include_contents (bool): Flag to indicate whether to include the items within each collection.

        Returns:
        - collections_list (list): List of dictionaries representing each collection, including its name, ID, and items (if include_contents is True).
        """
        endpoint = f"/emby/users/{self.user_id}/items?Fields=ChildCount,RecursiveItemCount&Recursive=true&IncludeItemTypes=boxset"
        url = self.server_url + endpoint
        response = requests.get(url, headers=self.headers)
        items = response.json()
        collections_list = []

        for item in items["Items"]:
            items_in_collection = None
            if include_contents:
                items_in_collection = self.get_items_in_collection(
                    item["Id"], ["ProviderIds"]
                )
            collections_list.append(
                {"Name": item["Name"], "Id": item["Id"], "items": items_in_collection}
            )

        return collections_list

    def get_items_in_collection(self, collection_id: int, fields: list = None):
        """
        Retrieves items in a collection based on the provided collection ID.

        Args:
            collection_id (str or int): The ID of the collection.
            fields (list): List of fields to include in the response. Defaults to None.

        Returns:
            list: A list of dictionaries containing the structured items in the collection.
                Each dictionary contains the specified fields for each item.
        """
        endpoint = f"/emby/users/{self.user_id}/items?Parentid={collection_id}"
        if fields:
            fields_str = ",".join(fields)
            endpoint += f"&Fields={fields_str}"
        url = self.server_url + endpoint
        response = requests.get(url, headers=self.headers)

        try:
            items = response.json()
        except Exception as e:
            print(
                f"Error occurred while getting items in collection id {collection_id} using url {url} response was {response}: {e}"
            )
            return None
        structured_items = []
        for item in items["Items"]:
            add_item = {
                "Id": item["Id"],
                "Name": item["Name"],
                "Type": item["Type"],
            }
            if "ProviderIds" in item:
                # Need special treatment because "Imdb" is sometimes all caps and sometimes not!
                imdb_id = item["ProviderIds"].get("Imdb") or item["ProviderIds"].get(
                    "IMDB"
                )
                add_item["Imdb"] = imdb_id

            for field in fields:
                add_item[field] = item.get(field)

            structured_items.append(add_item)
        return structured_items

    def create_collection(self, collection_name, item_ids) -> bool:
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
            return None

        response = requests.post(
            f"{self.server_url}/Collections?api_key={self.api_key}&IsLocked=true&Name={collection_name}&Ids={Emby.__ids_to_str(item_ids)}"
        )

        if response.status_code != 200:
            print(f"Error creating {collection_name}, response: {response}")
            return None

        print(f"Successfully created collection {collection_name}")
        return response.json()["Id"]

    def get_item(self, item_id) -> dict:
        endpoint = f"/emby/users/{self.user_id}/items/{item_id}"
        url = self.server_url + endpoint
        try:
            return requests.get(url, headers=self.headers).json()
        except Exception as e:
            print(f"Error occurred while getting item: {e}")
            return None

    def set_item_property(self, item_id, property_name, property_value):
        return self.__update_item(item_id, {property_name: property_value})

    def get_collection_id(self, collection_name):
        all_collections = self.get_all_collections(False)
        collection_found = False

        for collection in all_collections:
            if collection_name == collection["Name"]:
                collection_found = True
                collection_id = collection["Id"]
                break

        if collection_found is False:
            return None

        return collection_id

    def add_to_collection(self, collection_name, item_ids) -> int:
        # Returns the number of items added to the collection
        return self.__add_remove_from_collection(collection_name, item_ids, "add")

    def delete_from_collection(self, collection_name, item_ids) -> int:
        # Returns the number of items deleted from the collection
        return self.__add_remove_from_collection(collection_name, item_ids, "delete")

    def refresh_item(self, item_id):
        # Refreshes metadata for a specific item
        response = requests.post(
            f"{self.server_url}/Items/{item_id}/Refresh?api_key={self.api_key}&ReplaceAllMetadata=true"
        )
        time.sleep(self.seconds_between_requests)
        if response.status_code != 204:
            print(f"Error refreshing item {item_id}, response: {response}")
            return False
        return True

    def get_items(
        self,
        params=None,
        fields=None,
        include_item_types=None,
        filters=None,
        sort_by=None,
        limit=50,
        start_index=0,
        getAll=True,
    ):
        """
        Generic method to retrieve all items from Emby, querying in batches.

        Args:
            params (dict): Additional parameters to include in the query.
            fields (list): List of fields to include in the response.
            include_item_types (list): Types of items to include (e.g., ['Movie', 'Series']).
            filters (list): Filters to apply to the query.
            sort_by (str): Field to sort the results by.
            limit (int): Number of items to query in each batch.
            start_index (int): Index to start querying from.
            getAll (bool): Flag to indicate whether to retrieve all items or just the first batch.

        Returns:
            list: All items retrieved from the Emby API.
        """
        endpoint = f"/emby/users/{self.user_id}/items"
        query_params = {}

        if params:
            query_params.update(params)
        if fields:
            query_params["Fields"] = ",".join(fields)
        if include_item_types:
            query_params["IncludeItemTypes"] = ",".join(include_item_types)
        if filters:
            query_params["Filters"] = ",".join(filters)
        if sort_by:
            query_params["SortBy"] = sort_by

        query_params["Recursive"] = "true"
        query_params["Limit"] = limit

        url = self.server_url + endpoint
        all_items = []

        while True:
            print(".", end="", flush=True)
            time.sleep(self.seconds_between_requests)
            query_params["StartIndex"] = start_index
            response = requests.get(url, headers=self.headers, params=query_params)
            response_data = response.json()

            if "Items" in response_data:
                items = response_data["Items"]
                all_items.extend(items)
                if len(items) < limit:
                    break  # We've retrieved all items
                start_index += limit
            else:
                break  # No more items to retrieve

            if not getAll:
                break

        return all_items

    def set_item_as_played(self, user_id, item_id):
        """
        Set an item as played for a specific user.

        Args:
            user_id (str): The ID of the user.
            item_id (str): The ID of the item to mark as played.

        Returns:
            bool: True if the item was marked as played successfully, False otherwise.
        """
        endpoint = f"/emby/Users/{user_id}/PlayedItems/{item_id}"
        url = self.server_url + endpoint
        response = requests.post(url, headers=self.headers)
        if response.status_code == 200:
            return True
        else:
            print(
                f"Error marking item {item_id} as played for user {user_id}: {response.content}"
            )
            return False

    def set_item_as_favorite(self, user_id, item_id):
        """
        Set an item as a favorite for a specific user.

        Args:
            user_id (str): The ID of the user.
            item_id (str): The ID of the item to mark as a favorite.

        Returns:
            bool: True if the item was marked as a favorite successfully, False otherwise.
        """
        endpoint = f"/emby/Users/{user_id}/FavoriteItems/{item_id}"
        url = self.server_url + endpoint
        response = requests.post(url, headers=self.headers)
        if response.status_code == 200:
            return True
        else:
            print(
                f"Error marking item {item_id} as a favorite for user {user_id}: {response.content}"
            )
            return False

    def __update_item(self, item_id, data):
        item = self.get_item(item_id)
        if item is None:
            return None
        if "ForcedSortName" in data and "SortName" not in item["LockedFields"]:
            # If adding "ForcedSortName" to data, we must have "SortName" in LockedFields
            # see https://emby.media/community/index.php?/topic/108814-itemupdateservice-cannot-change-the-sortname-and-forcedsortname/
            item["LockedFields"].append("SortName")
        item.update(data)
        update_item_url = (
            f"{self.server_url}/emby/Items/{item_id}?api_key={self.api_key}"
        )
        try:
            response = requests.post(update_item_url, json=item, headers=self.headers)
            print(
                f"Updated item {item_id} with {data}. Waiting {self.seconds_between_requests} seconds."
            )
            time.sleep(self.seconds_between_requests)
            return response
        except Exception as e:
            print(f"Error occurred while updating item: {e}")
            return None

    def __add_remove_from_collection(
        self, collection_name: str, item_ids: list, operation: str
    ) -> int:

        affected_count = 0

        if len(item_ids) == 0:
            return affected_count

        collection_id = self.get_collection_id(collection_name)

        if collection_id is None:
            return affected_count

        batch_size = self.api_batch_size
        num_batches = (len(item_ids) + batch_size - 1) // batch_size

        print(
            f"Processing {collection_name} with '{operation}' in {num_batches} batches"
        )

        for i in range(num_batches):
            start_index = i * batch_size
            end_index = min((i + 1) * batch_size, len(item_ids))
            batch_item_ids = item_ids[start_index:end_index]
            print(".", end="", flush=True)

            if operation == "add":
                response = requests.post(
                    f"{self.server_url}/Collections/{collection_id}/Items/?api_key={self.api_key}&Ids={Emby.__ids_to_str(batch_item_ids)}"
                )
                affected_count += len(batch_item_ids)
            elif operation == "delete":
                response = requests.delete(
                    f"{self.server_url}/Collections/{collection_id}/Items/?api_key={self.api_key}&Ids={Emby.__ids_to_str(batch_item_ids)}"
                )
                affected_count += len(batch_item_ids)

            if response.status_code != 204:
                print(
                    f"Error processing collection with operation '{operation}', response: {response}"
                )
                return affected_count

            time.sleep(self.seconds_between_requests)

        print()
        print(f"Finished '{operation}' with {len(item_ids)} items in {collection_name}")

        return affected_count

    def __ids_to_str(ids: list) -> str:
        item_ids = [str(item_id) for item_id in ids]
        return ",".join(item_ids)
