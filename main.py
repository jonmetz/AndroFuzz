import os
import subprocess
import json
import re
import pexpect
import glob
from install import PackageInstaller

class AndroidLogger:
    '''
    Can collect logs about apps from an android device/emulator
    '''
    def __init__(self, log_dir='logs'):
        self.logs = {}
        log_cmd = 'adb -e logcat'
        self.logfile = None
        self.add_log_dir(log_dir)
        self.child = pexpect.spawn(log_cmd)
        try:
            self.child.read_nonblocking(timeout=0)
        except pexpect.TIMEOUT:
            pass

    def add_log_dir(self, log_dir): # Bug, what if file with name log_dir exists?
        if log_dir[-1] != '/':
            log_dir += '/'
        if os.path.isdir(log_dir):
            self.log_dir = log_dir
            return log_dir
        else:
            os.makedirs(log_dir)
            return self.add_log_dir(log_dir)

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

    def write_app_logs(self, program):
        '''
        Write logs of currently tested app to disk and remove it from
        the logs attribute
        '''
        # logs_dict = self.pop_program_logs(program)
        # # self.logfile.write(json.dumps(logs_dict))
        # if check_segfault(logs_dict):
        #     self.logfile.write(program +'\n\n\n')
        #     self.logfile.write(unicode(logs_dict))
        #     self.logfile.close()
        return self.logfile

    def add_app(self, app):
        '''
        Allows for the collection of log data from an app
        '''
        if self.logfile:
            self.logfile.close()
            self.logfile = None
        self.logs[app] = {}
        log_path = self.log_dir + '/' + app + '.log'
        self.logfile = open(log_path, 'a+')
        return self.logs[app], self

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

    def add_logs(self, app, file):
        '''
        Add the each line of logs to the log dictionary of app
        '''
        log_lines = self._get_logs(app, file)
        # self.check_segfault(log_lines, app, file)
        self.logs[app][file] = log_lines
        # file_log = {file: '\n'.join(log_lines)}
        if check_segfault(self.logs[app]):
            print "segf"
            self.logfile.write(file + '\t' + app + '\n')
            self.logfile.flush()
            self.logs[app][file] = ''
            # self.logfile.write(unicode(self.logs[app]))
        return self.logs[app][file]

    def _get_logs(self, app, file):
        '''
        Keep getting logs from the android device as long as they are being produced
        '''
        logs = ''
        while True:
            log_line = self.__read()
            if not log_line:
                break
            logs = '\n'.join([logs, log_line])
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

def open_files(files, intent='android.intent.action.VIEW', mimetype='application/pdf', log_dir='logs'):
    logger = AndroidLogger(log_dir)
    package_installer = PackageInstaller()
    applications = package_installer.install_applications()
    app_logfiles = []
    for application in applications:
        logger.add_app(application)
        stop_app(application)
        for file in files:
            p = open_file(file, intent, mimetype)
            logger.add_logs(application, file)
            stop_app(application, process=p)
        application = package_installer.uninstall(application)
        # app_logfiles.append(logger.write_app_logs(application))
    return app_logfiles

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

def check_segfault(log_dict):
    # regex = r'F/libc    \(  \d*\): Fatal signal \d{2,8} .*terminated by signal \(11\)'# r'Fatal signal 11(.|\n)*Process \d{2,8} terminated by signal'
    # regex = ur'F/libc    \(  \d*\): Fatal signal \d{2,8} .*terminated by signal \(11\)'
    # match = re.search(regex, log)
    # if match:
    #     return match.group()
    # else:
    #     return None
    segfault_caused = False
    files = log_dict.keys()
    for file in files:
        if 'Fatal signal 11' in log_dict[file]:
            print "Segfault caused by " + file
            segfault_caused = True
    return segfault_caused


def fuzz(log_dir='logs'):
    '''
    Push the files to the android device, install the apps and start fuzzing
    '''
    files = push_files()
    logs = open_files(files, log_dir=log_dir)
    return logs, files

# def examine_logs(log_dir):
#     if log_dir[-1] != '/': # should make a decorator
#         log_dir += '/'
#     logs = glob.glob(log_dir + '*.log')
#     for log_file in logs:
#         log_file_fp = open(log_file)
#         log_file_contents = log_file_fp.read()
#         log_file_fp.close()
#         check_segfault(json.loads(log_file_contents))
#         # segfault_logs = check_segfault(log_file_contents)
#         # if segfault_logs:
#         #     segfault_logs_fp = json.loads(open(logfile + '.segfault', 'w+'))
#         #     segfault_logs_fp.write(segfault_logs)


def main():
    log_dir = 'logs'
    _, fuzz_files = fuzz(log_dir=log_dir)
    print "Done Fuzzing"
    # examine_logs(log_dir)
    print "Done logging"
    cleanup(fuzz_files)

if __name__=='__main__':
    main()
