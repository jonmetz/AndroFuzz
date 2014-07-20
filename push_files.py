import os
import subprocess
from time import sleep
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

def push_files(remote_path='/mnt/sdcard/Download', local_path='pdfs', adb='adb'):
    args = [adb, 'push', local_path, remote_path]
    process = subprocess.Popen(args)
    result = process.wait()
    files=os.listdir(local_path)
    remote_files = [remote_path + '/' + file for file in files]
    return remote_files
#  START {act=android.intent.action.VIEW dat=file:///mnt/sdcard/Download/sample_pdf-0.pdf typ=application/pdf flg=0x3000000 cmp=com.adobe.reader/.AdobeReader u=0} from pid 149
# START {act=android.intent.action.VIEW dat=file:///mnt/sdcard/Download/sample_pdf-0.pdf typ=application/pdf cmp=com.adobe.reader/.AdobeReader u=0}

def open_files(device, files, applications=os.listdir('apk')):
    # adb shell am start -a android.intent.action.VIEW -d file:///mnt/sdcard/Download/sample_pdf-0.pdf -t application/pdf
    applications = [app.split('.apk')[0] for app in applications]
    intent = 'android.intent.action.VIEW'
    mimetype = 'application/pdf'
    files = [files[0], files[1]]
    for application in applications:
        kill_cmd = ['adb', 'shell', 'am', 'force-stop', application]
        for file in files:
            p = subprocess.Popen(kill_cmd)
            print 'stopped'
            p.wait()
            print "start"
            data = 'file://' + file
            open_cmd = ['adb', 'shell', 'am', 'start', '-W', '-a', intent, '-d', data, '-t', mimetype]
            p = subprocess.Popen(open_cmd)
            p.wait()
            print "done"


def main():
    timeout = 10000
    device = MonkeyRunner.waitForConnection(timeout)
    files = push_files()
    open_files(device, files)



if __name__=='__main__':
    main()
