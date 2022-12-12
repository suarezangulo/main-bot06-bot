import aiohttp
import urllib.parse
import json
from bs4 import BeautifulSoup
import re
import socket
import socks
from aiohttp_socks import ProxyConnector
import datetime
import requests

async def send_calendar(moodle: str, user: str, passw: str, urls: list,directtoken='',proxy:str="") -> list:
    if proxy == "":
        connector = aiohttp.TCPConnector()
    else:
        connector = ProxyConnector.from_url(proxy)
    async with aiohttp.ClientSession(connector=connector) as session:
    #async with aiohttp.ClientSession() as session:
        # Extraer el token de inicio de sesión
        try:
            # Login
            async with session.get(moodle + "/login/index.php") as response:
                html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            token = soup.find("input", attrs={"name": "logintoken"})
            if token:
                token = token["value"]
            else:
                token = ""
            payload = {
                "anchor": "",
                "logintoken": token,
                "username": user,
                "password": passw,
                "rememberusername": 1,
            }
            async with session.post(moodle + "/login/index.php", data=payload) as response:
                html = await response.text()

            sesskey = re.findall('(?<="sesskey":")(.*?)(?=")', html)[-1]
            userid = re.findall('(?<=userid=")(.*?)(?=")', html)[-1]
            # Mover a calendario
            base_url = (
                "{}/lib/ajax/service.php?sesskey={}&info=core_calendar_submit_create_update_form"
            )
            today = str(datetime.date.today()).split('-')
            date = {'year':today[0],'month':today[1],'day':today[2]}
            payload = [
                {
                    "index": 0,
                    "methodname": "core_calendar_submit_create_update_form",
                    "args": {
                        "formdata": "id=0&userid={}&modulename=&instance=0&visible=1&eventtype=user&sesskey={}&_qf__core_calendar_local_event_forms_create=1&mform_showmore_id_general=1&name=Subidas&timestart[day]="+date['day']+"&timestart[month]="+date['month']+"&timestart[year]="+date['year']+"&timestart[hour]=18&timestart[minute]=55&timedurationuntil[day]="+str(int(date['day'])+2)+"&timedurationuntil[month]="+date['month']+"&timedurationuntil[hour]=18&timedurationuntil[minute]=55&timedurationuntil[year]="+date['year']+"&description[text]={}&description[format]=1&description[itemid]=940353303&location=&duration=999999"
                    },
                }
            ]
            urls_payload = '<p dir="ltr"><span style="font-size: 14.25px;">{}</span></p>'
            base_url = base_url.format(moodle, sesskey)
            urlparse = lambda url: urllib.parse.quote_plus(urls_payload.format(url))
            urls_parsed = "".join(list(map(urlparse, urls)))
            payload[0]["args"]["formdata"] = payload[0]["args"]["formdata"].format(
                userid, sesskey, urls_parsed
            )
            async with session.post(base_url, data=json.dumps(payload)) as result:
                resp = await result.json()
                resp = resp[0]["data"]["event"]["description"]

            respfinal = re.findall("https?://[^\s\<\>]+[a-zA-z0-9]", resp)

            if(directtoken!=""):
                datas = []
                for uri in respfinal:
                    datas.append(str(uri).replace('pluginfile.php','webservice/pluginfile.php') + '?token=' + directtoken)
                return datas
            return respfinal
        except Exception as e:
            return False

#import asyncio
#async def exec():
#    data = await send_calendar('https://moodle.uclv.edu.cu/','sdel','Ana720209***',['https://moodle.uclv.edu.cu/draftfile.php/179050/user/draft/325001132/Captura%20de%20pantalla%20%283%29.png'],directtoken='6285c1979721547bfb03d769ceaf6eb4');
#    print(data)
#asyncio.run(exec())