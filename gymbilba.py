import os
import re
import copy
import json
import requests
import itertools

from bs4 import BeautifulSoup

from errors import *

class Gymbilba():
    LOGIN_URL = "https://gymbilba.edupage.org/login/edubarLogin.php?"
    BASE_URL = "https://gymbilba.edupage.org/"
    PATH = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))+"\\creds.lock"
    __MAPPER_RAN = False
    DEBUG = True

    def __init__(self):
        try:
            with open(self.PATH,"r") as _:
                if "gymbilba" not in json.loads(_.read()).keys():
                    self.create(False)
        except FileNotFoundError:
            self.create(True)
        finally:
            with open(self.PATH,"r") as _:
                _ = json.loads(_.read())
                self.auth = _["gymbilba"]["token"]
                self.name = _["gymbilba"]["username"]
                self.password = _["gymbilba"]["password"]
        self.session = requests.Session()
        self.login(mode="init")
    
    def create(self,new):
        if not new:
            with open(self.PATH,"r") as _:
                outer = json.loads(_.read())
        else:
            outer = {}
        with open(self.PATH,"w+") as _:
            data = {}
            data["token"] = None
            data["username"] = ""
            data["password"] = ""
            while data["token"] is None:
                data["token"] = str(input("Token? (optional)\n"))
            while data["username"] == "":
                data["username"] = str(input("User?\n"))
            while data["password"] == "":
                data["password"] = str(input("Password?\n"))
            outer["gymbilba"] = data
            _.write(json.dumps(outer))
        return
        
    def login(self,mode="data"):
        data = {
            "csrfauth" : self.auth,
            "username" : self.name,
            "password" : self.password
        }
        response = self.session.post(self.LOGIN_URL,data=data)
        self.full_response = response.text
        if self.DEBUG:
            with open("gymbilba.html","w+",encoding="utf-8") as _:
                _.write(response.text)
        if response.status_code == 200:
            if "<b>Ste prihlásený ako</b>" in response.text:
                if mode == "full":
                    return response.text
                elif mode == "data":
                    soup = BeautifulSoup(response.text,"html.parser")
                    script = soup.body.find_all("script")[2]
                    array = re.findall('(?si)userhome\((.*?)\);', str(script))
                    if len(array) == 1:
                        self.__data__ = json.loads("".join(array))
                        return self.__data__
                    else:
                        raise ArrayLengthError(len(array))
                elif mode == "init":
                    soup = BeautifulSoup(response.text,"html.parser")
                    script = soup.body.find_all("script")[2]
                    array = re.findall('(?si)userhome\((.*?)\);', str(script))
                    if len(array) == 1:
                        self.__data__ = json.loads("".join(array))
                    else:
                        raise ArrayLengthError(len(array))
            else:
                raise LoginError
        else:
            raise ResponseError(response.status_code)

    def get_news(self,count=-1,parse=True,outer_allowed = ["timestamp","reakcia_na","typ","user","target_user","user_meno","text","cas_udalosti","data","vlastnik","vlastnik_meno","pocet_reakcii","pomocny_zaznam","removed"],inner_allowed = ["title"]):
        data = self.__data__["items"]
        if count > len(data) or count < 1:
            count = len(data)
        if not parse:
            return data[:count-1]
        else:
            transformed = []
            for index in range(count):
                transformed_dict = {}
                live = data[index]
                for key, value in live.items():
                    if key in outer_allowed and key != "data":
                        transformed_dict[key] = value
                    elif key=="data" and type(data) is dict:
                        value = json.loads(value)
                        transformed_dict[key] = value[inner_allowed[0]]
                transformed.append(transformed_dict)
            return transformed

    def get_teachers(self,count=-1,parse=True,blacklist=["cb_hidden"]):
        data = self.__data__["dbi"]["teachers"]
        if count > len(data) or count < 1:
            count = len(data)
        if not parse:
            return dict(itertools.islice(data.items(),count))
        else:
            transformed = {}
            for index in list(data.keys()):
                if count == 0:
                    break
                live = data[index]
                transformed_dict = {}
                for key, value in live.items():
                    if key not in blacklist:
                        transformed_dict[key] = value
                transformed[live["id"]] = transformed_dict
                count -= 1
            return transformed

    def get_subjects(self,count=-1):
        if count > len(self.__data__["dbi"]["subjects"]) or count < 1:
            count = len(self.__data__["dbi"]["subjects"])
        return dict(itertools.islice(self.__data__["dbi"]["subjects"].items(),count))

    def get_classrooms(self,count=-1,parse=True,blacklist=["cb_hidden"]):
        data = self.__data__["dbi"]["classrooms"]
        if count > len(data) or count < 1:
            count = len(data)
        if not parse:
            return dict(itertools.islice(data.items(),count))
        else:
            transformed = {}
            for index in list(data.keys()):
                if count == 0:
                    break
                live = data[index]
                transformed_dict = {}
                for key, value in live.items():
                    if key not in blacklist:
                        transformed_dict[key] = value
                transformed[live["id"]] = transformed_dict
                count -= 1
            return transformed

    def get_classes(self,count=-1):
        if count > len(self.__data__["dbi"]["classes"]) or count < 1:
            count = len(self.__data__["dbi"]["classes"])
        return dict(itertools.islice(self.__data__["dbi"]["classes"].items(),count))

    def get_students(self,count=-1,parse=True,blacklist=["parent1id","parent2id","parent3id","dateto"]):
        data = self.__data__["dbi"]["students"]
        if count > len(data) or count < 1:
            count = len(data)
        if not parse:
            return dict(itertools.islice(data.items(),count))
        else:
            transformed_dict = {}
            for index in list(data.keys()):
                if count == 0:
                    break
                live = data[index]
                transformed = {}
                for key, value in live.items():
                    if key not in blacklist:
                        transformed[key] = value
                transformed_dict[index] = transformed
                count -= 1
            return transformed_dict

    def get_dayparts(self,count=-1):
        if count > len(self.__data__["dbi"]["dayparts"]) or count < 1:
            count = len(self.__data__["dbi"]["dayparts"])
        return dict(itertools.islice(self.__data__["dbi"]["dayparts"].items(),count))

    def resolve_dayparts(self,time=None,compare=False):
        if not compare:
            first_part = int(time.split(":")[0])
        else:
            first_part = int(self.get_alldonebefore().split(" ")[1].split(":")[0])
        if first_part < 6:
            return None
        elif 6 <= first_part <= 7:
            return self.__data__["dbi"]["dayparts"]["h0"]
        elif 8 <= first_part <= 11:
            return self.__data__["dbi"]["dayparts"]["h1"]
        elif 12 <= first_part <= 15:
            return self.__data__["dbi"]["dayparts"]["h2"]
        elif 16 <= first_part <= 19:
            return self.__data__["dbi"]["dayparts"]["h3"]

    def get_periods(self,count=-1,number=-1):
        if count > len(self.__data__["dbi"]["periods"]) or count < 1:
            count = len(self.__data__["dbi"]["periods"])
        if number != -1 and number < len(self.__data__["dbi"]["periods"]):
            return self.__data__["dbi"]["periods"][number]
        else:
            return self.__data__["dbi"]["periods"][:count]

    def get_processstates(self,count=-1,number=-1):
        if count > len(self.__data__["dbi"]["processStates"]) or count < 1:
            count = len(self.__data__["dbi"]["processStates"])
        if number != -1 and 0 < number < len(self.__data__["dbi"]["processStates"])+1:
            return self.__data__["dbi"]["processStates"][number]
        else:
            return dict(itertools.islice(self.__data__["dbi"]["processStates"].items(),count))

    def get_alldonebefore(self,compare=False):
        if not compare:
            return self.__data__["dbi"]["allDoneBefore"]
        else:
            return self.__data__["dbi"]["allDoneBefore"], self.resolve_dayparts(compare=True)

    def get_isstudentadult(self):
        return self.__data__["dbi"]["isStudentAdult"]

    def get_plans(self,count=-1,parse=True,blacklist=["icon","hwDataFixed2"]):
        if count > len(self.__data__["dbi"]["plans"]) or count < 1:
            count = len(self.__data__["dbi"]["plans"])
        if not parse:
            return dict(itertools.islice(self.__data__["dbi"]["plans"].items(),count))
        else:
            modified = self.__data__.copy()
            for index in list(modified["dbi"]["plans"].keys()):
                for _ in blacklist:
                    if type(modified["dbi"]["plans"][index]["settings"]) is dict:
                        modified["dbi"]["plans"][index]["settings"].pop(_, None)
                    elif isinstance(modified["dbi"]["plans"][index]["settings"],str):
                        temp = json.loads(modified["dbi"]["plans"][index]["settings"])
                        temp.pop(_,None)
                        modified["dbi"]["plans"][index]["settings"] = temp
            return dict(itertools.islice(modified["dbi"]["plans"].items(),count))

    def get_ospravedlnenkyenabled(self):
        return self.__data__["dbi"]["ospravedlnenkyEnabled"]

    def get_homeworksenabled(self):
        return self.__data__["dbi"]["homeworksEnabled"]

    def get_schooldays(self):
        return self.__data__["vyucovacieDni"]

    def get_selfinformation(self):
        return self.__data__["userrow"]

    def get_posturl(self):
        return self.__data__["postUrl"]

    def get_eventtypes(self,count=-1):
        if count > len(self.__data__["eventTypes"]) or count < 1:
            count = len(self.__data__["eventTypes"])
        dict_result = {}
        for index in range(len(self.__data__["eventTypes"])):
            dict_result[index] = self.__data__["eventTypes"][index]
        return dict(itertools.islice(dict_result.items(),count))

    def get_userid(self):
        return self.__data__["userid"]
    
    def usergroups(self):
        return self.__data__["userGroups"]

    def get_dayplan(self):
        raise UnimplementedError

    def get_namesday(self,day="all"):
        if day == "today":
            return self.__data__["meninyDnes"].split(" ")
        elif day == "tomorrow":
            return self.__data__["meninyZajtra"].split(" ")
        else:
             return {"today":self.__data__["meninyDnes"].split(" "),"tomorrow":self.__data__["meninyZajtra"].split(" ")}

    def get_periodstime(self,count=-1):
        if count > len(self.__data__["zvonenia"]) or count < 1:
            count = len(self.__data__["zvonenia"])
        dict_result = {}
        for index in range(len(self.__data__["zvonenia"])):
            dict_result[index] = self.__data__["zvonenia"][index]
        return dict(itertools.islice(dict_result.items(),count))

    def get_videourl(self):
        return self.__data__["videoUrl"]

    def get_showtimetablestate(self):
        return self.__data__["zobrazRozvrh"]

    def get_showcalendarstate(self):
        return self.__data__["zobrazKalendar"]

    def get_events(self):
        raise UnimplementedError

    def get_tips(self):
        raise UnimplementedError

    def get_etestenabled(self):
        return self.__data__["etestEnabled"]
    
    def get_updateinterval(self):
        return self.__data__["updateInterval"]

    def id_mapper(self):
        raise UnimplementedError
        if self.__MAPPER_RAN:
            return
        self.__MAPPER_RAN = True
        ids = {}
        data = {}
        for index in range(len(self.__data__["items"])):
            ids[self.__data__["items"][index]["ineid"]] = {}
            ids[self.__data__["items"][index]["ineid"]]["text"] = self.__data__["items"][index]["text"]
            ids[self.__data__["items"][index]["ineid"]]["location"] = "items"
            ids[self.__data__["items"][index]["ineid"]]["data"] = data
            data = {}
        for key in ["teachers","subjects","classrooms","absent_types","substitution_types"]:
            for index in list(self.__data__["dbi"][key].keys()):
                ids[self.__data__["dbi"][key][index]["id"]] = {}
                try:
                    ids[self.__data__["dbi"][key][index]["id"]]["text"] = self.__data__["dbi"][key][index]["firstname"] + " " + self.__data__["dbi"][key][index]["lastname"]
                    ids[self.__data__["dbi"][key][index]["id"]]["location"] = key
                except KeyError:
                    ids[self.__data__["dbi"][key][index]["id"]]["text"] = self.__data__["dbi"][key][index]["name"]
                    ids[self.__data__["dbi"][key][index]["id"]]["location"] = key
                    if key == "substitution_types":
                        data["short"] = self.__data__["dbi"][key][index]["short"] if self.__data__["dbi"][key][index]["short"] != "" else None
                ids[self.__data__["dbi"][key][index]["id"]]["data"] = data
                data = {}
        for index in list(self.__data__["dbi"]["classes"].keys()):
            ids[self.__data__["dbi"]["classes"][index]["id"]] = {}
            ids[self.__data__["dbi"]["classes"][index]["id"]]["text"] = self.__data__["dbi"]["classes"][index]["name"]
            ids[self.__data__["dbi"]["classes"][index]["id"]]["location"] = "classes"
            if self.__data__["dbi"]["classes"][index]["teacherid"] == "":
                data["teacher1id"] = None
            else:
                data["teacher1id"] = self.__data__["dbi"]["classes"][index]["teacherid"]
            if self.__data__["dbi"]["classes"][index]["teacher2id"] == "":
                data["teacher2id"] = None
            else:
                data["teacher2id"] = self.__data__["dbi"]["classes"][index]["teacher2id"]
            if self.__data__["dbi"]["classes"][index]["classroomid"] == "":
                data["classroomid"] = None
            else:
                data["classroomid"] = self.__data__["dbi"]["classes"][index]["classroomid"]
            data["teacher1"] = self.id_resolver(data["teacher1id"],_db=ids)[data["teacher1id"]]["text"]
            data["teacher2"] = self.id_resolver(data["teacher2id"],_db=ids)[data["teacher2id"]]["text"]
            data["classroom"] = self.id_resolver(data["classroomid"],_db=ids)[data["classroomid"]]["text"]
            ids[self.__data__["dbi"]["classes"][index]["id"]]["data"] = data
            data = {}
        for index in list(self.__data__["dbi"]["students"].keys()):
            ids[self.__data__["dbi"]["students"][index]["id"]] = {}
            ids[self.__data__["dbi"]["students"][index]["id"]]["text"] = self.__data__["dbi"]["students"][index]["firstname"] + " " + self.__data__["dbi"]["students"][index]["lastname"]
            ids[self.__data__["dbi"]["students"][index]["id"]]["location"] = "students"
            data["classid"] = self.__data__["dbi"]["students"][index]["classid"]
            data["parent1id"] = self.__data__["dbi"]["students"][index]["parent1id"]
            data["parent2id"] = self.__data__["dbi"]["students"][index]["parent2id"]
            data["gender"] = self.__data__["dbi"]["students"][index]["gender"]
            data["datefrom"] = self.__data__["dbi"]["students"][index]["datefrom"]
            data["numberinclass"] = self.__data__["dbi"]["students"][index]["numberinclass"]
            if self.__data__["dbi"]["students"][index]["parent3id"] == "":
                data["parent3id"] = None
            else:
                data["parent3id"] = self.__data__["dbi"]["students"][index]["parent3id"]
            data["classdata"] = self.id_resolver(data["classid"],_db=ids)[data["classid"]]
            transform = data["classdata"]["data"]
            data["classdata"].pop("data",None)
            for index2 in list(transform.keys()):
                data["classdata"][index2] = transform[index2]
            ids[self.__data__["dbi"]["students"][index]["id"]]["data"] = data
            data = {}
        self.mapped_id = ids
        return self.mapped_id.copy()

    def id_resolver(self,search,_db=None):
        if not self.__MAPPER_RAN:
            self.id_mapper()
        if _db is None:
            _db = self.mapped_id
        try:
            return copy.deepcopy({search : _db[search]})
        except KeyError:
            return {search : {"text":None,"location":None,"data":{}}}
