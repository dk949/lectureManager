# original script by DavidBuchanan314: https://gist.github.com/DavidBuchanan314/26aa8bd765807798d917b983ac13213b
import argparse
import json
import os
import requests
import youtube_dl


def getUserCacheDir():
    if not (cacheDir := os.getenv('XDG_CACHE_HOME')):
        if not os.path.exists((cacheDir := os.path.join(os.path.expanduser("~"), '.cache'))):
            return None
    return cacheDir


def getUserConfigDir():
    if not (configDir := os.getenv('XDG_CONFIG_HOME')):
        if not os.path.exists((configDir := os.path.join(os.path.expanduser("~"), '.config'))):
            return None
    return configDir


def getUserDownloadsDir():
    if not os.path.exists((downloadsDir := os.path.join(os.path.expanduser("~"), 'Downloads'))):
        return None

    if not os.path.exists((appDownloadsDir := os.path.join(downloadsDir, 'lectureManager'))):
        os.mkdir(appDownloadsDir)
    return appDownloadsDir


def initArgparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="download lectures from Panopto")
    parser.add_argument("-v", "--version", action="version", version=f"{parser.prog} version 0.1.0")

    parser.add_argument('-t', '--token', type=str, nargs='?',
                        help='pass the .ASPXAUTH token, if a token cannot be found\n'
                             'token can be obtained from the browser after logging into panopto\n'
                             'it\'s a cookie')
    parser.add_argument('-b', '--panopto-base', type=str, nargs='?', dest='base',
                        help='pass the panopto base URL if one cannot not be found\n'
                             'example of a base URL could be https://york.cloud.panopto.eu')
    parser.add_argument('-s', '--settings', type=str, nargs='?', default=getUserConfigDir(),
                        help='custom config directory where settings are stored\n'
                             '(XDG_CONFIG_HOME by default)')
    parser.add_argument('-o', '--output', type=str, nargs='?', default=getUserDownloadsDir(),
                        help='custom downloads directory (~/Downloads by default)')
    parser.add_argument('-y', '--yt-dl', action='store_const', const=True, default=False, dest='ytdl',
                        help='use youtube-dl to download the stream instead of the provided download link')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-c', '--cache', type=str, nargs='?', default=getUserCacheDir(),
                       help='custom cache file location (XDG_CACHE_HOME by default)')
    group.add_argument('-n', '--no-cache', action='store_const', const=True, default=False, dest='noCache',
                       help='don\'t cache the token and the base URl')

    return parser


def useArgs() -> dict:
    out = {}
    settings = {}
    parser = initArgparse()
    args = parser.parse_args()

    # Check if a cache file exists
    if os.path.exists(cacheFile := os.path.join(args.cache, "lectureManager", 'cache.json')):
        # check if no token or base URL have been passed in cli args
        if (not args.token) and (not args.base):
            with open(cacheFile, 'r') as jsonFile:
                data = json.load(jsonFile)
                out["token"] = data["token"]
                out["base"] = data["base"]
        elif not args.noCache:
            with open(cacheFile, 'r') as jsonFile:
                data = json.load(jsonFile)

            if args.token:
                out["token"] = data["token"] = args.token

            if args.base:
                out["base"] = data["base"] = args.base

            with open(cacheFile, "w") as outfile:
                json.dump(data, outfile)
        elif args.noCache and args.token and args.base:
            if args.token:
                out["token"] = args.token

            if args.base:
                out["base"] = args.base

        out['cacheDir'] = os.path.join(args.cache, "lectureManager")

    elif args.token and args.base and (not args.noCache):
        if not (os.path.exists(cacheDir := os.path.join(args.cache, "lectureManager"))):
            os.mkdir(cacheDir)

        with open(os.path.join(cacheDir, 'cache.json'), 'w') as outfile:
            json.dump({"token": args.token, "base": args.base}, outfile)

        out["token"] = args.token
        out["base"] = args.base
        out['cacheDir'] = os.path.join(args.cache, "lectureManager")

    if args.settings:
        if os.path.exists(confFile := os.path.join(args.settings, "lectureManager", 'settings.json')):
            with open(confFile, 'r') as jsonFile:
                settings = json.load(jsonFile)
        else:
            if not (os.path.exists(confDir := os.path.join(args.settings, "lectureManager"))):
                os.mkdir(confDir)
            with open(os.path.join(confDir, 'settings.json'), 'w') as outfile:
                json.dump({"aliases": {'DIRNAME': 'ALIAS'},
                           "folders": ["DIRNAME"]}, outfile)

    if 'token' not in out or 'base' not in out:
        print('token or base missing (or could not find cache file)')
        parser.print_usage()
        exit(1)

    if not args.output:
        print("could not determine output directory")
        parser.print_usage()
        exit(1)
    if 'cacheDir' not in out:
        print("could not find cache directory, using current working directory")
        out['cacheDir'] = os.getcwd()

    out["ytdl"] = args.ytdl
    out["settings"] = settings
    out["output"] = args.output
    return out


conf = useArgs()
withYTDL = conf['ytdl']
PANOPTOBASE = conf['base']

TOKEN = conf['token']

s = requests.session()  # cheeky global variable
s.cookies = requests.utils.cookiejar_from_dict({".ASPXAUTH": TOKEN})


def jsonApi(endpoint, params=dict(), post=False, paramtype="params"):
    if post:
        r = s.post(PANOPTOBASE + endpoint, **{paramtype: params})
    else:
        r = s.get(PANOPTOBASE + endpoint, **{paramtype: params})
    if not r.ok:
        print(r.text)
    return json.loads(r.text)


def nameNormalize(name):
    return name.replace("/", "_")


def isCached(sessionName: str):
    if os.path.exists(cacheFile := os.path.join(conf['cacheDir'], 'sessionCache.json')):
        with open(cacheFile, 'r') as jsonFile:
            cache = json.load(jsonFile)
        if sessionName in cache['sessions']:
            return True
        return False
    with open(cacheFile, 'w') as jsonFile:
        json.dump({'sessions': []}, jsonFile)
    return False


def cacheSession(sessionName):
    cacheFile = os.path.join(conf['cacheDir'], 'sessionCache.json')
    with open(cacheFile, 'r') as jsonFile:
        cache = json.load(jsonFile)
    cache['sessions'].append(sessionName)
    with open(cacheFile, 'w') as jsonFile:
        json.dump(cache, jsonFile)


def useYTDL(session, deliveryInfo, destDir):
    streams = deliveryInfo["Delivery"]["Streams"]
    for i in range(len(streams)):
        filename = nameNormalize(session["SessionName"]) + "_" + str(i) + ".mp4"
        destFilename = os.path.join(destDir, filename)
        ydlOpts = {
            "outtmpl": destFilename,
            "quiet": True
        }
        with youtube_dl.YoutubeDL(ydlOpts) as ydl:
            ydl.download([streams[i]["StreamUrl"]])


def notYTDL(session, deliveryInfo, destDir):
    filename = nameNormalize(session["SessionName"])
    destFilename = os.path.join(destDir, filename + '.mp4')
    res = s.get(deliveryInfo["DownloadUrl"])
    open(destFilename, 'wb').write(res.content)


def dlSession(session):
    destDir = os.path.join(
        conf["output"],
        conf["settings"]["aliases"][session["FolderName"]] if session["FolderName"] in conf["settings"]["aliases"]
        else nameNormalize(session["FolderName"])
    )
    if not os.path.exists(destDir):
        os.makedirs(destDir)

    deliveryInfo = jsonApi("/Panopto/Pages/Viewer/DeliveryInfo.aspx", {
        "deliveryId": session["DeliveryID"],
        "responseType": "json"
    }, True, "data")

    print(f"downloading {nameNormalize(session['SessionName'])}")
    if withYTDL:
        useYTDL(session, deliveryInfo, destDir)
    else:
        notYTDL(session, deliveryInfo, destDir)


def dlFolder(folder):
    sessions = jsonApi("/Panopto/Services/Data.svc/GetSessions", {
        "queryParameters": {
            "folderID": folder["Id"],
        }
    }, True, "json")["d"]["Results"]

    for session in sessions:
        if not isCached(nameNormalize(session["SessionName"])):
            dlSession(session)
            cacheSession(nameNormalize(session["SessionName"]))


def main():
    folders = jsonApi("/Panopto/Api/v1.0-beta/Folders", {
        "parentId": "null",
        "folderSet": 1
    })

    for folder in folders:
        if folder["Name"] in conf["settings"]["folders"]:
            dlFolder(folder)


if __name__ == "__main__":
    main()
