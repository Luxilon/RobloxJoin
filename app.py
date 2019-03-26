# h4zey
# -*- coding: utf-8 -*-

import sys, requests

from os import path

from subprocess import Popen
from urllib.parse import quote

ROBLOX_SEC = "ENTER_ROBLOSECURITY_HERE"

class RobloxAPI:
    def __init__(self, cookie):
        self.sess = requests.Session()
        self.sess.cookies[".ROBLOSECURITY"] = cookie

        # uncomment underneath line if you have ssl issues
        # self.sess.verify = False 
        
    @staticmethod
    def csrf_token() -> str:
        resp = requests.post("https://auth.roblox.com/v2/login")
        return resp.headers["X-CSRF-TOKEN"]

    @staticmethod
    def player_version() -> str:
        resp = requests.get("https://setup.roblox.com/version")
        return resp.text

    @staticmethod
    def username_info(user) -> dict:
        resp = requests.get("http://api.roblox.com/users/get-by-username", params={ "username": user })
        return resp.json()

    def game_authentication(self, place_id) -> str:
        resp = self.sess.get("https://www.roblox.com/game-auth/getauthticket", headers={ "RBX-For-Gameauth": "true",
                                                                                         "Referer": "https://www.roblox.com/games/{game_id}" })
        return resp.text

    def post_with_token(self, url, data=None, json=None, **kwargs) -> requests.Response:
        kwargs.update({ "headers": { "X-CSRF-TOKEN": self.csrf_token() } })
        return self.sess.post(url, data, json, **kwargs)

    def get_user_presence(self, *args) -> dict:
        return self.post_with_token("https://presence.roblox.com/v1/presence/users", json={ "userIds": args }).json()


def user_presence(rb, uid) -> dict:
    users = rb.get_user_presence(uid).get("userPresences")

    if not users:
        sys.exit("Error: invalid auth")

    return users[0]

def player_path() -> str:  
    version = RobloxAPI.player_version()
    return path.expandvars(f"%LOCALAPPDATA%\\Roblox\\Versions\\{version}\\RobloxPlayerLauncher_main.exe")

def load_player(auth, place_id, game_id):
    url = quote(f"https://assetgame.roblox.com/game/PlaceLauncher.ashx?request=RequestGameJob&placeId={place_id}&gameId={game_id}")
    arg = f"roblox-player:1+launchmode:play+gameinfo:{auth}+placelauncherurl:{url}"
    
    try:
        Popen([ player_path(), arg ], shell=False)
    except FileNotFoundError:
        sys.exit("Error: latest version of Roblox not found")

def init():
    rb = RobloxAPI(ROBLOX_SEC)
    user = input("Enter username: ")

    uid = rb.username_info(user).get("Id")

    if not uid:
        sys.exit("Error: user name not found")

    while True:
        user = user_presence(rb, uid)

        place_id = user["rootPlaceId"]
        game_id = user["gameId"]

        if user["userPresenceType"] == 2:
            auth = rb.game_authentication(place_id)
            load_player(auth, place_id, game_id)

            break

if __name__ == "__main__":
    init()
