import requests
import json
import os
import urllib2
from time import sleep
import sys

#keeping our api key and api secret off the program file so it's secure
fl = open('api.txt', 'r')
apis = fl.readlines() 

#print apis

apiKey =  apis[0].replace("\n","")
apiSec =  apis[1].replace("\n","")

#this is defined to make sure no illegal character appear in potential filenames
def correctFileName(filename):
    ret = filename.lower()
    illegalFirstChars = [' ','.','_','-']
    illegalChars = ['#','%','&','{','}','\\','<','>','*','?','/',' ','$','!',"'",'"',':','@']
    for index in range(len(filename)):
        if not filename[index] in illegalFirstChars:
            ret = filename[index:]
            break

    for char in illegalChars:
        ret = ret.replace(char,"")
    return ret


#first set of parameters passed to api call
userlistparam = {'api_key': apiKey, 'api_secret': apiSec , 'data_type': "JSON", 'page_size': 300}

#call to retrieve json object containing list of zoom users
userlistjson = requests.post('https://api.zoom.us/v1/user/list', params=userlistparam).json()
users =  userlistjson['users']

#print len(users)
#for i in range(10):

#for loop to go through each user in the list
for i in range(len(users)):
    
    #this retireves user that is currently being looked at and relevant info
    currUser = users[i]
    #if user has any recordings, this string will be the name of created directory
    username = currUser['email'][:currUser['email'].find('@')]
    #user id needed to pass to api call
    currID = currUser['id']
    
    print 'Checking User "%s" for New Recordings' % username 
    #Waits 1 Second to Prevent Too Many API Calls at once
    sleep(1)
    
    #second set of parameters passed to second api call
    videolistparams = {'api_key': apiKey, 'api_secret': apiSec, 'data_type': "JSON", 'host_id': currID, 'page_size': 300}
        
    #call to retrieve json object cotaining list of user recordings
    while True:
        videolistjson = requests.post("https://api.zoom.us/v1/recording/list", params=videolistparams).json()
        if "error" in videolistjson:
            if videolistjson["error"]["code"] == 403:
                print "Too Many API Calls at Once. Will Retry API Call in One Minute"
                sleep(60)
                continue
            else:
                sys.exit( "Unknown Error. Please run program again. If problem persists, contact justinp@sharedstudios.com")
        
        break
    currUserMeetings = videolistjson['meetings'] 
    
    #if this user has any recordings, this block of code will download them
    if (len(currUserMeetings) > 0):
        print '%d Recordings found for User "%s"; Downloading the new recording MP4 Files' % (len(currUserMeetings), username)
        #if folder for videos does not exist yet, creates a folder named after username
        if not os.path.exists("./" + username):
            os.makedirs("./" + username)

        #print username
        #print " "
        
        #for loop iterates through a meeting object, and we specfically want to contruct the meeting name
        #as well as iterate through recordings of a meeting
        for j in range(len(currUserMeetings)):
            currMeeting = currUserMeetings[j]
            #print currMeeting
            meetingName = currMeeting['topic'] + "-" + currMeeting['start_time']
            meetingName = correctFileName(meetingName)
            #print meetingName

            
            
            #a meeting might have multiple recordings, so this code block will iterate through those meetings
            for k in range(len(currMeeting['recording_files'])):
                
                currRecording = currMeeting['recording_files'][k]
                #some recording files are just audio, so we want to ensure we're only downloading the videos
                if currRecording['file_type'] != 'MP4':
                    continue

                #we finally  get to the code where we start donwloading
                filename = meetingName + '-' + str(k+1) + '.' + currRecording['file_type']
                
                #if recording file is already downloaded, this script won't download it again
                #this allows us to call this script to download new files after downloading an inital batch
                if not os.path.exists("./" + username + "/" + filename):
                    import urllib2
                    url = currRecording['download_url']
                    u = urllib2.urlopen(url)
                    f = open("./" + username + "/" + filename, 'wb')
                    #this code below just displays status of downloads within terminal (credit to stack overflow for this)
                    #if you don't need this, just remove the comments on the triple quotes
                    #'''
                    
                    meta = u.info()
                    file_size = int(meta.getheaders("Content-Length")[0])
                    print "Downloading %d.%d out of %d: %s Bytes: %s" % (j+1,k+1,len(currUserMeetings),filename, file_size)
                    
                    file_size_dl = 0
                    block_sz = 8192
                    while True:
                        buffer = u.read(block_sz)
                        if not buffer:
                            break
                        file_size_dl += len(buffer)
                        f.write(buffer)
                        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                        status = status + chr(8)*(len(status)+1)
                        print status,

                else:
                    print "Already Downloaded %d.%d out of %d" % (j+1,k+1,len(currUserMeetings))
                        #'''
                    #f.close()

                    #print filename
            if j == (len(currUserMeetings) - 1):
                print "Done Downloading User %s Recordings" % username
                print
                
        #print username

