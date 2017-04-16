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

#forum url
templateUrl="http://hzwsjc.com/forum.php?mod=forumdisplay&fid=61&sortid=10&filter=sortid&sortid=10&page=";
nPages=30
timeOut=30 #30s
exportFileName="data.csv"
illegalStr=['\xa0','\xa01','\xa02','»'];
csvFile=open(exportFileName,'w')

def removeUnknownStr(testStr):
    for curIllegalStr in illegalStr:
       testStr= str.replace(testStr,curIllegalStr,"")
    return testStr

def normalizeTimeEntiry(timeEntity):
    timeEntity.strip()
    #发表于 2015-12-30 09:48:51
    if timeEntity.count(" ") == 2:
        timeEntity = timeEntity[timeEntity.index(" "):timeEntity.rindex(" ")].strip()
        return timeEntity
    #发表于 4天前
    years = time.localtime().tm_year
    months = time.localtime().tm_mon
    days = time.localtime().tm_mday 
    if timeEntity.find("天前") > 0:
        timeEntity=timeEntity[timeEntity.index(" "):timeEntity.rindex("天前")]
        nDays=int(timeEntity)
        assert(nDays > 0)
        timeEntity="{0}-{1}-{2}".format(years,months,days-nDays)
        return timeEntity
    #发表于 1小时前
    if timeEntity.find("小时前") > 0:
        timeEntity="{0}-{1}-{2}".format(years,months,days)
        return timeEntity
    #发表于 昨天20:36
    if timeEntity.find("昨天") >0:
        timeEntity="{0}-{1}-{2}".format(years,months,days-1)
        return timeEntity
    if timeEntity.find("前天")>0:
        timeEntity="{0}-{1}-{2}".format(years,months,days-2)
        return timeEntity
    assert(False)

def removeColon(txt):
    id=txt.find("：")
    if id>0:
        return txt[id+1 : len(txt)]
    return txt

#'楼层： 第2 层，共33 层'
def parseFloorInfo(txt):
    if not txt.count("层") >=2:
        return txt
    curFloor= txt[txt.find("第")+1 : txt.find("层")]
    totoalFloor= txt[txt.find("共")+1 : txt.rfind("层")]
    return curFloor, totoalFloor
#<h2 class="house_h2">世纪城3房2厅2卫2阳台</h2>
#<ul class="house_ul2">
#<li>售&#160;&#160;&#160;&#160;&#160;&#160;&#160;价：<em>135</em>万元</li><!-- 售价 -->
#<li>面&#160;&#160;&#160;&#160;&#160;&#160;&#160;积：<em>143</em> 平方米</li><!-- 面积 -->
#<li>价格条件：净价 </li><!-- 价格条件 -->
#<li>房屋产权：商品房 </li><!-- 房屋产权 -->
#<li>房屋类型：住宅 </li><!-- 类型 -->
#<li>朝&#160;&#160;&#160;&#160;&#160;&#160;&#160;向：正南 </li><!-- 朝向 -->
#<li>装&#160;&#160;&#160;&#160;&#160;&#160;&#160;修：高档装修 </li><!-- 装修 -->
#<li>楼&#160;&#160;&#160;&#160;&#160;&#160;&#160;层： 第<em>29</em> 层，共<em>33</em> 层</li><!-- 楼层 -->
#</ul>
#<ul class="house_ul1">
#<li>户型：3 房&#160;2 厅&#160;2 卫&#160;2 阳台</li><!-- 户型 -->
#<li>楼龄： 年</li><!-- 楼龄 -->
#<li>地区：世纪城 </li><!-- 地区 -->
#<li>地址：个人 杭州湾世纪城白鹭园143平方欧式豪装 </li><!-- 地址 -->
#</ul>
def ParseDetailInfoPage(url,subFailedOpenUrl):
        socket.setdefaulttimeout(timeOut)
        try:
            with urllib.request.urlopen(url) as f:
                html = f.read().decode("gbk","ignore").encode("utf-8");
                soup=BeautifulSoup(html,'html.parser')
        except:
            subFailedOpenUrl.append(url)
            return
        postDateTags= soup.find("em",id=True)
        postDate=normalizeTimeEntiry(removeUnknownStr(postDateTags.get_text()))

        infoBlockTag=soup.find("ul",class_="house_ul2")
        liTags=infoBlockTag.find_all("li")
        price=removeColon(removeUnknownStr(liTags[0].em.get_text()))
        area=removeColon(removeUnknownStr(liTags[1].em.get_text()))
        priceCondition=removeColon(removeUnknownStr(liTags[2].get_text()))
        propertyRight=removeColon(removeUnknownStr(liTags[3].get_text()))
        houseType=removeColon(removeUnknownStr(liTags[4].get_text()))
        houseOrientation=removeColon(removeUnknownStr(liTags[5].get_text()))
        fitment=removeColon(removeUnknownStr(liTags[6].get_text()))
        curFloors, totalFloors=parseFloorInfo(removeColon(removeUnknownStr(liTags[7].get_text())))
        csvFile.write("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},".format(postDate,price,area,priceCondition,propertyRight,houseType,houseOrientation,fitment,curFloors,totalFloors))

        infoBlockTag=soup.find("ul",class_="house_ul1")
        liTags=infoBlockTag.find_all("li")
        houseCount= removeColon(removeUnknownStr(liTags[0].get_text()))
        houseAge=removeColon(removeUnknownStr(liTags[1].get_text()))
        region=removeColon(removeUnknownStr(liTags[2].get_text()))
        address=removeColon(removeUnknownStr(liTags[3].get_text()))
        csvFile.write("{0},{1},{2},{3},{4}\n".format(houseCount,houseAge,region,address,url))

def ParsePage(url,mainFailedOpenUrl,subFailedOpenUrl):
    socket.setdefaulttimeout(timeOut)
    try:
        with urllib.request.urlopen(url) as f:
            html = f.read().decode("gbk").encode("utf-8");
            soup=BeautifulSoup(html,'html.parser')
    except:
        mainFailedOpenUrl.append(url)
        return
    tag= soup.find('div',class_='fenlei wp')
    print("trying to parse {0}".format(url))
    for tag in tag.find_all('a'):
        if tag==None or tag["href"]==None :
            continue;
        infoPageUrl= tag["href"]
        print("    info page url is {0}".format(infoPageUrl))
        ParseDetailInfoPage(infoPageUrl,subFailedOpenUrl)

mainFailedOpenUrl=[]
subFailedOpenUrl=[]
for index in range(1,nPages):
    testUrl=templateUrl+str(index)
    ParsePage(testUrl,mainFailedOpenUrl,subFailedOpenUrl)
print("---1st parse: {0} main urls fail. {1} sub urls fail, need re-parse them\n".format(mainFailedOpenUrl.count,subFailedOpenUrl.count))
#re-parse those fail urls
mainFailedOpenUrl2=[]
subFailedOpenUrl2=[]
for curUrl in mainFailedOpenUrl:
    ParsePage(curUrl,mainFailedOpenUrl2,subFailedOpenUrl2)
print("---- 2nd parse: {0} main urls fail, {1} sub urls fail\n".format(mainFailedOpenUrl2,subFailedOpenUrl2))

csvFile.close()
