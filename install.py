import os
from itertools import izip
from push_files import popen_wait, kill_app

class PackageInstaller:
    def __init__(self, path='apk'):
        apks = os.listdir(path)
        self.package_dirs = {apk: package_path(apk) for apk in apks}
        self.__most_recently_installed = None

    def install_applications(self):
        apks = self.package_dirs.keys()
        apps = [apk.split('.apk')[0] for apk in apks]
        for apk, app in izip(apks, apps):
            apk_path = self.package_dirs.pop(apk)
            install_app(apk_path)
            self.__most_recently_installed = app
            yield app

    def uninstall(self, program):
        uninstall_app(program)
        return program

    def uninstall_most_recent(self):
        app = self.__most_recently_installed
        if app is not None:
            uninstall_app(app)
        else:
            return None

def package_path(apk, path='apk'):
    return '/'.join([os.getcwd(), path, apk])

def install_app(app_path):
    cmd = ['adb', '-e', 'install', app_path]
    return popen_wait(cmd)

def uninstall_app(app):
    kill_app(app)
    uninstall_cmd = ['adb', '-e', 'shell', 'pm', 'uninstall', app]
    return popen_wait(uninstall_cmd)
