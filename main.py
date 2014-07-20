import os
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

def get_MainActivity(package_name):
    return package_name + 'MainActivity'

def install_package(package_path, device):
    if device.installPackage(package_path):
        return True
    else:
        return False

def install_packages(device, directory='apk'):
    apks = os.listdir(directory)
    installation_results = []
    for apk in apks:
        package_path = os.getcwd() + '/' + directory + '/' + apk
        print package_path
        result = install_package(package_path, device)
        installation_results.append(result)
    return installation_results

def main():
    timeout = 10000
    device = MonkeyRunner.waitForConnection(timeout)
    directory = 'apk'
    packages = install_packages(device, directory=directory)
    print packages


if __name__=='__main__':
    main()
