# Emby MDBList Collection Creator 1.81

This tool allows you to convert lists from MDBList.com into collections within your Emby media server. MDBList aggregates content lists from various platforms including Trakt and IMDB.

## Features

* List Conversion: Transform MDBList lists into Emby collections
* Metadata Refresh: Keep ratings up-to-date for newly released content
* Collection Images: Upload local or remote images for collections posters
* Seasonal Collections: Specify when a collections should be visible
* Collection Ordering: Show your collections in order of which one was update
* Backup & Restore: Additional utilities to backup and restore watch history and favorites

## Prerequisites:

To use this script, you need:

* At minimum Python 3.11 installed on your system
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

If config_hidden.cfg exists it will be used instead. Just copy paste the contents of config.cfg into config_hidden.cfg and make your changes there. When updating the script, you can safely overwrite config.cfg without losing your settings.

### Running the Script

To run the script, follow these steps:

1. **Open a Command Prompt or Terminal:**
  - On Windows, press `Win + R`, type `cmd`, and press Enter.
  - On macOS or Linux, open the Terminal application.

2. **Navigate to the Project Directory:**
  - Use the `cd` command to change to the directory where the script is located. For example:
    ```bash
    cd /path/to/Emby-MDBList-Collection-Creator
    ```

3. **Install Required Packages:**
  - Ensure you have Python installed. You can download it from [python.org](https://www.python.org/).
  - Install the required Python package by running:
    ```bash
    pip install requests
    ```

4. **Run the Script:**
  - Execute the script by running:
    ```bash
    python app.py
    ```

If you encounter any issues, ensure you have followed each step correctly and have the necessary permissions.


### Running the Script in Docker

To run the script in a Docker container, you will need to mount a configuration file to `/app/config.cfg` but that's it - no ports need exposing.

An example docker run command:

```bash
docker run -v /path/to/config.cfg:/app/config.cfg ghcr.io/jonjonsson/emby-mdblist-collection-creator
```

Or use this example compose file:

```yml
version: '3.8'

services:
    emby-mdblist-collection-creator:
        image: ghcr.io/jonjonsson/emby-mdblist-collection-creator:latest
        volumes:
            - /path/to/config.cfg:/app/config.cfg
```


### Building the docker image manually

It's not necessary to build the image yourself, but should you choose to, you need these two commands:

1. Build the Docker image:

```bash
docker build -t emby-mdblist . --load
```

2. Run the Docker container, passing in the config file via a volume mount:

```bash
docker run -v .\config_hidden.cfg:/app/config.cfg emby-mdblist
```

(Use `./config_hidden.cfg` if you are on a Unix-based system)

## Creating Emby Collections from MDBList Lists

There are two methods to create Emby collections from MDBList lists:

### 1. Add MDBList URLs to `config.cfg` or `config_hidden.cfg` 

* Refer to `config.cfg` for examples.
* This method allows you to create collections from other users' lists, found at [MDBList Top Lists](https://mdblist.com/toplists/) for example.
* The `config.cfg` file contains examples. Use these as a guide to add more lists. 

### 2. Automatically Download Your Lists from MDBList

By creating your own lists on MDBList (found at [My MDBList](https://mdblist.com/mylists/)), Emby collections will be automatically created from your saved lists. This feature can be turned off in `config.cfg`. Please ensure your newly created MDBLists populate items before running the script.

## Sorting Shows and Movies by time added

This feature is off by default. Emby can not (yet) sort items inside collections by time added to library. That means you can't sort collections to show what is newest first. This is a shame if you have a Trending Movies collection for example and you can't see what's new at a glance. 

To address this you can have this script update the sort names of items that are in collections. It updates item sort name in the metadata so that the sort name is appended with "!!![number_of_minutes_until_year_2100_from_the_date_time_added_to_emby]". That way the newest items show first when sorted in the default alphabetical order. This will affect the sorting of these items elsewhere as well which you may or may not care about, you can always turn it off later and the old sort name will be restored on the next run of the script.

You can set this on by default for all collection in the config or set it per collection.

When an item is no longer in a collection that requires it to have a custom sort name the old sort name is restored. 

## Keeping rating up to date for newly released items
Helps to keep the ratings of newly released movies and shows up to date until the rating settles a bit on IMDB etc. See more in config.cfg.

## Seasonal lists
You can specify a period of the year to show a collection for. For example only show a collection during Christmas every year. You can also specify an end date so a collection does not show again after a specific date, useful for something like this years Oscars collection that you don't want to be hanging about forever. See example in config file.

## Collection posters
Specify the image to use as a collection poster, either a local image or an image url. See examples in config.cfg.

## Backing up IsWatched and Favorites
Kind of a bolted on functionality since it's unrelated to the main function of the script, but I needed it so I added it.

### Backuping up
Run app_backup.py to save IsWatched and Favorites for all users to json files, the files will be saved to a "backup" directory. If you only want to use this functionality it's enough to fill out "emby_server_url", "emby_user_id" and "emby_api_key" in the config file.

### Restoring backup
Run app_restore_backup.py to restore IsWatched and Favorites to ANOTHER server, see comments at top of app_restore_backup.py.

## Frequently Asked Questions

- **What happens if I rename my collection in Emby or this script?**
  - A new collection will be created with the name you specify in the config file and the renamed collection will be ignored by the script. 
  
- **Does this affect my manually created collection?**
  - This will only affect collections with the same name as specified in the config file.
  
- **Do I need a server to use this script?**
  - No, you can run it on your Windows or Mac PC and just keep it open. The script refreshes the collections every n hours as specified in config.cfg.
  
- **Do the collections show for all Emby users?**
  - Yes, the collections will be visible to all Emby users.

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
Added support for multiple MDBList urls for a single collection.

### Version 1.61 + 1.62
Fix for item sort names not being updated unless collection existed prior. Additional error handling.

### Version 1.7
Added ability to have seasonal or temporary lists like for Halloween, Christmas, Oscars etc. Thanks to @cj0r for the idea. See example in config file. No breaking changes for any older version.

### Version 1.71
Added Docker support thanks to @neoKushan. Minor fix for seasonal lists.

### Version 1.8
Added ability to set collection posters.

### Version 1.81
Can set custom sort name for a collection. Use "collection_sort_name" in config.