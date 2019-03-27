# h4zey
# -*- coding: utf-8 -*-

import sys, requests

from glob import glob
from os.path import expandvars

from enum import Enum, unique

from subprocess import Popen
from urllib.parse import quote

class RobloxAPI:
    def __init__(self, cookie):
        self.sess = requests.Session()
        self.sess.cookies[".ROBLOSECURITY"] = cookie
        
    @staticmethod
    def csrf_token() -> str:
        resp = requests.post("https://auth.roblox.com/v2/login")
        return resp.headers["X-CSRF-TOKEN"]

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


@unique
class Status(Enum):
    OFFLINE = 0
    ONLINE = 1
    PLAYING = 2


def user_presence(rb, uid) -> dict:
    users = rb.get_user_presence(uid).get("userPresences")

    if not users:
        sys.exit("Error: invalid auth")

    return users[0]

def player_path() -> str:
    roblox = expandvars(f"%LOCALAPPDATA%\\Roblox\\Versions")

    for f in glob(f"{roblox}\\**\\RobloxPlayerLauncher.exe"):
        return f

def load_player(auth, place_id, game_id):
    url = quote(f"https://assetgame.roblox.com/game/PlaceLauncher.ashx?request=RequestGameJob&placeId={place_id}&gameId={game_id}")
    arg = f"roblox-player:1+launchmode:play+gameinfo:{auth}+placelauncherurl:{url}"
    
    try:
        Popen([ player_path(), arg ], shell=False)
    except FileNotFoundError:
        sys.exit("Error: latest version of Roblox not found")

def join_game(rb, place_id, game_id) -> bool:
    auth = rb.game_authentication(place_id)
    load_player(auth, place_id, game_id)

    return True

def init():
    cookie = input("Enter ROBLOSECURITY: ")
    rb = RobloxAPI(cookie)

    user = input("Enter username: ")
    uid = rb.username_info(user).get("Id")

    if not uid:
        sys.exit("Error: user name not found")

    while True:
        info = user_presence(rb, uid)

        place_id = info["rootPlaceId"]
        game_id = info["gameId"]

        status = info["userPresenceType"]

        print(f"[User: <{user}> => {Status(status)}]")

        if status == 2:
            if join_game(rb, place_id, game_id):
                break

if __name__ == "__main__":
    print(player_path())
