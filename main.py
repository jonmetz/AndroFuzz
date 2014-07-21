import os
import subprocess
import json
import pexpect
from install import PackageInstaller

class AndroidLogger:
    def __init__(self):
        self.logs = {}
        log_cmd = 'adb -e logcat ActivityManager:W \*:S'
        self.child = pexpect.spawn(log_cmd)
        try:
            self.child.read_nonblocking(timeout=0)
        except pexpect.TIMEOUT:
            pass

    def __read(self):
        try:
            self.child.expect('\r\r\n', timeout=3)
            log_output = self.child.before
        except pexpect.TIMEOUT:
            log_output = None
        return log_output

    def add_app(self, app):
        self.logs[app] = {}

    def get_logs(self):
        return self.logs

    def add_logs(self, app, file):
        self.logs[app][file] = self._get_logs(app, file)
        return self.logs[app][file]

    def _get_logs(self, app, file):
        logs = []
        while True:
            log_line = self.__read()
            if not log_line:
                break
            # elif app in log_line:
            logs.append(log_line)
        return logs

def push_files(remote_path='/mnt/sdcard/Download', local_path='pdfs', adb='adb'):
    cmd = [adb, 'push', local_path, remote_path]
    popen_wait(cmd)
    files=os.listdir(local_path)
    remote_files = [remote_path + '/' + file for file in files]
    return remote_files

def kill_app(application, process=None):
    if process:
        process.kill()
    else:
        kill_cmd = ['adb', 'shell', 'am', 'force-stop', application]
        return popen_wait(kill_cmd)

def popen_wait(cmd, message=None):
    p = subprocess.Popen(cmd)
    ret_val = p.wait()
    if message:
        print(message)
    return ret_val

def open_file(file, intent, mimetype):
    data = 'file://' + file
    open_cmd = ['adb', 'shell', 'am', 'start', '-W', '-a', intent, '-d', data, '-t', mimetype]
    p = subprocess.Popen(open_cmd)
    return p

def open_files(files, intent='android.intent.action.VIEW', mimetype='application/pdf'):
    logger = AndroidLogger()
    package_installer = PackageInstaller()
    applications = package_installer.install_applications()
    files = [files[0], files[1]]
    for application in applications:
        logger.add_app(application)
        kill_app(application)
        for file in files:
            p = open_file(file, intent, mimetype)
            logger.add_logs(application, file)
            kill_app(application, process=p)
    return logger.get_logs()

def main():
    files = push_files()
    logs = open_files(files)
    print json.dumps(logs)


if __name__=='__main__':
    main()
