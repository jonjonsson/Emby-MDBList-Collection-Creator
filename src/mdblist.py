from urllib.parse import quote
import requests


class Mdblist:

    def __init__(self, api_key):
        self.api_key = api_key
        self.user_info_url = "https://mdblist.com/api/user/?apikey=" + api_key
        self.my_lists_url = "https://mdblist.com/api/lists/user/?apikey=" + api_key
        self.search_lists_url = (
            "https://api.mdblist.com/lists/search?query={query}&apikey=" + api_key
        )
        self.get_lists_of_user_url = (
            "https://mdblist.com/api/lists/user/{id}/?apikey=" + api_key
        )
        self.items_url = (
            "https://mdblist.com/api/lists/{list_id}/items/?apikey=" + api_key
        )
        self.top_lists_url = "https://api.mdblist.com/lists/top?apikey=" + api_key
        self.get_list_by_name_url = (
            "https://api.mdblist.com/lists/{username}/{listname}?apikey=" + api_key
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

    def get_list(self, list_id):
        url = self.items_url.format(list_id=list_id)
        response = requests.get(url)
        if response.text:
            list = None
            try:
                list = response.json()
            except Exception:
                print(f"Error! Cannot decode json, make sure URL is valid: {url}")
                return None, None
            imdb_ids = [item["imdb_id"] for item in list]
            if len(imdb_ids) == 0:
                print(
                    f"ERROR! Cannot find any items in list id {list_id} with api url {url} and public url https://mdblist.com/?list={list_id}."
                )
            return imdb_ids, self.check_list_mediatype(list)
        else:
            print(f"No response received from {url}")
            return None, None

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
            list = response.json()
            imdb_ids = []
            for item in list:
                if "imdb_id" in item:
                    imdb_ids.append(item["imdb_id"])
                else:
                    print(f"Could not find imdb_id in item {item}.")
            if len(imdb_ids) == 0:
                print(
                    f"ERROR! Cannot find any items in list with api url {url} and public url {url.replace('/json','')}."
                )
            return imdb_ids, self.check_list_mediatype(list)
        else:
            print(f"No response received from {url}")
            return None, None

    def get_my_lists(self) -> list:
        # Example return
        # [{"id": 45811, "name": "Trending Movies", "slug": "trending-movies", "items": 20, "likes": null, "dynamic": true, "private": false, "mediatype": "movie", "description": ""}]
        response = requests.get(self.my_lists_url)
        list = response.json()
        return list

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
        return [
            list for list in lists if list["user_name"].lower() == user_name.lower()
        ]

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
        username = parts[0]
        listname = parts[1]
        return self.get_list_by_name(username, listname)
