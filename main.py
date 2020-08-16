import requests, json, getpass, os, re

from bs4 import BeautifulSoup

from errors import ResponseError

LOGIN_URL = "https://gymbilba.edupage.org/login/edubarLogin.php?"
BASE_URL = "https://gymbilba.edupage.org/"
PATH = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))+"\\creds.lock"

DEBUG = True

def login(**kwargs):
    data = {
        "csrfauth" : kwargs["csrfauth"],
        "username" : kwargs["username"],
        "password" : kwargs["password"]
    }
    response = requests.post(LOGIN_URL, data =data)
    print(response.status_code)
    if response.status_code == 200:
        return response.text
    else:
        raise ResponseError

def init():
    with open(PATH,"w+") as _:
        data = {}
        data["token"] = ""
        data["username"] = ""
        data["password"] = ""
        while data["token"] == "":
            data["token"] = str(getpass.getpass("Token?\n "))
        while data["username"] == "":
            data["username"] = str(input("User?\n "))
        while data["password"] == "":
            data["password"] = str(getpass.getpass("Password?\n "))
        _.write(json.dumps(data))

def main(*args,**kwargs):
    try:
        with open(PATH,"r"): pass
    except FileNotFoundError:
        init()
    finally:
        with open(PATH,"r") as _:
            _ = json.loads(_.read())
            auth = _["token"]
            name = _["username"]
            password = _["password"]
    response = login(csrfauth=auth,username=name,password=password)
    if DEBUG:
        with open("response.html","w+",encoding="utf-8") as _:
            _.write(response)
    #arr = re.findall(r'(?<={}).*?(?={})'.format("<script>","</script>"), response)
    #print(arr)

if __name__ == "__main__":
    main()
