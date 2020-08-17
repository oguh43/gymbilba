import os
import re
import json
import requests
import itertools

from bs4 import BeautifulSoup

from errors import *

class Stravacz():
    LOGIN_URL = "https://www.strava.cz/Strava/Stravnik/prihlaseni"
    BASE_URL = "https://www.strava.cz/Strava/Stravnik/Uvod"
    PATH = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))+"\\creds.lock"
    DEBUG = True

    def __init__(self):
        try:
            with open(self.PATH,"r") as _:
                if "stravacz" not in json.loads(_.read()).keys():
                    self.create(False)
        except FileNotFoundError:
            self.create(True)
        finally:
            with open(self.PATH,"r") as _:
                _ = json.loads(_.read())
                self.viewstate = _["stravacz"]["viewstate_token"]
                self.viewstategenerator = _["stravacz"]["viewstategenerator_token"]
                self.school_id = _["stravacz"]["school_id"]
                self.name = _["stravacz"]["username"]
                self.password = _["stravacz"]["password"]
                self.x = _["stravacz"]["x"]
                self.y = _["stravacz"]["y"]

        self.session = requests.Session()
        #self.login(mode="init")
    
    def create(self,new):
        if not new:
            with open(self.PATH,"r") as _:
                outer = json.loads(_.read())
        else:
            outer = {}
        with open(self.PATH,"w+") as _:
            data = {}
            data["viewstate_token"] = ""
            data["viewstategenerator_token"] = ""
            data["school_id"] = ""
            data["username"] = ""
            data["password"] = ""
            data["x"] = ""
            data["y"] = ""
            while data["viewstate_token"] == "":
                data["viewstate_token"] = str(input("Viewstate token?\n "))
            while data["viewstategenerator_token"] == "":
                data["viewstategenerator_token"] = str(input("Viewstategenerator token?\n "))
            while data["school_id"] == "":
                data["school_id"] = str(input("School id?\n "))
            while data["username"] == "":
                data["username"] = str(input("User?\n "))
            while data["password"] == "":
                data["password"] = str(input("Password?\n "))
            while data["x"] == "":
                data["x"] = str(input("X?\n "))
            while data["y"] == "":
                data["y"] = str(input("Y?\n "))
            outer["stravacz"] = data
            _.write(json.dumps(outer))
        return

    def login(self,mode="data"):
        data = {
            "__VIEWSTATE": self.viewstate,
            "__VIEWSTATEGENERATOR": self.viewstategenerator,
            "zarizeni": self.school_id,
            "uzivatel": self.name,
            "heslo": self.password,
            "x": self.x,
            "y": self.y
        }
        response = self.session.post(self.LOGIN_URL,data=data)
        self.full_response = response.text
        if self.DEBUG:
            with open("stravacz.html","w+",encoding="utf-8") as _:
                _.write(response.text)
        if response.status_code == 200:
            return response.text
        else:
            raise ResponseError(response.status_code)

#PUT ON HOLD, CANT DEVELOP IF THERE IS NO DATA
raise UnimplementedError