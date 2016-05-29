# -*- coding: utf-8 -*- 
import os
import re
import urllib.request
import socket
from bs4 import BeautifulSoup  
#send mail
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
import time
import datetime
#map
import json
import operator

dataFile="E:\\all-projects\\pyProject\\Parse58\\Parse58\\Parse58.json"
jsonVal=json.load(open(dataFile, 'r'))
durationDays=int(jsonVal["durationDays"]) #only care about the info posted 5 days
durationDistance=int(jsonVal["durationDistance"]) # 8km is acceptable
mapKey=jsonVal["mapKey"] #you can get one from http://lbs.amap.com/
myPos=jsonVal["myPos"] #your home position
#for email
from_addr = jsonVal["from_addr"] 
smtp_server = jsonVal["smtp_server"] # sender's smtp server
password = jsonVal["password"]
to_addr = jsonVal["to_addr"]#receiver's email
#Parse58Parse58.json's formate should be like this:
#{
#"durationDays" : "2",
#"durationDistance" : "8000",
#"mapKey" : "bb19345e51532a23549780744",
#"myPos" : "121.316895,31.066031",
#"from_addr" : "abc@sina.com",
#"password" : "123456",
#"to_addr" : "abc@qq.com",
#"smtp_server" : "smtp.sina.com"
#}

class GaoDeMap:
    def __init__(self,strKey,city):
        self.key=strKey
        self.city=city

    def GetPositionId(self,pos):
        #http://restapi.amap.com/v3/geocode/geo?key=您的key&address=方恒国际中心A座&city=北京
        url="http://restapi.amap.com/v3/geocode/geo?key=%s&address=%s&city=%s"%(self.key,urllib.parse.quote(pos),urllib.parse.quote(self.city))
        with urllib.request.urlopen(url) as f:
            html=f.read().decode()
            jsonVal = json.loads(html)
            if len(jsonVal["geocodes"]) <1:
                aa=0
            if jsonVal["count"].strip()=="0" or jsonVal["info"].strip().lower() != "ok":
                return ""
            else:
                return jsonVal["geocodes"][0]["location"]
    def RideToPos(self,startPosId,endPosId):
        #http://restapi.amap.com/v3/direction/walking?origin=116.434307,39.90909&destination=116.434446,39.90816&key=<用户的key>
        #http://restapi.amap.com/v3/direction/driving?origin=116.481028,39.989643&destination=116.465302,40.004717&extensions=all&output=xml&key=<用户的key>
        url="http://restapi.amap.com/v3/direction/walking?origin=%s&destination=%s&key=%s"%(startPosId,endPosId,self.key)
        with urllib.request.urlopen(url) as f:
            html=f.read().decode()
            jsonVal = json.loads(html)
            if jsonVal["info"].strip().lower() != "ok":
                return 1e10
            else:
                return int(jsonVal["route"]["paths"][0]["distance"])

gmap=GaoDeMap(mapKey,"上海")
class JobInfo:
    def JobInfo(self):
        self.url=""
        self.postDate=0
        self.detail=""
        self.position=""
        self.title=""
        self.companyName=""
        self.pathLength=0
    def url(self,str):
        self.url=str
    def postDate(self, day):
        self.postDate=day
    def position(self, str):
        self.position=str
    def title(self,str):
        self.title=str
    def companyName(self,str):
        self.companyName=str
    def pathLength(self,dist):
        self.pathLength=dist
    def selfCheck(self):
        return not(self.url!="" and self.postDate==0 and self.detail=="" and self.position=="" 
                   and self.title!="" and self.companyName!="")
    def print(self):
        print(self.title,'\n',self.postDate,'\n',self.detail,'\n',self.position,'\n',self.companyName,'\n',self.url,'\n')


def ParseDetailInfoPage(url):
    workPostion,jobDescription="",""
    with urllib.request.urlopen(url) as f:
        html=f.read()
        soup=BeautifulSoup(html,'html.parser')
    tag= soup.find('div',class_='xq')
    if tag==None:
        return workPostion, jobDescription
    tag=tag.ul
    for tag in tag.find_all('li',class_='condition'):
        if tag.span.string.strip().find( '工作地址')>-1:
            #postion,松江区新桥镇新育路406弄26号
            workPostion= tag.span.next_sibling.next_sibling.string
    #job description
    tag= soup.find('div', class_='posMsg borb')
    jobDescription=tag.get_text()
    return workPostion, jobDescription

def GetWhenInfoPosted(str):
    timeStamp = int(time.time())
    timeArray = time.localtime(timeStamp)
    str=str.strip()
    if str== "今天":
        return 0
    if str.find("小时")>=0 or str.find("分钟")>=0:
        return 0
    #06-09
    convertedDate= str.split('-')
    if len(convertedDate)==2:
        postedDate=datetime.datetime(timeArray[0],int(convertedDate[0]),int(convertedDate[1]))
        tmpDay=datetime.datetime.now()-postedDate
        return tmpDay.days
    else:
        print("---unknow date type:%s",str)
    return 0

def Paser58(urlMain, allJobInfos):
    global durationDays
    #  <dl>...</dl>
    socket.setdefaulttimeout(5)
    with urllib.request.urlopen(urlMain) as f:
        html=f.read()
        soup=BeautifulSoup(html,'html.parser')
    for item in soup.find_all('dl'):
        if item.get('logr') ==None:
            continue
        tmpJobInfo= JobInfo()
        #titleTag= item.find('a',class_="t");
        titleTag=item.dt.a
        if titleTag.string==None:
            continue
        tmpJobInfo.url=titleTag.get('href').strip()
        foundTag= next((x for x in allJobInfos if x.url == tmpJobInfo.url), None)
        if foundTag!=None:
            continue
        tmpJobInfo.title=titleTag.string.strip()
        workPostion, jobDescription= ParseDetailInfoPage(tmpJobInfo.url)
        tmpJobInfo.position=workPostion.strip()
        tmpJobInfo.detail=jobDescription.strip()
        tmpJobInfo.companyName= item.find('a',class_="fl").string.strip()
        print("parsing:",tmpJobInfo.companyName)
        postDateTag=item.find('dd',class_="w68")
        if postDateTag.string!=None:
            postDate=postDateTag.string.strip()
        else:
            postDate=postDateTag.a.string.strip()
        tmpJobInfo.postDate=GetWhenInfoPosted(postDate)
        if tmpJobInfo.postDate<=durationDays:
            #we can mesure the distance now
            global gmap
            workPosId=gmap.GetPositionId(tmpJobInfo.position)
            if workPosId =="":
                print("error occur in GetPositionID")
                continue
            #discard those work far away from my home
            pathLength=gmap.RideToPos(myPos,workPosId) 
            if pathLength>durationDistance:
                print(" current distance:%d, discard this item"%pathLength)
                continue
            tmpJobInfo.pathLength=pathLength
            allJobInfos.append(tmpJobInfo)
            print("%d days:%s is good candidate"%(tmpJobInfo.postDate,tmpJobInfo.title))
        else:
            print(" curretn posted date:%d, discard this item"%tmpJobInfo.postDate)
            continue
allJobInfos=[]
allUrls=[]
#dongjing,chedun,xinqiao,maqiao,zhuanqiao,huayang,sijing,
#xinqiao baojie
allUrls.append("http://sh.58.com/xinqiao/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-01b4-3d0a-4537-da4705a4f616&ClickID=2")
#chedun baojie
allUrls.append("http://sh.58.com/chedun/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-01ba-ffcb-be34-326784e51cdf&ClickID=3")
#dongjing baojie
allUrls.append("http://sh.58.com/dongjing/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-02d5-b6d4-5069-abe12081ab42&ClickID=1")
#sijing baojie
allUrls.append("http://sh.58.com/sijing/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-01bb-0b9a-bb9d-1959e2fc4dd1&ClickID=3")
#maqiao baojie
allUrls.append("http://sh.58.com/maqiaozhen/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-0182-3651-01a2-096e67f4ea3d&ClickID=1")
#zhuanqiao baojie
allUrls.append("http://sh.58.com/zhuanqiao/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-018b-e766-8227-1b11d59bda1d&ClickID=4")

#dongjing ayi
allUrls.append("http://sh.58.com/xinqiao/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-01b4-3d0a-4537-da4705a4f616&ClickID=2")
#jiuting ayi
allUrls.append("http://sh.58.com/xinqiao/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-01b4-3d0a-4537-da4705a4f616&ClickID=2")
#xinqiao ayi
allUrls.append("http://sh.58.com/xinqiao/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-01b4-3d0a-4537-da4705a4f616&ClickID=2")
#chedun ayi
allUrls.append("http://sh.58.com/xinqiao/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-01b4-3d0a-4537-da4705a4f616&ClickID=2")
#sijing ayi
allUrls.append("http://sh.58.com/xinqiao/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-01b4-3d0a-4537-da4705a4f616&ClickID=2")
#maqiao ayi
allUrls.append("http://sh.58.com/xinqiao/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-01b4-3d0a-4537-da4705a4f616&ClickID=2")
#zhuanqiao ayi
allUrls.append("http://sh.58.com/xinqiao/job/?key=%E4%BF%9D%E6%B4%81&cmcskey=%E4%BF%9D%E6%B4%81&final=1&specialtype=gls&canclequery=isbiz%3D0&PGTID=0d302408-01b4-3d0a-4537-da4705a4f616&ClickID=2")

for curUrl in allUrls:
    Paser58( curUrl,allJobInfos)

allJobInfos.sort(key=operator.attrgetter('pathLength'))

#send info to email
def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr(( \
        Header(name, 'utf-8').encode(), \
        addr.encode('utf-8') if isinstance(addr, unicode) else addr))


mail_msg=""
for tmpInfo in allJobInfos:
    if not tmpInfo.selfCheck():
        continue
    mail_msg +="""
<p><a href="%s">%s,距离：%sm</a></p>
<p>%s 天以前发布，   %s   %s  %s</p>
<p>%s</p>
<p>---------------------------------</p>
"""%(tmpInfo.url,tmpInfo.title,tmpInfo.pathLength,tmpInfo.postDate,tmpInfo.JobInfo,tmpInfo.position,
     tmpInfo.companyName,tmpInfo.detail)

msg = MIMEText(mail_msg, 'html', 'utf-8')

#获得当前时间时间戳
timeStamp = int(time.time())
#转换为其他日期格式,如:"%Y-%m-%d %H:%M:%S"
timeArray = time.localtime(timeStamp)
otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

msg['From'] =from_addr
msg['To'] = to_addr
msg['Subject'] = "58同城筛选数据__%s"%otherStyleTime

server = smtplib.SMTP(smtp_server, 25)
server.set_debuglevel(1)
server.login(from_addr, password)
server.sendmail(from_addr, [to_addr], msg.as_string())
server.quit()