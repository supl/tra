#!/usr/bin/env python3

import requests
import json
import base64
import subprocess
import sys
import time
import twid
import os
import dateutil.parser as date_parser
import getopt
import random
import re
from pprint import pprint

optlist, _ = getopt.getopt(sys.argv[1:], "d:n:f:t:s:")
for opt, value in optlist:
    if opt == '-d':
        go_date = date_parser.parse(value).strftime("%Y-%m-%d")
    elif opt == '-n':
        go_train = value
    elif opt == '-f':
        from_station = value
    elif opt == '-t':
        to_station = value
    elif opt == '-s':
        go_normal_seat = value

person_id = twid.random()
ac = "d32fe414-1004-4904-8a1d-700ed8bed7b7"
ky = "80928E"
vc = "1B91364AAA7A4403A37BB8190187E6C7"
url = "https://mobile.railway.gov.tw/AppService/TRTrainService.ashx"
host = "mobile.railway.gov.tw"
tmpimg = 'tmp{}.jpg'.format(os.getpid());

def main():
    while True:
        try:
            CaptchaImageBase64, CaptchaSessionCode = getCaptcha(ac, ky, vc)
            with open(tmpimg, 'wb') as f:
                f.write(base64.b64decode(CaptchaImageBase64))

            CaptchaCode = subprocess.check_output(['tesseract', tmpimg, 'stdout']).decode('utf-8').strip()
            print('Captcha Code: ' + CaptchaCode)
            os.unlink(tmpimg)

            if re.search(r'[^a-zA-Z0-9]', CaptchaCode):
                print('Skip because invalid CaptchaCode')
                continue

            ComputerCode = bookTrainTicket(CaptchaSessionCode, CaptchaCode, person_id, go_date, go_train, from_station, to_station, go_normal_seat)
            if ComputerCode is not None:
                sys.exit('身分證號: {} && 電腦代碼: {}'.format(person_id, ComputerCode))

        except Exception as e:
            print(e)

        random.seed()
        sleep_s = random.randint(60, 120)
        print("sleep {} seconds...\n".format(sleep_s))
        time.sleep(sleep_s)

def getCaptcha(ac, ky, vc):
    post = {"ASK": "getCaptcha", "AC": ac, "KY": ky, "VC": vc}
    j = requests.post(
        url,
        data=post,
        headers={"Host": host, "User-Agent": "Mozilla/5.0"},
        proxies={ "http": "socks5://localhost:9050", "https": "socks5://localhost:9050", }
    ).json()

    print(j['Description'])
    if j['IsSuccess']:
        return (j['CaptchaImageBase64'], j['CaptchaSessionCode'])
    else:
        raise Exception('failed')

def bookTrainTicket(CaptchaSessionCode, CaptchaCode, person_id, go_date, go_train, from_station, to_station, go_normal_seat):
    post = {
        "ASK": "bookTrainTicket",
        "AC": ac,
        "KY": ky,
        "VC": vc,
        "LANG": "en-US",
        "CAPTCHA_SESSION_CODE": CaptchaSessionCode,
        "CAPTCHA_CODE": CaptchaCode,
        "GO_DATE": go_date,
        "FROM_STATION": from_station,
        "TO_STATION": to_station,
        "BOOKING_GO_TICKET": "1",
        "GO_TRAIN": go_train,
        "GO_NORMAL_SEATS": go_normal_seat,
        "PERSON_ID": person_id,
        "GO_DESK_SEATS": "0",
        "BOOKING_BACK_TICKET": "0",
        "BACK_DATE": "",
        "BACK_TRAIN": "",
        "BACK_NORMAL_SEATS": "0",
        "BACK_DESK_SEATS": "0",
    }

    j = requests.post(
        url,
        data=post,
        headers={ "Host": host, "User-Agent": "Mozilla/5.0" },
        proxies={ "http": "socks5://localhost:9050", "https": "socks5://localhost:9050", }
    ).json()
    print(j['Data']['GoTicketResult']['Description'])

    success = j['Data']['GoTicketResult']['IsBookingSuccess']
    return j['Data']['GoTicketResult']['ComputerCode'] if success else None

if __name__ == "__main__":
    main()
