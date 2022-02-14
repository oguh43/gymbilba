from __future__ import annotations

import os
import re
import copy
import json
import atexit
import requests
import itertools

from bs4 import BeautifulSoup

from errors import *

class Gymbilba():
    __LOGIN_URL = "https://gymbilba.edupage.org/login/edubarLogin.php?"
    __BASE_URL = "https://gymbilba.edupage.org/"
    __PATH = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))+"\\creds.lock"
    __MAPPER_RAN = False
    __LOGGED_IN = False
    __DEBUG = False

    def __init__(self):
        
        try:
            with open(self.__PATH,"r") as _:
                if "gymbilba" not in json.loads(_.read()).keys():
                    self.__create(new=False)
        except FileNotFoundError:
            self.__create(new=True)
        finally:
            with open(self.__PATH,"r") as _:
                _ = json.loads(_.read())
                self.auth = _["gymbilba"]["token"]
                self.name = _["gymbilba"]["username"]
                self.password = _["gymbilba"]["password"]
        self.session = requests.Session()
        self.login(mode="init")
        atexit.register(self.__destructor)
    
    def __destructor(self) -> None:
        del self.session

    def __create(self,*,new : bool) -> None:
        if not new:
            with open(self.__PATH,"r") as _:
                outer = json.loads(_.read())
        else:
            outer = {}
        with open(self.__PATH,"w+") as _:
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
        
    def login(self,*,mode : str = "data") -> tuple(str,dict,None):
        if self.__LOGGED_IN and mode == "init":
            mode = "data"
        data = {
            "csrfauth" : self.auth,
            "username" : self.name,
            "password" : self.password
        }
        response = self.session.post(self.__LOGIN_URL,data=data)
        self.full_response = response.text
        if self.__DEBUG:
            with open("gymbilba.html","w+",encoding="utf-8") as _:
                _.write(response.text)
        if response.status_code == 200:
            if "<b>Ste prihlásený ako</b>" in response.text:
                if mode == "full":
                    return response.text
                elif mode == "data":
                    soup = BeautifulSoup(response.text,"html.parser")
                    script = soup.body.find_all("script")[2]
                    array = re.findall('(?si)userhome\((.*?\})\);', str(script))
                    if len(array) == 1:
                        self.__data__ = json.loads("".join(array))
                        return self.__data__
                    else:
                        raise ArrayLengthError(len(array))
                elif mode == "init":
                    array = re.findall(r'(?<={}).*?\}}(?={})'.format("userhome\(","\);"), response.text)
                    if len(array) == 1:
                        self.__data__ = json.loads("".join(array))
                        self.__LOGGED_IN = True
                    else:
                        raise ArrayLengthError(len(array))
            else:
                raise LoginError
        else:
            raise ResponseError(response.status_code)

    def get_substitution(self):
        soup = BeautifulSoup("".join(re.findall("(?<=\\.signature {font-Size:inherit}<\\/style>)(.*)(?=<div style=\\\\\"text-align:center;font-size:12px\\\\\">)",self.session.get(f"{self.__BASE_URL}dashboard/eb.php?mode=substitution").text)).replace("\\",""),"html.parser")
        ret = soup.find_all("div",string=re.compile(".+"))
        allData = []
        for x in ret:
            allData.append(x.text)
        ret = soup.find_all("div",class_="header")
        triedy = []
        for x in ret:
            triedy.append(x.text)

        fin = {
            "meta": {}
        }
        fin["meta"]["missing_teachers"] = [re.sub(" +"," ",word.strip()) for word in re.findall(".+: (.*)",allData.pop(0))[0].split(",")]
        fin["meta"]["missing_classes"] = [re.sub(" +"," ",word.strip()) for word in re.findall(".+: (.*)",allData.pop(0))[0].split(",")]

        current = ""
        for line in allData:
            if line in triedy:
                current = line
                fin[line] = {}
                continue
            if re.search("(?<=\()(\d)(?=\))|^\d$|^\d+ ?- ?\d+$|(?<=\()(\d+ ?- ?\d+)(?=\))",line) != None:
                fin[current][re.search("(?<=\()(\d)(?=\))|^\d$|^\d+ ?- ?\d+$|(?<=\()(\d+ ?- ?\d+)(?=\))",line).group(0)] = "" 
            else:
                fin[current][list(fin[current].keys())[-1]] = line
        return fin
        
    def get_news(self,*,count : int = -1,parse : bool = True,outer_allowed : list = ["timestamp","reakcia_na","typ","user","target_user","user_meno","text","cas_udalosti","data","vlastnik","vlastnik_meno","pocet_reakcii","pomocny_zaznam","removed"],inner_allowed : list = ["title"]) -> dict:
        data = self.__data__["items"]
        if count > len(data) or count < 1:
            count = len(data)
        if not parse:
            return {key : data[key] for key in range(len(data[:count-1]))}
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
            return {key : transformed[key] for key in range(len(transformed))}

    def get_teachers(self,*,count : int = -1,parse : bool = True,blacklist : list = ["cb_hidden"]) -> dict:
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

    def get_subjects(self,*,count : int = -1) -> dict:
        if count > len(self.__data__["dbi"]["subjects"]) or count < 1:
            count = len(self.__data__["dbi"]["subjects"])
        return dict(itertools.islice(self.__data__["dbi"]["subjects"].items(),count))

    def get_classrooms(self,*,count : int = -1,parse : bool = True,blacklist : list = ["cb_hidden"]) -> dict:
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

    def get_classes(self,*,count : int =-1) -> dict:
        if count > len(self.__data__["dbi"]["classes"]) or count < 1:
            count = len(self.__data__["dbi"]["classes"])
        return dict(itertools.islice(self.__data__["dbi"]["classes"].items(),count))

    def get_students(self,*,count : int = -1,parse : bool = True,blacklist : list =["parent1id","parent2id","parent3id","dateto"]) -> dict:
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

    def get_dayparts(self,*,count : int = -1) -> dict:
        if count > len(self.__data__["dbi"]["dayparts"]) or count < 1:
            count = len(self.__data__["dbi"]["dayparts"])
        return dict(itertools.islice(self.__data__["dbi"]["dayparts"].items(),count))

    def resolve_dayparts(self,*,time : str = None,compare : bool = False) -> dict:
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

    def get_periods(self,*,count : int = -1,number : int = -1) -> dict:
        if count > len(self.__data__["dbi"]["periods"]) or count < 1:
            count = len(self.__data__["dbi"]["periods"])
        if number != -1 and number < len(self.__data__["dbi"]["periods"]):
            return self.__data__["dbi"]["periods"][number]
        else:
            return {key : self.__data__["dbi"]["periods"][key] for key in range(len(self.__data__["dbi"]["periods"][:count]))}

    def get_processstates(self,*,count : int = -1,number : int = -1) -> dict:
        if count > len(self.__data__["dbi"]["processStates"]) or count < 1:
            count = len(self.__data__["dbi"]["processStates"])
        if number != -1 and 0 < number < len(self.__data__["dbi"]["processStates"])+1:
            return self.__data__["dbi"]["processStates"][number]
        else:
            return dict(itertools.islice(self.__data__["dbi"]["processStates"].items(),count))

    def get_alldonebefore(self,*,compare : bool = False) -> tuple(str,tuple(str,dict)):
        if not compare:
            return self.__data__["dbi"]["allDoneBefore"]
        else:
            return self.__data__["dbi"]["allDoneBefore"], self.resolve_dayparts(compare=True)

    def get_isstudentadult(self) -> bool:
        return self.__data__["dbi"]["isStudentAdult"]

    def get_plans(self,*,count : int = -1,parse : bool = True,blacklist : list = ["icon","hwDataFixed2"]) -> dict:
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

    def get_ospravedlnenkyenabled(self) -> bool:
        return self.__data__["dbi"]["ospravedlnenkyEnabled"]

    def get_homeworksenabled(self) -> bool:
        return self.__data__["dbi"]["homeworksEnabled"]

    def get_schooldays(self) -> bool:
        return self.__data__["vyucovacieDni"]

    def get_selfinformation(self) -> bool:
        return self.__data__["userrow"]

    def get_posturl(self) -> bool:
        return self.__data__["postUrl"]

    def get_eventtypes(self,*,count : int = -1) -> dict:
        if count > len(self.__data__["eventTypes"]) or count < 1:
            count = len(self.__data__["eventTypes"])
        dict_result = {}
        for index in range(len(self.__data__["eventTypes"])):
            dict_result[index] = self.__data__["eventTypes"][index]
        return dict(itertools.islice(dict_result.items(),count))

    def get_userid(self) -> str:
        return self.__data__["userid"]
    
    def usergroups(self) -> dict:
        return {key : self.__data__["userGroups"][key] for key in range(len(self.__data__["userGroups"]))}

    def get_dayplan(self) -> Exception:
        raise UnimplementedError

    def get_namesday(self,*,day : str = "all") -> tuple(str,str,dict):
        if day == "today":
            return self.__data__["meninyDnes"].split(" ")
        elif day == "tomorrow":
            return self.__data__["meninyZajtra"].split(" ")
        else:
             return {"today":self.__data__["meninyDnes"].split(" "),"tomorrow":self.__data__["meninyZajtra"].split(" ")}

    def get_periodstime(self,*,count : int = -1) -> dict:
        if count > len(self.__data__["zvonenia"]) or count < 1:
            count = len(self.__data__["zvonenia"])
        dict_result = {}
        for index in range(len(self.__data__["zvonenia"])):
            dict_result[index] = self.__data__["zvonenia"][index]
        return dict(itertools.islice(dict_result.items(),count))

    def get_videourl(self) -> str:
        return self.__data__["videoUrl"]

    def get_showtimetablestate(self) -> bool:
        return self.__data__["zobrazRozvrh"]

    def get_showcalendarstate(self) -> bool:
        return self.__data__["zobrazKalendar"]

    def get_events(self) -> Exception:
        raise UnimplementedError

    def get_tips(self) -> Exception:
        raise UnimplementedError

    def get_etestenabled(self) -> bool:
        return self.__data__["etestEnabled"]
    
    def get_updateinterval(self) -> int:
        return self.__data__["updateInterval"]

    def __id_mapper(self) -> None:
        self.__MAPPER_RAN = True
        ids = {}
        data = {}
        for index in range(len(self.__data__["items"])):
            ids[self.__data__["items"][index]["ineid"]] = {}
            ids[self.__data__["items"][index]["ineid"]]["text"] = self.__data__["items"][index]["text"]
            ids[self.__data__["items"][index]["ineid"]]["location"] = "items"
            ids[self.__data__["items"][index]["ineid"]]["data"] = data
            data = {}
        for key in ["teachers","subjects","classrooms","absent_types","substitution_types","studentabsent_types","dayparts","processTypes"]:
            for index in list(self.__data__["dbi"][key].keys()):
                ids[self.__data__["dbi"][key][index]["id"]] = {}
                try:
                    ids[self.__data__["dbi"][key][index]["id"]]["text"] = self.__data__["dbi"][key][index]["firstname"] + " " + self.__data__["dbi"][key][index]["lastname"]
                    ids[self.__data__["dbi"][key][index]["id"]]["location"] = key
                except KeyError:
                    ids[self.__data__["dbi"][key][index]["id"]]["text"] = self.__data__["dbi"][key][index]["name"]
                    ids[self.__data__["dbi"][key][index]["id"]]["location"] = key
                    try:
                        data["user"] = self.__data__["dbi"][key][index]["user"]
                        data["enabled"] = self.__data__["dbi"][key][index]["enabled"]
                    except KeyError:
                        pass
                    if key in ["substitution_types","absent_types","studentabsent_types","dayparts"]:
                        data["short"] = self.__data__["dbi"][key][index]["short"] if self.__data__["dbi"][key][index]["short"] != "" else None
                        try:
                            data["excuse_type"] = self.__data__["dbi"][key][index]["excuse_type"] if self.__data__["dbi"][key][index]["excuse_type"] != "" else None
                        except KeyError:
                            try:
                                data["starttime"] = self.__data__["dbi"][key][index]["starttime"] if self.__data__["dbi"][key][index]["starttime"] != "" else None
                                data["endtime"] = self.__data__["dbi"][key][index]["endtime"] if self.__data__["dbi"][key][index]["endtime"] != "" else None
                            except KeyError:
                                pass
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
            data["teacher1"] = self.id_resolver(data["teacher1id"],__db=ids)[data["teacher1id"]]["text"]
            data["teacher2"] = self.id_resolver(data["teacher2id"],__db=ids)[data["teacher2id"]]["text"]
            data["classroom"] = self.id_resolver(data["classroomid"],__db=ids)[data["classroomid"]]["text"]
            ids[self.__data__["dbi"]["classes"][index]["id"]]["data"] = data
            data = {}
        for index in list(self.__data__["dbi"]["students"].keys()):
            ids[self.__data__["dbi"]["students"][index]["id"]] = {}
            ids[self.__data__["dbi"]["students"][index]["id"]]["text"] = self.__data__["dbi"]["students"][index]["firstname"] + " " + self.__data__["dbi"]["students"][index]["lastname"]
            ids[self.__data__["dbi"]["students"][index]["id"]]["location"] = "students"
            data["classid"] = self.__data__["dbi"]["students"][index]["classid"]
            data["parent1id"] = self.__data__["dbi"]["students"][index]["parent1id"]
            data["parent2id"] = self.__data__["dbi"]["students"][index]["parent2id"] if self.__data__["dbi"]["students"][index]["parent2id"] != "" else None
            data["gender"] = self.__data__["dbi"]["students"][index]["gender"]
            data["datefrom"] = self.__data__["dbi"]["students"][index]["datefrom"]
            data["numberinclass"] = self.__data__["dbi"]["students"][index]["numberinclass"]
            if self.__data__["dbi"]["students"][index]["parent3id"] == "":
                data["parent3id"] = None
            else:
                data["parent3id"] = self.__data__["dbi"]["students"][index]["parent3id"]
            data["classdata"] = self.id_resolver(data["classid"],__db=ids)[data["classid"]]
            transform = data["classdata"]["data"]
            data["classdata"].pop("data",None)
            for index2 in list(transform.keys()):
                data["classdata"][index2] = transform[index2]
            ids[self.__data__["dbi"]["students"][index]["id"]]["data"] = data
            data = {}
        for index in list(self.__data__["dbi"]["students"].keys()):
            for parent in ["parent1id","parent2id","parent3id"]:
                if self.__data__["dbi"]["students"][index][parent]!= "":
                    ids[self.__data__["dbi"]["students"][index][parent]] = {}
                    ids[self.__data__["dbi"]["students"][index][parent]]["text"] = self.__data__["dbi"]["students"][index]["firstname"] + " " + self.__data__["dbi"]["students"][index]["lastname"] + " " + parent
                    ids[self.__data__["dbi"]["students"][index][parent]]["location"] = "students:"+parent
                    ids[self.__data__["dbi"]["students"][index][parent]]["data"] = {}
                    ids[self.__data__["dbi"]["students"][index][parent]]["data"]["parentof"] = index
        for index in range(len(self.__data__["dbi"]["periods"])):
            ids[self.__data__["dbi"]["periods"][index]["id"]] = {}
            ids[self.__data__["dbi"]["periods"][index]["id"]]["text"] = self.__data__["dbi"]["periods"][index]["name"]
            ids[self.__data__["dbi"]["periods"][index]["id"]]["location"] = "periods"
            ids[self.__data__["dbi"]["periods"][index]["id"]]["data"] = {}
            ids[self.__data__["dbi"]["periods"][index]["id"]]["data"]["starttime"] = self.__data__["dbi"]["periods"][index]["starttime"]
            ids[self.__data__["dbi"]["periods"][index]["id"]]["data"]["endtime"] = self.__data__["dbi"]["periods"][index]["endtime"]
            ids[self.__data__["dbi"]["periods"][index]["id"]]["data"]["short"] = self.__data__["dbi"]["periods"][index]["short"]
            ids[self.__data__["dbi"]["periods"][index]["id"]]["data"]["daypartdata"] = self.resolve_dayparts(time=self.__data__["dbi"]["periods"][index]["starttime"])
        self.mapped_id = ids

    def id_resolver(self,*,search : str,__db : dict = None) -> dict:
        if not self.__MAPPER_RAN:
            self.__id_mapper()
        if __db is None:
            __db = self.mapped_id
        try:
            return copy.deepcopy({search : __db[search]})
        except KeyError:
            return {search : {"text":None,"location":None,"data":{}}}
