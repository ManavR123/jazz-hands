import cv2
import numpy as np
import copy
import math
import simpleaudio as sa
#from appscript import app

# Environment:
# OS    : Mac OS EL Capitan
# python: 3.5
# opencv: 2.4.13

# parameters
cap_region_x_begin=0.5  # start point/total width
cap_region_y_end=1  # start point/total width
threshold = 60  #  BINARY threshold
blurValue = 41  # GaussianBlur parameter
bgSubThreshold = 50
learningRate = 0
prev = 0
prevprev = 0

# variables
isBgCaptured = 0   # bool, whether the background captured
triggerSwitch = False  # if true, keyborad simulator works

def printThreshold(thr):
    print("Changed threshold to "+str(thr))


def removeBG(frame):
    fgmask = bgModel.apply(frame,learningRate=learningRate)
    # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    # res = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

    kernel = np.ones((3, 3), np.uint8)
    fgmask = cv2.erode(fgmask, kernel, iterations=1)
    res = cv2.bitwise_and(frame, frame, mask=fgmask)
    return res


def calculateFingers(res, drawing):  # -> finished bool, cnt: finger count
    #  convexity defect
    hull1 = cv2.convexHull(res[0], returnPoints=False)
    hull2 = cv2.convexHull(res[1], returnPoints=False)
    ret = True
    cnt = 0

    # print('Len hull1: ' + str(len(hull1)))
    # print('Len hull2: ' + str(len(hull2)))

    if len(hull1) > 3:
        defects1 = cv2.convexityDefects(res[0], hull1)
        if type(defects1) == type(None):  # avoid crashing.   (BUG not found)
            ret = False
        else:
           for i in range(defects1.shape[0]):  # calculate the angle
               s, e, f, d = defects1[i][0]
               start = tuple(res[0][s][0])
               end = tuple(res[0][e][0])
               far = tuple(res[0][f][0])
               a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
               b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
               c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
               angle = math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c))  # cosine theorem
               if angle <= math.pi / 2:  # angle less than 90 degree, treat as fingers
                   cnt += 1
                   cv2.circle(drawing, start, 8, [211, 84, 0], -1)
    
    if len(hull2) > 3 and (len(hull1) != len(hull2)):
        defects2 = cv2.convexityDefects(res[1], hull2)
        if type(defects2) == type(None):
            ret = False
        else:
            for i in range(defects2.shape[0]):  # calculate the angle
                s, e, f, d = defects2[i][0]
                start = tuple(res[1][s][0])
                end = tuple(res[1][e][0])
                far = tuple(res[1][f][0])
                a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
                b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
                c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
                angle = math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c))  # cosine theorem
                if angle <= math.pi / 2:  # angle less than 90 degree, treat as fingers
                    cnt += 1
                    cv2.circle(drawing, start, 8, [211, 84, 0], -1)
                    
    if ret:
        return True, cnt
    else:
        return False, 0


# Camera
camera = cv2.VideoCapture(0)
camera.set(10,200)
cv2.namedWindow('trackbar')
cv2.createTrackbar('trh1', 'trackbar', threshold, 100, printThreshold)


while camera.isOpened():
    ret, frame = camera.read()
    threshold = cv2.getTrackbarPos('trh1', 'trackbar')
    frame = cv2.bilateralFilter(frame, 5, 50, 100)  # smoothing filter
    frame = cv2.flip(frame, 1)  # flip the frame horizontally
    cv2.rectangle(frame, (int(cap_region_x_begin * frame.shape[1]), 0),
                 (frame.shape[1], int(cap_region_y_end * frame.shape[0])), (255, 0, 0), 2)
    cv2.imshow('original', frame)

    #  Main operation
    if isBgCaptured == 1:  # this part won't run until background captured
        img = removeBG(frame)
        img = img[0:int(cap_region_y_end * frame.shape[0]),
                    int(cap_region_x_begin * frame.shape[1]):frame.shape[1]]  # clip the ROI
        #cv2.imshow('mask', img)

        # convert the image into binary image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (blurValue, blurValue), 0)
        #cv2.imshow('blur', blur)
        ret, thresh = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)
        #cv2.imshow('ori', thresh)

        # get the coutours
        thresh1 = copy.deepcopy(thresh)
        contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        length = len(contours)
        first = second = -1
        ci = ci2 = 0
        if length > 0:
            for i in range(length):  # find the biggest contour (according to area)
                temp = contours[i]
                area = cv2.contourArea(temp)
                if area > first:
                    second = first
                    first = area
                    ci = i 
                elif area > second:# and area != first):
                    second = area
                    ci2 = i

            res = contours[ci]
            res2 = contours[ci2]
            hull = cv2.convexHull(res)
            hull2 = cv2.convexHull(res2)
            drawing = np.zeros(img.shape, np.uint8)
            cv2.drawContours(drawing, [res], 0, (0, 255, 0), 2)
            cv2.drawContours(drawing, [res2], 0, (0, 255, 0), 2)
            #cv2.drawContours(drawing, [hull], 0, (0, 0, 255), 3)

            isFinishCal, cnt = calculateFingers([res, res2], drawing)
            if triggerSwitch and isFinishCal:
                if cnt == 0:
                    prevprev = prev
                    prev = 0
                    print(cnt)
                elif cnt == 1 and cnt != prev and cnt != prevprev:
                    prevprev = prev
                    prev = 1
                    filename = 'a.wav'
                    wave_obj = sa.WaveObject.from_wave_file(filename)
                    play_obj = wave_obj.play()
                    #play_obj.wait_done()  # Wait until sound has finished playing
                    print(cnt)
                elif cnt == 2 and cnt != prev and cnt != prevprev:
                    prevprev = prev
                    prev = 2
                    filename = 'b.wav'
                    wave_obj = sa.WaveObject.from_wave_file(filename)
                    play_obj = wave_obj.play()
                    #play_obj.wait_done()  # Wait until sound has finished playing
                    print(cnt)
                elif cnt == 3 and cnt != prev and cnt != prevprev:
                    prevprev = prev
                    prev = 3
                    filename = 'c.wav'
                    wave_obj = sa.WaveObject.from_wave_file(filename)
                    play_obj = wave_obj.play()
                    #play_obj.wait_done()  # Wait until sound has finished playing
                    print(cnt)
                elif cnt == 4 and cnt != prev and cnt != prevprev:
                    prevprev = prev
                    prev = 4
                    filename = 'd.wav'
                    wave_obj = sa.WaveObject.from_wave_file(filename)
                    play_obj = wave_obj.play()
                    #play_obj.wait_done()  # Wait until sound has finished playing
                    print(cnt)
                elif cnt == 5 and cnt != prev and cnt != prevprev:
                    prevprev = prev
                    prev = 5
                    filename = 'e.wav'
                    wave_obj = sa.WaveObject.from_wave_file(filename)
                    play_obj = wave_obj.play()
                    #play_obj.wait_done()  # Wait until sound has finished playing
                    print(cnt)
                elif cnt == 6 and cnt != prev and cnt != prevprev:
                    prevprev = prev
                    prev = 6
                    filename = 'f.wav'
                    wave_obj = sa.WaveObject.from_wave_file(filename)
                    play_obj = wave_obj.play()
                    #play_obj.wait_done()  # Wait until sound has finished playing
                    print(cnt)
                elif cnt == 7 and cnt != prev and cnt != prevprev:
                    prevprev = prev
                    prev = 7
                    filename = 'g.wav'
                    wave_obj = sa.WaveObject.from_wave_file(filename)
                    play_obj = wave_obj.play()
                    #play_obj.wait_done()  # Wait until sound has finished playing
                    print(cnt)
                
                #app('System Events').keystroke(' ')  # simulate pressing blank space
                

        cv2.imshow('output', drawing)

    # Keyboard OP
    k = cv2.waitKey(10)
    if k == 27:  # press ESC to exit
        camera.release()
        cv2.destroyAllWindows()
        break
    elif k == ord('b'):  # press 'b' to capture the background
        bgModel = cv2.createBackgroundSubtractorMOG2(0, bgSubThreshold)
        isBgCaptured = 1
        print('Background captured')
    elif k == ord('r'):  # press 'r' to reset the background
        bgModel = None
        triggerSwitch = False
        isBgCaptured = 0
        print ('Background reset')
    elif k == ord('n'):
        triggerSwitch = True
        print ('Trigger enabled')
