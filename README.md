
# Emby MDBList Collection Creator
A Python script can take MDBList.com lists and create collections from them in Emby. MDBList stores Trakt and IMDB lists (and more) that can be accessed via API.

## Requirements:
* "requests" Python package. Install with "pip install requests"
* Admin user on Emby
* A user on https://mdblist.com/

## Fill in the admin section in config.cfg.

You'll need the Emby server URL, Emby user ID, Emby API key and an MDBList API key.
See comments in *config.cfg* for further info.

## There are 2 ways to create collections from lists on MDBList

### Add list MDBList IDs to config.cfg
* See *config.cfg* for examples.
* Use this to create collections from other people's lists. You will find these lists at https://mdblist.com/toplists/
* There are a couple of examples in *config.cfg*. Use that to add more lists. You'll see the following parameters:
* * "Id" - Specify the ID of the MDBList you want to use. You can find this ID by viewing the source of the MDBList page and look for "?list="
* * "Frequency" is how often the collection is updated. 100 = 100% of the time. 50 = 50% etc. It will always run the first time.
* *  "Source" is optional and just for your own record.

### Automatically download your created lists on MDBList
You can create your own lists on MDBList, see https://mdblist.com/mylists/. Emby collections will be automatically created from your saved lists on MDBList. You can turn this off in config.cfg. Wait for your newly created MDBLists lists to populate items before running the script.

## FAQ
* What happens if I rename my collection in Emby or this script
* * Another collection will be created with whatever name you specify in config.cfg
* Does this affect my collection that I have created manually?
* * Only if they have the same name as you specify in config.cfg
* Do I need a server to use this script?
* * No, you can just run it on your PC and keep it open. It refreshes the collections every n hour.
* Do the collections show for all Emby users?
* * Yes.

## Helpful URLS for dev:
* https://swagger.emby.media/?staticview=true#/
* https://github.com/MediaBrowser/Emby/wiki
* https://dev.emby.media/doc/restapi/Browsing-the-Library.html
* https://dev.emby.media/home/sdk/apiclients/Python/README.html