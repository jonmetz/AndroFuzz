import os
from push_files import popen_wait

class PackageInstaller:
    def __init__(self, path='apk'):
        apks = os.listdir(directory)
        self.package_dirs = {apk: package_path(apk) for apk in apks}

    def install_applications(self):
        apks = self.package_dirs.keys()
        for apk in apks:
            apk_path = self.package_dirs.pop(apk)
            install_package(apk_path)
            yield apk


def package_path(apk, directory='apk'):
    return '/'.join([os.getcwd(), directory, apk])

def install_package(package_path):
    cmd = ['adb', '-e', 'install', package_path]
    return popen_wait(cmd)
