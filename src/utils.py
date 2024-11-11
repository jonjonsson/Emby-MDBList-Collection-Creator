from datetime import datetime


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
