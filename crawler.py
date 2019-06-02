import os,sys
import pdb
from multiprocessing.dummy import Pool
from functools import partial

from bs4 import BeautifulSoup
from urllib import request
import requests
import numpy as np
from settings import *

class texCrawler(object):
    def __init__(self):
        html_doc = request.urlopen(URL0).read()
        self.soup = BeautifulSoup(html_doc, 'lxml')
        self.blackList = ["all", "about", "contribute"]
        self.texList = self.getTexList()

    def getTexList(self):
        TexList = []
        for link in self.soup.find_all('a'):
            url = link.get('href')
            if len(url.split("/"))==5 and url[:15]=="/tikz/examples/" \
                                    and url[15:-1] not in self.blackList:
                TexList.append(URL0ROOT+url)
        return TexList

    def downloadTex(self, url, filePath):
        htmldoc = request.urlopen(url).read()
        soupT = BeautifulSoup(htmldoc, 'lxml')
        for link in soupT.find_all('a'):
            url = link.get('href')
            if url[-3:]=="tex" and url[:4]!="http":
                fileName = url.split("/")[-1]
                try:
                    r = requests.get(URL0ROOT+url)
                except:
                    print("can't download %s, url is %s"%(fileName, URL0ROOT+url))
                    return False
                open(filePath+fileName, 'wb').write(r.content)
    #             print("%s downloaded"%fileName)
                break
        return True

    def crawlBatch(self):
        pool = Pool(16)
        isSuccess = pool.map(partial(self.downloadTex, filePath=TEXPATH), self.texList)
        pool.close()
        pool.join()

