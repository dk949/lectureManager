# lectureManager
## What is is?
* A program to download lectures from [Panopto](https://www.panopto.com/)

## How to use it?
* When launching the script for the first time, pass your ASPXAUTH token and panopto pase URL
  * Base URL can look like this "https://york.cloud.panopto.eu/"
  * The token can be obtained from the browser after logging into the website
    * In Firefox it is in the Debug options (F12) -> Storage -> Cookies
```shell
python lectureManager.py -t "[ASPXAUTHTOKEN]" -b "[https://baseurl.xyz]"
```
* These will get cached unless the `-n` option is provided
  * Cache directory can be specified with `-c [path/to/cache/dir]`, but is set to `XDG_CACHE_HOME` by default
* After they have been downloaded names of the lectures will also get cached, so they don't have to be downloaded again
* A `settings.json` will be generated in the config directory
  * Specified with `-s` or set to `XDG_CONFIG_HOME` by default
  * This file contains names of folders to be downloaded, as well as their aliases, which will be used to name download directories
* Default download rirectory is `~/Downloads/lectureManager/FOLDERNAME`
  * Where `FOLDERNAME` is the name of the folder provided by Panopto or its alias set in `settings.json`
  * This can be specified with `-o`
  
  ## settings.json
* Currently you can specify aliases and folders to download
* syntax for these is as follows
```json
{
    "aliases": {
        "PANOPTO_DIR_NAME1": "ALIAS_DIR_NAME1",
        "PANOPTO_DIR_NAME2": "ALIAS_DIR_NAME2"
    },
    "folders": [
        "PANOPTO_DIR_NAME1",
        "PANOPTO_DIR_NAME2"
    ]
}
```
  
## youtube-dl
* The script can use [youtube-dl](https://youtube-dl.org/) instead of the download link provided by Panopto
* Sometimes when there are multiple streams, only one will be downloaded.
  * When using the download link, the streams get merged with one being scaled down in the corner of the video.
* This is not the defualt behaviour, but can be enabled with `-y`

Based on the original script by DavidBuchanan314: https://gist.github.com/DavidBuchanan314/26aa8bd765807798d917b983ac13213b
