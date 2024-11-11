from datetime import datetime
import re


class ItemSorting:
    """
    iterate over categories with sorting required and add sorting name if missing.
    Add all items to a list.

    Then get all items from emby that have a sorting name and check if they are in the above list.
    If not reset the sorting list.
    """

    def __init__(self, emby):
        self.emby = emby
        self.items_ids_with_new_sort_names = []
        self.seconds_between_requests = 1

        # Sort name example: "!!![{time_until_2100}]{previous_sort_name}"
        # Example: "!!![0000000000]The Matrix"
        self.sort_name_start = "!!!["
        self.sort_name_end = "]"
        self.sort_name_regex = r"!!!\[\d+\]"

    @staticmethod
    def minutes_until_2100(iso_date: str):
        """
        Returns:
            int: The number of minutes remaining until the year 2100.
        """
        date = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        # remove timezone from date
        date = date.replace(tzinfo=None)
        year_2100 = datetime(2100, 1, 1)
        delta = year_2100 - date
        minutes = delta.days * 24 * 60 + delta.seconds // 60
        return minutes

    def has_sorting_name(self, sort_name: str):
        return sort_name.startswith(self.sort_name_start)

    def process_collection(self, collection_id: int):
        """
        Iterate over collection with sorting required and add sorting name if missing.
        """

        if collection_id is None:
            print("Error: Category ID is None")
            return

        # Set DisplayOrder for collection
        # https://emby.media/community/index.php?/topic/124081-set-display-order-of-a-collection-with-api/
        self.emby.set_item_property(collection_id, "DisplayOrder", "SortName")

        items_in_collection = self.emby.get_items_in_collection(
            collection_id, ["SortName", "DateCreated"]
        )

        if items_in_collection is None:
            print(f"Error: Should not return None for collection {collection_id}")
            return

        for item in items_in_collection:
            # Example item: {'Id': '1541497', 'SortName': 'Elemental', 'DateCreated': '2023-12-08T09:27:58.0000000Z'}
            self.items_ids_with_new_sort_names.append(item["Id"])
            if self.has_sorting_name(item["SortName"]):
                continue
            new_sort_name = f"{self.sort_name_start}{self.minutes_until_2100(item['DateCreated'])}{self.sort_name_end}{item['SortName']}"
            self.emby.set_item_property(item["Id"], "ForcedSortName", new_sort_name)

    def __remove_sort_name(self, item: dict):
        new_sort_name = re.sub(self.sort_name_regex, "", item["SortName"])
        self.emby.set_item_property(item["Id"], "ForcedSortName", new_sort_name)

    def reset_items_not_in_custom_sort_categories(self):
        """
        Get all items from emby that have a sorting name and check if they are in the above list.
        If not reset the sorting list.
        """
        items_with_sort_name = self.emby.get_items_starting_with_sort_name(
            self.sort_name_start
        )
        print()
        for item in items_with_sort_name:
            if item["Id"] not in self.items_ids_with_new_sort_names:
                self.__remove_sort_name(item)

        self.items_ids_with_new_sort_names = []
