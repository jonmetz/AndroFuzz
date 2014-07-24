import os
import subprocess
import json
import re
import pexpect
from install import PackageInstaller

class AndroidLogger:
    def __init__(self):
        self.logs = {'segfaults':{}}
        log_cmd = 'adb -e logcat ActivityManager:W \*:S'
        self.child = pexpect.spawn(log_cmd)
        try:
            self.child.read_nonblocking(timeout=0)
        except pexpect.TIMEOUT:
            pass

    def __read(self):
        try:
            self.child.expect('\r\r\n', timeout=5)
            log_output = self.child.before
        except pexpect.TIMEOUT:
            log_output = None
        return log_output

    def add_app(self, app):
        self.logs[app] = {}
        return self.logs[app]

    def get_logs(self):
        return self.logs

    def check_segfault(self, log_lines, program):
        regex = re.compile('F/libc    \(  \d{2,4}\): Fatal signal 11 .*terminated by signal \(11\)', re.Unicode, re.DOTALL)
        match = regex.search(regex, '\n'.join(log_lines))
        if match:
            self.logs['segfaults'] = {program: log_lines}
            return
        else:
            return

    def add_logs(self, app, file):
        log_lines = self._get_logs(app, file)
        self.check_segfault(log_lines)
        self.logs[app][file] = log_lines
        return self.logs[app][file]

    def _get_logs(self, app, file):
        logs = []
        while True:
            log_line = self.__read()
            if not log_line:
                break
            logs.append(log_line)
        return logs

def push_files(remote_path='/mnt/sdcard/Download', local_path='pdfs', adb='adb'):
    cmd = [adb, 'push', local_path, remote_path]
    popen_wait(cmd)
    files=os.listdir(local_path)
    remote_files = [remote_path + '/' + file for file in files]
    return remote_files

def stop_app(application, process=None):
    if process:
        process.kill()
    home_screen() # Can't kill apps in foreground
    stop_cmd = ['adb', 'shell', 'am', 'force-stop', application]
    return popen_wait(stop_cmd)

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
    for application in applications:
        logger.add_app(application)
        stop_app(application)
        for file in files:
            p = open_file(file, intent, mimetype)
            logger.add_logs(application, file)
            stop_app(application, process=p)
        package_installer.uninstall_most_recent()
    return logger.get_logs()

def home_screen():
    return send_key_event('3')

def send_key_event(event_num):
    cmd = ['adb', 'shell', 'input', 'keyevent', event_num]
    return popen_wait(cmd)

def power_button():
    return send_key_event('26')

def kill_app(app):
    stop_app(app)
    kill_cmd = ['adb', 'shell', 'am', 'kill', app]
    return popen_wait(kill_cmd)

def adb_cmd(cmd):
    return ['adb', '-e'] + cmd

def adb_shell_cmd(cmd):
    return adb_cmd(['shell']) + cmd

def cleanup(files):
    return popen_wait(adb_shell_cmd(['rm'] + files))

def main():
    files = push_files()
    logs = open_files(files)
    print json.dumps(logs)
    cleanup(files)

if __name__=='__main__':
    main()
