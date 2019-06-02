import sys, os
from subprocess import Popen, PIPE, call, TimeoutExpired
from argparse import ArgumentParser
import numpy as np
from pdf2image import convert_from_path

def imgCrop(path):
    images = convert_from_path(path)
    pic = images[0] #only use the first page
    imageData = np.asarray(pic)
    adjustedData = imageData+1 #white is (255,255,255), make it 0
    isZero = adjustedData==0
    isWhite = isZero[:,:,0]&isZero[:,:,1]&isZero[:,:,2]
    x1,x2 = getEnds(np.sum(~isWhite, axis=0))
    y1,y2 = getEnds(np.sum(~isWhite, axis=1))
    area = (x1,y1,x2+1,y2+1)
    return pic.crop(area)
    
def getEnds(array):
    x1 = 0
    x2 = 0
    for i,valid in enumerate(array):
        if valid>0:
            if x1==0:
                x1=i
            x2=i
    return (x1,x2)


if __name__=="__main__":
    parser = ArgumentParser()
    parser.add_argument("-f", dest="fileName", action='store', required=True)
    parser.add_argument("-t", dest="timeout", action='store', default="10", required=False)
    texFileName = parser.parse_args().fileName
    timeOut = parser.parse_args().timeout

    cmd = "pdflatex -halt-on-error "+texFileName
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    try:
        (pout, perr) = proc.communicate(timeout=int(timeOut))
        ret = proc.wait(timeout=int(timeOut))
    except TimeoutExpired:
        sys.stderr.write(texFileName+": " + "Compile timeout!\n")
        proc.kill()
        exit(1)

    if ret != 0:
        # error message of pdflatex is in standard out, with ! at the beginning.
        for i,line in enumerate(pout.decode("ascii").split("\n")):
            if line and line[0]=="!":
                sys.stderr.write(texFileName+": " + line+"\n")
        exit(1)
    else:
        picFilename = texFileName[:-3]+"jpeg"
        imgCrop(os.path.basename(texFileName)[:-3]+"pdf").save(picFilename, "JPEG")
