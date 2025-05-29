from urllib.parse import quote
import requests


class Mdblist:

    def __init__(self, api_key):
        self.api_key = api_key
        self.user_info_url = "https://api.mdblist.com/user/?apikey=" + api_key
        self.my_lists_url = "https://api.mdblist.com/lists/user/?apikey=" + api_key
        self.search_lists_url = (
            "https://api.mdblist.com/lists/search?query={query}&apikey=" + api_key
        )
        self.get_lists_of_user_url = (
            "https://api.mdblist.com/lists/user/{id}/?apikey=" + api_key
        )
        self.items_url = (
            "https://api.mdblist.com/lists/{list_id}/items/?apikey=" + api_key
        )
        self.top_lists_url = "https://api.mdblist.com/lists/top?apikey=" + api_key
        self.get_list_by_name_url = (
            "https://api.mdblist.com/lists/{username}/{listname}?apikey=" + api_key
        )
        self.get_list_by_id_url = (
            "https://api.mdblist.com/lists/{list_id}?apikey=" + api_key
        )

    def get_user_info(self):
        try:
            response = requests.get(self.user_info_url)
            user_info = response.json()
            return user_info
        except Exception as e:
            print(f"Error getting MDBList user info: {e}")
            return False

    # Take the json encoded list and return the mediatypes as a list
    def check_list_mediatype(self, list) -> list:
        mediatypes = []
        for item in list:
            if "mediatype" in item and item["mediatype"] not in mediatypes:
                mediatypes.append(item["mediatype"])
        return mediatypes

    def get_list(
        self,
        list_id,
        filter_imdb_ids=True,
        append_to_response=[],
        limit=None,
        offset=None,
        max_items=None,  # <-- Added max_items parameter
    ):
        """
        Retrieves a list of items from a specified list ID and optionally filters by IMDb IDs.
        Supports pagination using limit and offset. By default, fetches all items.

        Args:
            list_id (str): The ID of the list to retrieve.
            filter_imdb_ids (bool, optional): If True, filters the list to only include IMDb IDs. Defaults to True.
            append_to_response (list, optional): Additional parameters to append to the response URL. Defaults to an empty list.
            limit (int, optional): Number of items per request. Defaults to None (fetch all).
            offset (int, optional): Offset for pagination. Defaults to None.
            max_items (int, optional): Maximum number of items to retrieve. Defaults to None (fetch all).

        Returns:
            tuple: (list of IMDb IDs or items, list of media types)
        """
        all_items = []
        current_offset = offset if offset is not None else 0
        page_limit = limit if limit is not None else 1000

        while True:
            url = self.items_url.format(list_id=list_id)
            params = []
            if append_to_response:
                params.append(f"append_to_response={'%2C'.join(append_to_response)}")
            params.append(f"limit={page_limit}")
            params.append(f"offset={current_offset}")
            if params:
                url = f"{url}&{'&'.join(params)}"

            response = requests.get(url)
            if not response.text:
                print(f"No response received from {url}")
                return None, None

            try:
                result = response.json()
                items = result.get("movies", []) + result.get("shows", [])
            except Exception:
                print(f"Error! Cannot decode json, make sure URL is valid: {url}")
                return None, None

            all_items.extend(items)

            # If max_items is set and we've reached/exceeded it, break
            if max_items is not None and len(all_items) >= max_items:
                all_items = all_items[:max_items]
                break

            # Check if more pages are available
            has_more = response.headers.get("X-Has-More", "false").lower() == "true"
            if not has_more:
                break
            current_offset += page_limit

        if filter_imdb_ids is False:
            return all_items, self.check_list_mediatype(all_items)

        imdb_ids = []
        for item in all_items:
            if "imdb_id" in item:
                imdb_ids.append(item["imdb_id"])
            else:
                print(f"Warning: Could not find imdb_id in item {item}.")

        if len(imdb_ids) == 0:
            print(f"ERROR! Cannot find any items in list id {list_id}.")
        return imdb_ids, self.check_list_mediatype(all_items)

    def get_list_using_url(self, url):
        # Just append /json to end of url to get the json version of the list
        # Check first if json is already in the url
        if url.endswith("/json"):
            url = url[:-5]

        # Make sure that url does not end with /
        if url.endswith("/"):
            url = url[:-1]

        url = url + "/json"

        response = requests.get(url)
        if response.text:
            lst = response.json()
            imdb_ids = []
            for item in lst:
                if "imdb_id" in item:
                    imdb_ids.append(item["imdb_id"])
                else:
                    print(f"Could not find imdb_id in item {item}.")
            if len(imdb_ids) == 0:
                print(
                    f"ERROR! Cannot find any items in list with api url {url} and public url {url.replace('/json','')}."
                )
            return imdb_ids, self.check_list_mediatype(lst)
        else:
            print(f"No response received from {url}")
            return None, None

    def get_list_items_using_url(self, url):
        # Just append /json to end of url to get the json version of the list
        # Check first if json is already in the url
        # Used for external lists.
        # TODO There is a better way since External lists support was added to api
        if url.endswith("/json"):
            url = url[:-5]

        # Make sure that url does not end with /
        if url.endswith("/"):
            url = url[:-1]
        url = url + "/json"
        response = requests.get(url)
        if response.text:
            list = response.json()
            """
            It returns like this if empty, we need to handle it
            0 = {'error': 'empty or private list'}
            len() = 1
            """
            if len(list) == 1 and "error" in list[0]:
                print(f"Error! {list[0]['error']}")
                return None, None

            return list, self.check_list_mediatype(list)
        else:
            print(f"No response received from {url}")
            return None, None

    def get_my_lists(self) -> list:
        # Example return
        # [{"id": 45811, "name": "Trending Movies", "slug": "trending-movies", "items": 20, "likes": null, "dynamic": true, "private": false, "mediatype": "movie", "description": ""}]
        response = requests.get(self.my_lists_url)
        lst = response.json()
        return lst

    def find_list_id_by_name(self, list_name):
        """
        Lists search
        Search public lists by title

        GET https://mdblist.com/api/lists/search?s={query}&apikey={api_key}
        query: List Title to search
        Response

        [
            {
                "id":14,
                "name":"Top Watched Movies of The Week / >60",
                "slug":"top-watched-movies-of-the-week",
                "items":72,
                "likes":244,
                "user_id":3,
                "mediatype":"movie",
                "user_name":"linaspurinis",
                "description":"",
            },
        ]
        """
        url = self.search_lists_url.format(list_name=quote(list_name))
        response = requests.get(url)
        lists = response.json()
        return lists

    def __filter_lists_by_user_name(lists, user_name):
        return [lst for lst in lists if lst["user_name"].lower() == user_name.lower()]

    def find_list_id_by_name_and_user(self, list_name, user_name):
        lists = self.find_list_id_by_name(list_name)
        filtered = Mdblist.__filter_lists_by_user_name(lists, user_name)
        if len(filtered) == 0:
            return None
        if len(filtered) > 1:
            print(
                f"Warning! Found {len(filtered)} lists with name {list_name} by user {user_name}. Will use the first one."
            )
        return filtered[0]["id"]

    def get_lists_of_user(self, user_id):
        """
        Get User lists
        Returns list of User Lists

        GET https://mdblist.com/api/lists/user/{id}/
        id: user id
        Response
        [
            {
                "id":13,
                "name":"Top Watched Movies of The Week for KiDS",
                "slug":"top-watched-movies-of-the-week-for-kids",
                "items":13,
                "likes":50,
                "mediatype":"movie",
                "description":"",
            },
        ]

        """
        url = self.get_lists_of_user_url.format(id=user_id)
        response = requests.get(url)
        lists = response.json()
        return lists

    def get_top_lists(self):
        """
        Get Top Lists
        Returns list of Top Lists

        GET https://api.mdblist.com/lists/top?apikey=abc123
        apikey: Your API key
        Response
        [
            {
                "id": 2194,
                "user_id": 1230,
                "user_name": "garycrawfordgc",
                "name": "Latest TV Shows",
                "slug": "latest-tv-shows",
                "description": "",
                "mediatype": "show",
                "items": 300,
                "likes": 477
            },
            ...
        ]
        """
        response = requests.get(self.top_lists_url)
        top_lists = response.json()
        return top_lists

    def search_list(self, query):
        """
        Search Lists
        Returns list of Lists matching the query

        GET https://api.mdblist.com/lists/search?query=Horror&apikey=abc123
        query: Search query
        apikey: Your API key
        Response
        [
            {
                "id": 2410,
                "user_id": 894,
                "user_name": "hdlists",
                "name": "Horror Movies (Top Rated From 1960 to Today)",
                "slug": "latest-hd-horror-movies-top-rated-from-1980-to-today",
                "description": "",
                "mediatype": "movie",
                "items": 920,
                "likes": 139
            },
            ...
        ]
        """
        url = self.search_lists_url.format(query=quote(query))
        response = requests.get(url)
        search_results = response.json()
        return search_results

    def get_list_by_name(self, username, listname):
        """
        Get List by Name
        Returns list details matching the username and listname

        GET https://api.mdblist.com/lists/{username}/{listname}?apikey=abc123
        username: The username associated with the list
        listname: The slug of the list
        apikey: Your API key
        Response
        [
            {
                "id": 1176,
                "user_id": 3,
                "user_name": "linaspurinis",
                "name": "Latest Certified Fresh Releases",
                "slug": "latest-certified-fresh-releases",
                "description": "Score >= 60\r\nLimit 30",
                "mediatype": "movie",
                "items": 30,
                "likes": 21,
                "dynamic": true,
                "private": false
            },
            ...
        ]
        """
        url = self.get_list_by_name_url.format(username=username, listname=listname)
        response = requests.get(url)
        list_details = response.json()
        return list_details

    def get_list_info_by_id(self, list_id):
        """
        Get List Info by ID
        Returns list details matching the list ID

        GET https://api.mdblist.com/lists/{listid}?apikey=abc123
        listid: The ID of the list
        apikey: Your API key
        Response
        [
            {
                "id": 1176,
                "user_id": 3,
                "user_name": "linaspurinis",
                "name": "Latest Certified Fresh Releases",
                "slug": "latest-certified-fresh-releases",
                "description": "Score >= 60\r\nLimit 30",
                "mediatype": "movie",
                "items": 30,
                "likes": 21,
                "dynamic": true,
                "private": false
            }
        ]
        """
        url = self.get_list_by_id_url.format(list_id=list_id)
        response = requests.get(url)
        list_info = response.json()

        if isinstance(list_info, dict):
            error = list_info.get("error")
            print(f"Error getting list {url} : {error}")
            return None

        if not isinstance(list_info, list):
            print(f"Error getting list, it should a list! {url} : {list_info}")
            return None

        if len(list_info) > 0:  # return first list info
            return list_info[0]

        print(f"Error getting list! {list_info}")
        return None

    def get_list_info_by_url(self, url):
        """
        Take an MDBList public URL and return list info.

        Example:
        URL: https://mdblist.com/lists/khoegh93/danish-spoken-2011-2020
        This function extracts the username and list name from the URL and uses them
        to retrieve the list info via the get_list_by_name method.

        Args:
        url (str): The MDBList public URL.

        Returns:
        dict: The list information retrieved by get_list_by_name.
        """
        url = url.replace("https://mdblist.com/lists/", "")
        parts = url.split("/")
        if len(parts) != 2:
            print(f"Error! URL {url} is not in the expected format.")
            return None
        username = parts[0]
        listname = parts[1]
        return self.get_list_by_name(username, listname)

    def get_my_limits(self):
        """
        Get My Limits
        Returns the API usage limits and current usage.

        GET https://api.mdblist.com/user?apikey=abc123
        apikey: Your API key
        Response
        {
            "api_requests": 100000,
            "api_requests_count": 276,
            "user_id": 3,
            "patron_status": "active_patron",
            "patreon_pledge": 300
        }
        """
        url = f"https://api.mdblist.com/user?apikey={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting limits: {response.status_code}")
            return None
