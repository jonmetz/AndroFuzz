import os
import subprocess

def main():
    remote_path = '/mnt/sdcard/Download'
    local_path = 'pdfs'
    args = ['adb', 'push', local_path, remote_path]
    process = subprocess.Popen(args)
    if process.wait() is not 0:
        print 'Fail'
    else:
        print 'Success'

if __name__=='__main__':
    main()
