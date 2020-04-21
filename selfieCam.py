import cv2
import imutils.imutils as imutils
from imutils.imutils.video import VideoStream
import time
import pigpio
import datetime
import tkinter as tk
from tkinter import simpledialog
import numpy as np
from subprocess import call
import os

h = 480
w = 640
dispW,dispH = (1024,768)
frameRate = 90
cap = VideoStream(usePiCamera=True,resolution=(w,h),framerate=frameRate).start()
cap.camera.vflip = True
windName = "selfie cam"
preVid = 1
vid = 0
cv2.namedWindow(windName)
cv2.moveWindow(windName,dispW//2-w//2,dispH//2-h//2)
startTime = 0
saveName = ''
savePath = ''
time.sleep(.5)
whiteRedHold, whiteBlueHold = cap.camera.awb_gains
cap.camera.awb_mode = 'off'
cap.camera.awb_gains = (whiteRedHold,whiteBlueHold)
stop = False
charStart = 5
alpha = .75
ft = cv2.freetype.createFreeType2()
ft.loadFontData(fontFileName='Helvetica.ttf',id=0)
fontHeight = 15

def changeBrightness(brightVal):
    cap.camera.brightness = brightVal
def changeContrast(contrastVal):
    cap.camera.contrast = contrastVal*2 - 100
def startRecord(event,x,y,flags,params):
    global preVid,saveName,cap,dispW,dispH,w,h,savePath
    if preVid:
        if event==cv2.EVENT_LBUTTONDOWN and x>(w//2-h//25) and x<(w//2+h//25) and y>(9*h//10-h//25) and y<(9*h//10+h//25) and saveName != '':
            preVid = not preVid
            now = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
            saveName = "{}-{}".format(saveName,now)
            savePath = "/home/pi/selfieCam/selfieCamVids/{}".format(saveName)
            os.mkdir(savePath)
            cap.camera.start_recording(savePath+'/'+saveName+'.h264',format='h264',quality=20)
        elif event==cv2.EVENT_LBUTTONDOWN and x>8*w//10 and y>27*h//30 and x<w-10 and y<h-10:
            cap.camera.awb_mode = 'auto'
            time.sleep(.5)
            whiteRedHold, whiteBlueHold = cap.camera.awb_gains
            cap.camera.awb_mode = 'off'
            cap.camera.awb_gains = (whiteRedHold,whiteBlueHold)
def stopRecord(event,x,y,flags,params):
    global saveName,cap, stop
    if event==cv2.EVENT_LBUTTONDOWN and x>(w//2-h//25) and x<(w//2+h//25) and y>(9*h//10-h//25) and y<(9*h//10+h//25):
        stop = True
        

cv2.createTrackbar('Brightness',windName,0,100,changeBrightness)
cv2.createTrackbar('Contrast',windName,0,100,changeContrast)

cv2.setTrackbarPos('Brightness',windName,cap.camera.brightness)
cv2.setTrackbarPos('Contrast',windName,(cap.camera.brightness+100)//2)

cv2.setMouseCallback(windName,startRecord)

while True:
    state = cap.hasGotten
    frame = cap.read()
    overlay = np.copy(frame)
    cv2.rectangle(overlay,(0,0),(w,22),(200,200,200),-1)
    cv2.addWeighted(overlay,alpha,frame,1-alpha,0,frame)
    if vid:
        timeStamp = time.time()-startTime
        frameRate = int(cap.getFramerate())
        timeStamp = datetime.timedelta(seconds=int(timeStamp))
        ft.putText(frame,
                    "Recording: {}, {} fps, {} elapsed".format(saveName,frameRate, timeStamp),
                    (5,15),
                    fontHeight,
                    (255,255,255),
                    -1,
                    cv2.LINE_AA,
                    True)
        cv2.rectangle(frame, (w//2-h//30, 9*h//10-h//30),(w//2+h//30, 9*h//10+h//30),[0,0,255],-1,cv2.LINE_AA)
        cv2.rectangle(frame, (w//2-h//25, 9*h//10-h//25),(w//2+h//25, 9*h//10+h//25),[0,0,255],1,cv2.LINE_AA)
    
    if preVid:
        if saveName == '':
            cv2.circle(frame, (w//2, 9*h//10),h//30,[200,200,200],-1,cv2.LINE_AA)
            cv2.circle(frame, (w//2, 9*h//10),h//25,[200,200,200],1,cv2.LINE_AA)
        else:
            cv2.circle(frame, (w//2, 9*h//10),h//30,[0,0,255],-1,cv2.LINE_AA)
            cv2.circle(frame, (w//2, 9*h//10),h//25,[0,0,255],1,cv2.LINE_AA)
        cv2.rectangle(frame,(8*w//10,27*h//30),(w-10,h-10),(100,100,100),-1,cv2.LINE_AA)
        cv2.rectangle(frame,(8*w//10,27*h//30),(w-10,h-10),(255,255,255),1,cv2.LINE_AA)
        buttonFontHeight = 20
        text = "Reset WB"
        widthText,heightText = ft.getTextSize(text,buttonFontHeight,-1)[0]
        textX = 8*w//10+((w-10)-(8*w//10))//2-widthText//2
        textY = 27*h//30+((h-10)-(27*h//30))//2+8
        ft.putText(frame,
                    text,
                    (textX,textY),
                    buttonFontHeight,
                    (255,255,255),
                    -1,
                    cv2.LINE_AA,
                    True)
        ft.putText(frame,
                    "Save Name (all lowercase): {}".format(saveName),
                    (5,15),
                    fontHeight,
                    (255,255,255),
                    -1,
                    cv2.LINE_AA,
                    True)
    if not preVid and not vid:
        vid = not vid
        cv2.destroyWindow(windName)
        cv2.namedWindow(windName)
        cv2.moveWindow(windName,dispW//2-w//2,dispH//2-h//2)
        cv2.setMouseCallback(windName,stopRecord)
        startTime = time.time()
    if state is False:
        cv2.imshow(windName,frame)
    if stop:
        cap.camera.stop_recording()
        call(["ffmpeg",
              "-framerate","{}".format(frameRate),
              "-i","{}".format(savePath+'/'+saveName+".h264"),
              "-c","copy","{}".format(savePath+'/'+saveName+".mp4")])
        break
    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        cap.camera.stop_recording()
        if saveName != '':
            call(["ffmpeg",
                  "-framerate","{}".format(frameRate),
                  "-i","{}".format(savePath+'/'+saveName+".h264"),
                  "-c","copy","{}".format(savePath+'/'+saveName+".mp4")])
        break
    elif key == 255:
        continue
    else:
        if preVid:
            if key == 8:
                if len(saveName)>0:
                    saveName = saveName[0:-1]
            elif key<126:
                saveName += chr(key)


        
