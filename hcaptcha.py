import base64
import datetime
import hashlib
import json
import math
import os
import random
import time
import typing as t
import urllib.parse

import requests

from detect_image import KindaComputerVision

xJsonT: t.TypeAlias = t.Dict[str, t.Any]

class HCaptcha:
    def __init__(self, sitekey: str, host: str, hand_mode: bool = False) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0",
        })
        self.session.proxies.update({
            "https": ""
        })
        self.sitekey = sitekey
        self.host = host
        self.hand_mode = hand_mode
        self.tries = 0
        self.version = "b1c18b1"
        self.solver = KindaComputerVision()
        self.session.trust_env = False

    def get_REQ(self) -> xJsonT:
        return self.session.post(f"https://hcaptcha.com/checksiteconfig?v={self.version}&host={self.host}&sitekey={self.sitekey}&sc=1&swa=1").json()
    
    def download_tasklist(self, question: str, tasklist: t.List[xJsonT]) -> None:
        dirname = f"{int(datetime.datetime.now().timestamp())}"
        os.makedirs(dirname)
        with open(f"{dirname}/question.txt", "w") as stream:
            stream.write(question)
        for x in tasklist:
            print(random.randint(0, 10))
            with open(dirname + f"/{x['task_key']}.png", "wb") as stream:
                stream.write(requests.get(x["datapoint_uri"]).content)

    def get_CAPTCHA(self, req: xJsonT, n: str) -> xJsonT:
        params = urllib.parse.urlencode({
            "sitekey": self.sitekey,
            "v": self.version,
            "host": self.host,
            "n": n,
            'motiondata': '{"st":1670843048749,"mm":[[57,76,1670843062410],[40,66,1670843062436],[34,56,1670843062462],[28,45,1670843062489],[26,42,1670843062514],[26,41,1670843062566],[28,41,1670843062592],[33,41,1670843062618],[37,42,1670843062645]],"mm-mp":15.666666666666666,"md":[[37,42,1670843062688]],"md-mp":0,"mu":[[37,42,1670843062742]],"mu-mp":0,"v":1,"topLevel":{"inv":false,"st":1670843048316,"sc":{"availWidth":1600,"availHeight":811,"width":1600,"height":900,"colorDepth":24,"pixelDepth":24,"top":0,"left":0,"availTop":27,"availLeft":0,"mozOrientation":"landscape-primary","onmozorientationchange":null},"nv":{"permissions":{},"pdfViewerEnabled":true,"doNotTrack":"unspecified","maxTouchPoints":0,"mediaCapabilities":{},"oscpu":"Linux x86_64","vendor":"","vendorSub":"","productSub":"20100101","cookieEnabled":true,"buildID":"20181001000000","mediaDevices":{},"serviceWorker":{},"credentials":{},"clipboard":{},"mediaSession":{},"webdriver":false,"hardwareConcurrency":12,"geolocation":{},"appCodeName":"Mozilla","appName":"Netscape","appVersion":"5.0 (X11; Ubuntu)","platform":"Linux x86_64","userAgent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0","product":"Gecko","language":"ru-RU","languages":["ru-RU","ru","en-US","en"],"locks":{},"onLine":true,"storage":{},"plugins":["internal-pdf-viewer","internal-pdf-viewer","internal-pdf-viewer","internal-pdf-viewer","internal-pdf-viewer"]},"dr":"","exec":false,"wn":[[306,726,1,1670843048319]],"wn-mp":0,"xy":[[0,0,1,1670843048319]],"xy-mp":0,"mm":[[300,111,1670843048359],[303,112,1670843048379],[300,139,1670843048449],[290,148,1670843048467],[279,155,1670843048488],[278,155,1670843048504],[279,154,1670843048527],[296,149,1670843048550],[283,439,1670843062335],[205,426,1670843062358],[123,408,1670843062384]],"mm-mp":825.7647058823529},"session":[],"widgetList":["0kpsu9eeie6"],"widgetId":"0kpsu9eeie6","href":"https://accounts.hcaptcha.com/demo","prev":{"escaped":false,"passed":false,"expiredChallenge":false,"expiredResponse":false}}',
            "hl": "ru",
            "c": json.dumps(req["c"])
        })
        self.session.headers["Content-Type"] = "application/x-www-form-urlencoded"
        return self.session.post(f"https://hcaptcha.com/getcaptcha/{self.sitekey}", data=params).json()

    def get_N(self, req_val: str) -> str:
            data = req_val.split(".")
            req = {"header": json.loads(base64.b64decode(data[0] + "=======").decode("utf-8")), "payload": json.loads(base64.b64decode(data[1] +"=======").decode("utf-8")), "raw": {"header": data[0], "payload": data[1], "signature": data[2]}}
            def a(r):
                for t in range(len(r) - 1, -1, -1):
                    if r[t] < 63:
                        r[t] += 1
                        return True
                    r[t] = 0
                return False
            i = lambda r: "".join(["0123456789/:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"[r[n]] for n in range(len(r))])
            def o(r, e: str) -> bool:
                digest = hashlib.sha1(e.encode()).digest()
                a = [digest[math.floor(n / 8)] >> n % 8 & 1 for n in range(8 * len(digest))][:r]
                index2: t.Callable[[t.List, t.Any], int] = lambda x, y: x.index(y) if y in x else -1
                return 0 == a[0] and index2(a, 1) >= r - 1 or -1 == index2(a, 1)
            def get():
                for e in range(25):
                    n = [0 for i in range(e)]
                    while a(n):
                        u = req["payload"]["d"] + "::" + i(n)
                        if o(req["payload"]["s"], u):
                            return i(n)
            return ":".join(["1", str(req["payload"]["s"]), datetime.datetime.now().isoformat()[:19].replace("T", "").replace("-", "").replace(":", ""), req["payload"]["d"],"", get()]) # type: ignore

    def try_bypass(self, captcha: xJsonT) -> xJsonT | bool:
        self.tries += 1
        print("try №", self.tries)
        try:
            print(captcha["requester_question"]["en"], len(captcha["tasklist"]), "images")
        except KeyError:
            return False
        if not self.hand_mode:
            answers = self.solver.ensure_func(captcha["requester_question"]["en"])(captcha["tasklist"])
            # self.download_tasklist(captcha["requester_question"]["en"], captcha["tasklist"])
        else:
            answers = {x: y[1] for x, y in {y["task_key"]: [print(f"image {x + 1}/{len(captcha['tasklist'])}", y["datapoint_uri"]), input()] for x, y in enumerate(captcha["tasklist"])}.items()}
        data = json.dumps({
            "v": self.version,
            "job_mode": "image_label_binary",
            "answers": answers,
            "serverdomain": self.host,
            "sitekey": self.sitekey,
            "motionData": '{"st":1670843063264,"dct":1670843063265,"mm":[[143,300,1670843063358],[144,307,1670843063385],[153,325,1670843063426],[156,341,1670843063476],[174,348,1670843063506],[308,357,1670843063658],[302,389,1670843065580],[217,423,1670843065605],[157,438,1670843065631],[139,437,1670843065657],[136,435,1670843065683],[136,435,1670843065761],[135,441,1670843065787],[138,450,1670843065813],[143,456,1670843065839],[145,458,1670843065865],[149,459,1670843065890],[154,459,1670843065917],[159,457,1670843065943],[166,452,1670843065969],[172,444,1670843065995],[182,431,1670843066020],[192,417,1670843066046],[201,408,1670843066073],[208,401,1670843066099],[212,395,1670843066125],[214,393,1670843066163],[216,390,1670843066839],[240,357,1670843066865],[254,323,1670843066891],[262,283,1670843066917],[267,245,1670843066943],[269,217,1670843066969],[269,199,1670843066995],[270,188,1670843067021],[270,180,1670843067046],[269,173,1670843067072],[267,167,1670843067098],[266,165,1670843067124],[261,166,1670843067294],[238,170,1670843067320],[193,172,1670843067345],[130,170,1670843067371],[79,163,1670843067398],[50,158,1670843067423],[43,157,1670843067450],[48,157,1670843067618],[81,172,1670843067644],[119,191,1670843067670],[141,200,1670843067695],[157,208,1670843067722],[166,215,1670843067749],[170,218,1670843067774],[177,222,1670843067800],[187,227,1670843067825],[199,233,1670843067851],[211,237,1670843067878],[222,239,1670843067903],[230,241,1670843067930],[239,244,1670843067956],[244,246,1670843067981],[244,251,1670843068164],[238,262,1670843068189],[228,283,1670843068215],[216,310,1670843068242],[207,338,1670843068267],[205,358,1670843068293],[204,367,1670843068319],[203,377,1670843068345],[203,389,1670843068371],[201,404,1670843068398],[201,414,1670843068423],[201,417,1670843068449],[201,419,1670843068488],[202,419,1670843068566],[205,416,1670843068592],[211,410,1670843068617],[223,398,1670843068644],[238,384,1670843068670],[248,371,1670843068697],[250,369,1670843068722],[246,369,1670843068826],[234,374,1670843068852],[222,377,1670843068877],[208,379,1670843068904],[198,379,1670843068929],[193,378,1670843068956],[192,378,1670843069098],[190,380,1670843069124],[186,389,1670843069151],[181,396,1670843069176],[177,403,1670843069202],[172,407,1670843069228],[165,411,1670843069255],[163,412,1670843069281],[163,413,1670843069345],[168,418,1670843069371],[176,423,1670843069397],[183,426,1670843069423],[191,428,1670843069449],[200,430,1670843069476],[206,432,1670843069501],[213,432,1670843069526],[222,432,1670843069553],[228,433,1670843069579],[234,435,1670843069605],[240,438,1670843069632],[247,442,1670843069657],[252,446,1670843069682],[255,447,1670843069709],[254,448,1670843070345],[252,445,1670843070371],[250,441,1670843070398],[246,435,1670843070423],[242,427,1670843070449],[241,421,1670843070475],[239,413,1670843070501],[236,406,1670843070527],[234,403,1670843070553],[231,402,1670843070579],[228,400,1670843070605],[221,399,1670843070631],[210,398,1670843070657],[198,396,1670843070683],[187,395,1670843070709],[177,393,1670843070734],[171,392,1670843070761],[171,391,1670843070995],[174,391,1670843071021],[183,391,1670843071047],[193,390,1670843071073],[198,389,1670843071098],[209,386,1670843071137],[220,383,1670843071163],[227,379,1670843071190],[233,375,1670843071216],[240,372,1670843071241],[244,370,1670843071280],[242,370,1670843071410],[235,375,1670843071436],[217,386,1670843071462],[193,400,1670843071488],[163,414,1670843071514],[130,423,1670843071540],[101,425,1670843071566],[85,423,1670843071591],[76,420,1670843071618],[69,417,1670843071644],[62,413,1670843071670],[51,408,1670843071696],[41,403,1670843071722],[36,401,1670843071747],[35,399,1670843071839],[39,396,1670843071865],[45,393,1670843071891],[50,391,1670843071916],[51,389,1670843071942],[51,387,1670843071968],[52,384,1670843071995],[52,381,1670843072021],[55,381,1670843072254],[62,381,1670843072280],[81,383,1670843072306],[110,385,1670843072332],[131,380,1670843072358],[152,354,1670843072384],[158,305,1670843072410],[153,248,1670843072436],[145,213,1670843072462],[144,203,1670843072487],[143,200,1670843072514],[143,198,1670843072540],[143,196,1670843072566],[143,193,1670843072592],[143,195,1670843072891],[146,205,1670843072917],[156,232,1670843072943],[171,268,1670843072968],[189,309,1670843072994],[209,346,1670843073021],[231,384,1670843073047],[248,412,1670843073072],[258,433,1670843073099],[265,449,1670843073124],[268,459,1670843073151],[268,465,1670843073176],[268,473,1670843073202],[266,479,1670843073501],[266,476,1670843073528],[267,473,1670843073553],[268,471,1670843073605],[268,470,1670843073631],[270,467,1670843073657],[272,465,1670843073683]],"mm-mp":27.86522911051214,"md":[[266,165,1670843067196],[43,157,1670843067496],[245,247,1670843068010],[250,369,1670843068723],[193,378,1670843068979],[255,448,1670843069732],[170,391,1670843070816],[244,370,1670843071306],[52,381,1670843072085],[143,193,1670843072631],[272,464,1670843073722]],"md-mp":652.6,"mu":[[266,165,1670843067272],[43,157,1670843067572],[245,247,1670843068087],[250,369,1670843068806],[193,378,1670843069053],[255,448,1670843069797],[170,391,1670843070898],[244,370,1670843071383],[52,381,1670843072147],[143,193,1670843072705],[272,464,1670843073792]],"mu-mp":652,"topLevel":{"inv":false,"st":1670843048316,"sc":{"availWidth":1600,"availHeight":811,"width":1600,"height":900,"colorDepth":24,"pixelDepth":24,"top":0,"left":0,"availTop":27,"availLeft":0,"mozOrientation":"landscape-primary","onmozorientationchange":null},"nv":{"permissions":{},"pdfViewerEnabled":true,"doNotTrack":"unspecified","maxTouchPoints":0,"mediaCapabilities":{},"oscpu":"Linux x86_64","vendor":"","vendorSub":"","productSub":"20100101","cookieEnabled":true,"buildID":"20181001000000","mediaDevices":{},"serviceWorker":{},"credentials":{},"clipboard":{},"mediaSession":{},"webdriver":false,"hardwareConcurrency":12,"geolocation":{},"appCodeName":"Mozilla","appName":"Netscape","appVersion":"5.0 (X11; Ubuntu)","platform":"Linux x86_64","userAgent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0","product":"Gecko","language":"ru-RU","languages":["ru-RU","ru","en-US","en"],"locks":{},"onLine":true,"storage":{},"plugins":["internal-pdf-viewer","internal-pdf-viewer","internal-pdf-viewer","internal-pdf-viewer","internal-pdf-viewer"]},"dr":"","exec":false,"wn":[],"wn-mp":0,"xy":[],"xy-mp":0,"mm":[[283,439,1670843062335],[205,426,1670843062358],[123,408,1670843062384],[132,411,1670843063256],[137,418,1670843063318],[262,606,1670843073229],[261,612,1670843073255],[260,616,1670843073281],[260,618,1670843073307],[260,616,1670843073410],[259,610,1670843073437],[259,607,1670843073461],[259,604,1670843073488]],"mm-mp":761.4848484848485},"v":1}',
            "n": self.get_N(captcha['c']["req"]),
            "c": json.dumps(captcha["c"]).replace(" ", "")
        })
        self.session.headers["Content-type"] = "application/json"
        a = self.session.post(f"https://hcaptcha.com/checkcaptcha/{self.sitekey}/{captcha['key']}", data=data)
        return a.json()

    def solve(self, req: t.Optional[str] = None) -> xJsonT:
        data: xJsonT | bool = self.get_REQ() if not req else {"c": req}
        data['c']["type"] = "hsl"
        n = self.get_N(data["c"]["req"])
        captcha: xJsonT = self.get_CAPTCHA(data, n)
        if captcha.get("pass"):
            print("Solved at Get_Captcha.")
            return captcha
        captcha["c"]["type"] = "hsl"
        data = self.try_bypass(captcha)
        if isinstance(data, bool):
            print("ratelimited")
            return self.solve()
        if data.get("pass"):
            print("Solved with images.")
            return data
        else:
            print("trying again...")
            val = data["c"]
            val["type"] = "hsl"
            return self.solve(req=val)
                
# tim = time.time()
# a = HCaptcha(sitekey="a5f74b19-9e45-40e0-b45d-47ff91b7a6c2", host="accounts.hcaptcha.com", hand_mode=False)
# a = HCaptcha(sitekey="f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34", host="discord.com", hand_mode=False)
# print(a.solve())
# print("Solved In", time.time() - tim, "seconds")
# for hand mode write true or false
