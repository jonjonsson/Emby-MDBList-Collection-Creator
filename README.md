# Emby MDBList Collection Creator

This Python script allows you to take lists from MDBList.com and transform them into collections in Emby. MDBList is a platform that stores lists from Trakt, IMDB, and more, which can be accessed through an API.

## Prerequisites:

To use this script, you need:

* Python installed on your system
* "Requests" Python package (install with `pip install requests`)
* Admin privileges on Emby
* A user account on [MDBList](https://mdblist.com/)
* The script has been tested with Emby Version 4.7.14.0, but other recent versions should also be compatible

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

### 1. Add MDBList IDs to `config.cfg`

* Refer to `config.cfg` for examples.
* This method allows you to create collections from other users' lists, found at [MDBList Top Lists](https://mdblist.com/toplists/).
* The `config.cfg` file contains a few examples. Use these as a guide to add more lists. The parameters you'll encounter are:
  * "Id" - The ID of the MDBList you want to use. This can be found by viewing the source of the MDBList page and looking for "?list="
  * "Frequency" - The frequency at which the collection is updated. 100 = 100% of the time, 50 = 50% of the time, etc. The collections will always be created if they do not previously exist.
  * "Source" - This field is optional and is for your own records.

### 2. Automatically Download Your Lists from MDBList

By creating your own lists on MDBList (found at [My MDBList](https://mdblist.com/mylists/)), Emby collections will be automatically created from your saved lists. This feature can be turned off in `config.cfg`. Please ensure your newly created MDBLists populate items before running the script.

## Frequently Asked Questions

- **What happens if I rename my collection in Emby or this script?**
  - A new collection will be created with the name you specify in `config.cfg`.
  
- **Does this affect my manually created collection?**
  - This will only affect collections with the same name as specified in `config.cfg`.
  
- **Do I need a server to use this script?**
  - No, you can run it on your PC and keep it open. The script refreshes the collections every n hours.
  
- **Do the collections show for all Emby users?**
  - Yes, the collections will be visible to all Emby users.