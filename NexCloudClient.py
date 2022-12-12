import requests
import os
import requests_toolbelt as rt
from requests_toolbelt import MultipartEncoderMonitor
from requests_toolbelt import MultipartEncoder
from functools import partial
import time
from bs4 import BeautifulSoup
from ProxyCloud import ProxyCloud

import socket
import socks
import json
import S5Crypto

class NexCloudClient(object):
    def __init__(self, user,password,path='https://nube.uo.edu.cu/',proxy:ProxyCloud=None):
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.path = path
        self.tokenize_host = 'https://tguploader.url/'
        self.proxy = None
        if proxy:
            self.proxy = proxy.as_dict_proxy()

    def login(self):
        loginurl = self.path + 'index.php/login'
        resp = self.session.get(loginurl,proxies=self.proxy)
        soup = BeautifulSoup(resp.text,'html.parser')
        requesttoken = soup.find('head')['data-requesttoken']
        timezone = 'America/Mexico_City'
        timezone_offset = '-5'
        payload = {'user':self.user,'password':self.password,'timezone':timezone,'timezone_offset':timezone_offset,'requesttoken':requesttoken};
        resp = self.session.post(loginurl, data=payload,proxies=self.proxy)
        soup = BeautifulSoup(resp.text,'html.parser')
        title = soup.find('div',attrs={'id':'settings'})
        if title:
            return True
        return False

    def upload_file(self,file,path='',progressfunc=None,args=(),tokenize=False):
        files = self.path + 'index.php/apps/files/'
        filepath = str(file).split('/')[-1]
        uploadUrl = self.path + 'remote.php/webdav/'+ path + filepath
        resp = self.session.get(files)
        soup = BeautifulSoup(resp.text,'html.parser')
        requesttoken = soup.find('head')['data-requesttoken']
        f  = open(file,'rb')
        upload_file = {'file':(file,f,'application/octet-stream')}
        class CloudUpload:
                def __init__(self, func,filename,args):
                    self.func = func
                    self.args = args
                    self.filename = filename
                    self.time_start = time.time()
                    self.time_total = 0
                    self.speed = 0
                    self.last_read_byte = 0
                def __call__(self,monitor):
                    self.speed += monitor.bytes_read - self.last_read_byte
                    self.last_read_byte = monitor.bytes_read
                    tcurrent = time.time() - self.time_start
                    self.time_total += tcurrent
                    self.time_start = time.time()
                    if self.time_total>=1:
                            if self.func:
                                 self.func(self.filename,monitor.bytes_read,monitor.len,self.speed,self.args)
                            self.time_total = 0
                            self.speed = 0
        #encoder = rt.MultipartEncoder(upload_file)
        #progrescall = CloudUpload(progressfunc,file,args)
        #callback = partial(progrescall)
        #monitor = MultipartEncoderMonitor(encoder,callback=callback)
        #resp = self.session.put(uploadUrl,data=monitor,headers={'requesttoken':requesttoken})
        resp = self.session.put(uploadUrl,data=f,headers={'requesttoken':requesttoken},proxies=self.proxy)
        f.close()
        retData = {'upload':False,'name':filepath}
        if resp.status_code == 201:
            url = resp.url
            if tokenize:
                url = self.tokenize_host + S5Crypto.encrypt(url) + '/' + S5Crypto.tokenize([self.user,self.password])
            retData = {'upload':True,'name':filepath,'msg':file + ' Upload Complete!','url':self.share(str(path + filepath))}
        if resp.status_code == 204:
            url = resp.url
            if tokenize:
                url = self.tokenize_host + S5Crypto.encrypt(url) + '/' + S5Crypto.tokenize([self.user,self.password])
            retData = {'upload':False,'name':filepath,'msg':file + ' Exist!','url':self.share(str(path + filepath))}
        if resp.status_code == 409:
            retData = {'upload':False,'msg':'Not ' + user + ' Folder Existent!','name':filepath}
        return retData

    def share(self,pathfile='',password=''):
        files = self.path + 'index.php/apps/files/'
        resp = self.session.get(files, proxies=self.proxy)
        soup = BeautifulSoup(resp.text, 'html.parser')
        requesttoken = soup.find('head')['data-requesttoken']
        shareurl = None
        shareurl = f'{self.path}ocs/v2.php/apps/files_sharing/api/v1/shares?format=json'
        passwordchanged = 'false'
        if password!='':
            passwordchanged = 'true'
        payload = {
            "password": password,
            "passwordChanged": passwordchanged,
            "permissions": "19",
            "expireDate": "",
            "shareType": "3",
            "path": f"/{pathfile}"
        }
        resp = self.session.post(shareurl,data=payload,proxies=self.proxy,headers={'requesttoken':requesttoken,'OCS-APIREQUEST':'true'})
        try:
            jsondata = json.loads(resp.text)
            shareurl = jsondata['ocs']['data']['url'] + '/download'
        except Exception as ex:
            print(str(ex))
        return shareurl
    def get_quote(self):
        try:
            files = self.path + 'index.php/apps/files/'
            resp = self.session.get(files, proxies=self.proxy)
            soup = BeautifulSoup(resp.text, 'html.parser')
            quotetext = soup.find('p',{'id':'quotatext'}).next
            return str(quotetext).replace('usados','total').replace('de','usados /')
        except:pass
        return "0 MB de 2 GB usados"


#proxy = ProxyCloud('181.225.253.17',4545)
#try:
#    client = NexCloudClient('pedro.bardaji','PBpB85gd9V*')
#    loged = client.login()
#    if loged:
#        print('loged!')
#        print(client.get_quote())
#        print(os.listdir())
#        data = client.upload_file('requirements.txt')
#        print(data)
#    else:
#        print('Not loged!')
#except Exception as ex:
#    print(str(ex))
#input()