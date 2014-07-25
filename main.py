import os
import subprocess
import json
import re
import pexpect
from install import PackageInstaller

class AndroidLogger:
    '''
    Can collect logs about apps from an android device/emulator
    '''
    def __init__(self, logfile_name='logs'):
        self.logs = {}
        log_cmd = 'adb -e logcat'
        self.logfile = fp=(open("logs", "a"))
        self.child = pexpect.spawn(log_cmd)
        try:
            self.child.read_nonblocking(timeout=0)
        except pexpect.TIMEOUT:
            pass

    def __read(self):
        '''
        Read logs from adb
        '''
        try:
            self.child.expect('\r\r\n', timeout=5)
            log_output = self.child.before
        except pexpect.TIMEOUT:
            log_output = None
        return log_output

    def close_logfile(self):
        self.logfile.close()

    def append_app_logs(self, program):
        '''
        Write logs of currently tested app to disk and remove it from
        the logs attribute
        '''
        logs_dict = self.pop_program_logs(program)
        logs_dict['program_name'] = program
        self.logfile.write(unicode(logs_dict))

    def add_app(self, app):
        '''
        Allows for the collection of log data from an app
        '''
        self.logs[app] = {}
        return self.logs[app]

    def get_logs(self):
        '''
        Returns the adb logs created during the fuzzing of an app
        '''
        return self.logs

    def pop_program_logs(self, program):
        '''
        Returns the logs of an app and removes them from
        this objects logs dictionary
        '''
        return self.logs.pop(program, {})

    # def check_segfault(self, log_lines, program, input_name, input_type="file"):
    #     # regex = re.compile('F/libc    \(  \d{2,4}\): Fatal signal 11 .*terminated by signal \(11\)', re.DOTALL)
    #     import pdb; pdb.set_trace()
    #     regex = 'Fatal signal 11(.|\n)*Process \d{2,4} terminated by signal '
    #     logs = '\n'.join(log_lines)
    #     match = re.search(regex, logs)
    #     if match:
    #         self.logs[program]['segfaults'] = {'logs': log_lines, input_type: input_name}
    #         return
    #     else:
    #         return

    def add_logs(self, app, file):
        '''
        Add the each line of logs to the log dictionary of app
        '''
        log_lines = self._get_logs(app, file)
        # self.check_segfault(log_lines, app, file)
        self.logs[app][file] = log_lines
        return self.logs[app][file]

    def _get_logs(self, app, file):
        '''
        Keep getting logs from the android device as long as they are being produced
        '''
        logs = []
        while True:
            log_line = self.__read()
            if not log_line:
                break
            logs.append(log_line)
        return logs

def push_files(remote_path='/mnt/sdcard/Download', local_path='pdfs', adb='adb'):
    '''
    Push files in the local_path directory to the remote_path directory on the android device
    '''
    cmd = [adb, 'push', local_path, remote_path]
    popen_wait(cmd)
    files=os.listdir(local_path)
    remote_files = [remote_path + '/' + file for file in files]
    return remote_files

def stop_app(application, process=None):
    '''
    Start running an app
    '''
    if process:
        process.kill()
    home_screen() # Can't kill apps in foreground
    stop_cmd = ['adb', 'shell', 'am', 'force-stop', application]
    return popen_wait(stop_cmd)

def popen_wait(cmd, message=None):
    '''
    Start a process using a Popen event and wait for it to terminate
    '''
    p = subprocess.Popen(cmd)
    ret_val = p.wait()
    if message:
        print(message)
    return ret_val

def open_file(file, intent, mimetype):
    '''
    Create a Popen object that opens a file with an app and returns the Popen object
    '''
    data = 'file://' + file
    open_cmd = ['adb', 'shell', 'am', 'start', '-W', '-a', intent, '-d', data, '-t', mimetype]
    p = subprocess.Popen(open_cmd)
    return p

def open_files(files, intent='android.intent.action.VIEW', mimetype='application/pdf'):
    logger = AndroidLogger()
    package_installer = PackageInstaller()
    applications = package_installer.install_applications()[:1]
    for application in applications:
        logger.add_app(application)
        stop_app(application)
        for file in files:
            p = open_file(file, intent, mimetype)
            logger.add_logs(application, file)
            stop_app(application, process=p)
        package_installer.uninstall_most_recent()
        logger.append_app_logs(application)
    return logger.get_logs()

def home_screen():
    '''
    Send the press home button event to the android device
    '''
    return send_key_event('3')

def send_key_event(event_num):
    '''
    Send an arbitrary key event to an android device
    '''
    cmd = ['adb', 'shell', 'input', 'keyevent', event_num]
    return popen_wait(cmd)

def power_button():
    '''
    Send the press power button event to the android device
    '''
    return send_key_event('26')

def kill_app(app):
    '''
    Kills an app process
    '''
    stop_app(app)
    kill_cmd = ['adb', 'shell', 'am', 'kill', app]
    return popen_wait(kill_cmd)

def adb_cmd(cmd):
    '''
    run the adb cmd using adb on an android device
    '''
    return ['adb'] + cmd

def adb_shell_cmd(cmd):
    '''
    run the shell command on the android device
    '''
    return adb_cmd(['shell']) + cmd

def cleanup(files):
    '''
    Remove the files from the android device
    '''
    return popen_wait(adb_shell_cmd(['rm'] + files))

def fuzz():
    '''
    Push the files to the android device, install the apps and start fuzzing
    '''
    files = push_files()
    logs = open_files(files)
    return logs

def main():
    logs = fuzz()
    fp = open('logs', 'w+')
    logs_json = json.dumps(logs)
    fp.write(logs_json)
    fp.close()
    cleanup(files)

if __name__=='__main__':
    main()
