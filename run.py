import sys, os
import math
import logging
logging.basicConfig(filename="run.LOG", level=logging.INFO)
from subprocess import Popen, PIPE
from multiprocessing import Pool
from collections import defaultdict

from dominate.tags import *

from crawler import texCrawler
from settings import *

def clean():
    removeExtension = ["log", "gnuplot", "nav", "out", "snm", "toc", "aux", "tex", "pdf", "vrb", "data", "tdo", "ps"]
    removeList = [name for name in os.listdir() if name.split(".")[-1] in removeExtension]
    for name in removeList:
        os.remove(name)

def findTag(fileName):
    with open(fileName, 'r') as f:
        try:
            content = f.read()
        except UnicodeDecodeError:
            return None
    if "\n:Tags:" not in content:
        return 1
    for i,line in enumerate(content.split("\n")):
        if line[:6]==":Tags:":
            tag = line
            if ";" in tag[6:]:
                tagL = [t.strip().lower() for t in tag[6:].split(";") if t.strip()]
            elif "," in tag[6:]:
                tagL = [t.strip().lower() for t in tag[6:].split(",") if t.strip()]
            else:
                tagL = [tag[6:].strip().lower(), ]
            break
    return tagL

def _tdGen(names, availFiles):
    temp = []
    for name in names:
            if name+".jpeg" in availFiles:
                li_name = li(a(name, href = IMGPATH+name+".jpeg"))
            else:
                li_name = li(a(name))
            temp.append(li_name)
    return td(temp)

def tdGen(names, availFiles):
    a1 = math.ceil(len(names)/3)
    a2 = a1*2
    td1 = _tdGen(names[:a1], availFiles)
    td2 = _tdGen(names[a1:a2], availFiles)
    td3 = _tdGen(names[a2:], availFiles)
    return td1,td2,td3

def compileAndPrune():
    texFiles = [name for name in os.listdir(TEXPATH) if name[-4:]==".tex"]
    count = 0
    for tex in texFiles[12:16]:
        cmd = "python texCompile.py -f "+TEXPATH+tex
        # import pdb;pdb.set_trace()
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        (pout, perr) = proc.communicate()
        ret = proc.wait()
        if ret != 0:
            logging.warning("failed to compile tex file: %s"%TEXPATH+tex)
            logging.warning(perr.decode("ascii"))
        else:
            logging.info("compiled tex file: %s, count %d"%(TEXPATH+tex, count))
        count+=1
    clean()

def compileSingle(tex, timeout="20"):
    cmd = "python texCompile.py -f "+TEXPATH+tex + " -t " + timeout
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    (pout, perr) = proc.communicate()
    ret = proc.wait()
    if ret != 0:
        logging.warning("failed to compile tex file: %s"%TEXPATH+tex)
        logging.warning(perr.decode("ascii"))
        return False
    else:
        logging.info("compiled tex file: %s"%TEXPATH+tex)
        return True

def makeTagDict():
    noTagCount = 0
    texFiles = [name for name in os.listdir(TEXPATH) if name[-4:]==".tex"]
    tagDict = defaultdict(list)
    for tex in texFiles:
        res = findTag(TEXPATH+tex)
        if res is None:
            logging.warning("Failed to decode tex file: %s"%TEXPATH+tex)
        elif res==1:
            logging.info("Has no tag: %s"%TEXPATH+tex)
            noTagCount +=1
        else:
            for tag in res:
                if tag:
                    tagDict[tag].append(tex.split(".")[0])
    logging.info("%d tex files has no tag"%noTagCount)
    return tagDict

def makeHTML(tagDict):
    availFiles = os.listdir(IMGPATH)
    divs = []
    for tags in tagDict:
        h51 = h5(tags, id=tags)
        td1, td2, td3 = tdGen(tagDict[tags], availFiles)
        table1 = table(tbody(tr([td1,td2,td3])))
        t = div([h51,table1], _class="tag-table tag-list")
        divs.append(t)
    f = html(body(divs))
    with open("index.html", "w") as outf:
        outf.write(str(f))

if __name__=="__main__":
    # step1: crawl latex files
    crw = texCrawler()
    crw.crawlBatch()

    # step2&3: compile .tex file, and prune the image from pdf
    # It takes around 10 min to compile all 400+ tex files on a laptop.
    texFiles = [name for name in os.listdir(TEXPATH) if name[-4:]==".tex"]
    pool = Pool(4)
    isSuccess = pool.map(compileSingle, texFiles)
    pool.close()
    pool.join()
    logging.info("tex compilation done!")
    clean()
    
    # step2&3: slower alternative
    # compileAndPrune()

    # step4: build an html file to catigorize images by tag
    tagDict = makeTagDict()
    logging.info("Tag dictionary has been created.")

    makeHTML(tagDict)
    logging.info("HTML file has been created.")


