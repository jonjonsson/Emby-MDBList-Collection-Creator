import requests


class Mdblist:

    def __init__(self, api_key):
        self.api_key = api_key
        self.user_info_url = "https://mdblist.com/api/user/?apikey=" + api_key
        self.my_lists_url = "https://mdblist.com/api/lists/user/?apikey=" + api_key
        self.search_lists_url = (
            "https://mdblist.com/api/lists/search?s={list_name}&apikey=" + api_key
        )
        self.get_lists_of_user_url = (
            "https://mdblist.com/api/lists/user/{id}/?apikey=" + api_key
        )
        self.items_url = (
            "https://mdblist.com/api/lists/{list_id}/items/?apikey=" + api_key
        )

    def get_user_info(self):
        response = requests.get(self.user_info_url)
        user_info = response.json()
        return user_info

    def get_list(self, list_id):
        url = self.items_url.format(list_id=list_id)
        response = requests.get(url)
        if response.text:
            list = response.json()
            imdb_ids = [item["imdb_id"] for item in list]
            if len(imdb_ids) == 0:
                print(
                    f"ERROR! Cannot find any items in list id {list_id} with api url {url} and public url https://mdblist.com/?list={list_id}."
                )
            return imdb_ids
        else:
            print(f"No response received from {url}")
            return None

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
        list_name = list_name.replace(" ", "%20")
        url = self.search_lists_url.format(list_name=list_name)
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

    def find_list_id_by_url(self, url):
        # Find list by url, example: https://mdblist.com/lists/betdonkey/best-rottentomatoes-documentaries
        # where betdonkey is the user_name and best-rottentomatoes-documentaries is the list_name
        # This is problematic because url is the slug, not the list name and fails often
        url_parts = url.split("/")
        user_name = url_parts[-2]
        list_name = url_parts[-1]
        list_name = list_name.replace("-", " ")
        lists = self.find_list_id_by_name_and_user(list_name, user_name)
        return lists

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
