# Emby MDBList Collection Creator 1.61

This Python script allows you to take lists from MDBList.com and transform them into collections in Emby. MDBList is a platform that stores lists from Trakt, IMDB, and more, which can be accessed through an API. There is also a refresh metadata functionality that helps keep ratings up to date for newly released items.

## Prerequisites:

To use this script, you need:

* Python installed on your system
* "Requests" Python package (install with `pip install requests`)
* Admin privileges on Emby
* A user account on [MDBList](https://mdblist.com/)
* The script has been tested with Emby Version 4.8.8.0, but other recent versions should also be compatible

## Usage

### Configuring the Admin Section

In the `config.cfg` file, fill in the following details:

* Emby server URL
* Emby admin user ID
* Emby API key
* MDBList API key

Refer to the comments in `config.cfg` for additional information.

### Running the Script

Navigate to the project directory and execute the following commands:

```bash
pip install requests
python app.py
```

## Creating Emby Collections from MDBList Lists

There are two methods to create Emby collections from MDBList lists:

### 1. Add MDBList URLs or IDs to `config.cfg`

* Refer to `config.cfg` for examples.
* This method allows you to create collections from other users' lists, found at [MDBList Top Lists](https://mdblist.com/toplists/).
* The `config.cfg` file contains examples. Use these as a guide to add more lists. 

### 2. Automatically Download Your Lists from MDBList

By creating your own lists on MDBList (found at [My MDBList](https://mdblist.com/mylists/)), Emby collections will be automatically created from your saved lists. This feature can be turned off in `config.cfg`. Please ensure your newly created MDBLists populate items before running the script.

## Sorting Shows and Movies by time added

This feature that is off by default. Emby can not (yet) sort collections by time added to library. That means you can't sort collections to show what is newest first. This is kinda lame if you have a Trending Movies category and you can't see what's new at a glance. 

To address this you can have this script update the sort names of items that are in collections. It updates item sort name in the metadata so that the sort name is appended with "!!![number_of_minutes_until_year_2100_from_the_date_time_added_to_emby]". That way the newest items show first in the default alphabetical order. This will affect the sorting of these items elsewhere as well which you may or may not care about, you can always turn it off and the old sort name will be restored on the next run of the script.

You can set this on by default for all collection in the config or set it per collection.

When an item is no longer in a collection that requires it to have a custom sort name the old sort name is restored. 

## Keeping rating up to date for newly released items
Helps to keep the ratings of newly released movies and shows up to date until the rating settles a bit on IMDB etc. See more in config.cfg.

## Backing up IsWatched and Favorites
Kind of a bolted on functionality since it's unrelated to the main function of the script, but I needed it so I added it.

### Backuping up
Run app_backup.py to save IsWatched and Favorites for all users to json files, the files will be saved to a "backup" directory. If you only want to use this functionality it's enough to fill out "emby_server_url", "emby_user_id" and "emby_api_key" in the config file.

### Restoring backup
Run app_restore_backup.py to restore IsWatched and Favorites to ANOTHER server, see comments at top of app_restore_backup.py.

## Changelog

### Version 1.1
Can use lists by specifing MDBList name and user name of creator instead of having to know the ID. No change required for config.cfg. See example config.cfg on how to use it.

### Version 1.2
Optionally change the sort name of Emby Collections so that the collections that get modified are ordered first. On by default. Optionally add "update_collection_sort_name = False" to config.cfg to disable.

### Version 1.3
Optionally set sort names of items so that the newest items show first in the collection.

### Version 1.4
Optionally refresh metadata for newly added media. Added 2 scripts to backup IsWatched and Favorites for all users. 

### Version 1.5
New preffered method of adding lists by using the mdblist URL instead of the older method of specifying the ID or list name + author. No config file update is required, old methods will still work. See config.cfg for more info.

### Version 1.6
Added support for multiple MDBList urls for a single category.

### Version 1.61
Fix for item sort names not being updated unless collection existed prior.

## Frequently Asked Questions

- **What happens if I rename my collection in Emby or this script?**
  - A new collection will be created with the name you specify in `config.cfg`.
  
- **Does this affect my manually created collection?**
  - This will only affect collections with the same name as specified in `config.cfg`.
  
- **Do I need a server to use this script?**
  - No, you can run it on your PC and keep it open. The script refreshes the collections every n hours as specified in config.cfg.
  
- **Do the collections show for all Emby users?**
  - Yes, the collections will be visible to all Emby users.
