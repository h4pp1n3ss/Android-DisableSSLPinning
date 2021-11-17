#!/usr/bin/env python3

"""
    @Author: me
    @Description: SSL-Unpining via network configuration (Trust CA Users/Systems)

"""

import subprocess
import sys
import shutil
import os
import argparse


def log(message):
    print("[*] " +  message)


def apk_decompile(filename):
    """ APK decompile to create folder """
    output = subprocess.getoutput("apktool d {} -o {}".format(filename, filename.replace(".apk", "_out")))
    if 'Exception in' in output:
        log("Some error occur")
        log(output)
        try:
            os.rmdir(filename.replace(".apk", "_out"))
        except:
            pass
        return False
    else:
        return True


def apk_build(filepath):
    """ APK build to create APK file """
    output = subprocess.getoutput("apktool b {} --use-aapt2".format(filepath))
    try:
        os.listdir(filepath + os.sep + 'dist')
    except FileNotFoundError:
        log("An error occur when rebuild the APK")
        log(output)
        return False
    return True


def add_network_security_config(basedir):
    data = '''\
<network-security-config> 
    <base-config> 
        <trust-anchors> 
            <!-- Trust preinstalled CAs --> 
            <certificates src="system" /> 
            <!-- Additionally trust user added CAs --> 
            <certificates src="user" /> 
        </trust-anchors> 
    </base-config> 
</network-security-config>'''
    with open(os.path.join(basedir, 'res', 'xml', 'network_security_config.xml'), 'w') as fh:
        fh.write(data)


def edit_manifest(filepath):
    with open(filepath) as fh:
        contents = fh.read()
    new_contents = contents.replace("<application ", '<application android:networkSecurityConfig="@xml/network_security_config" ')
    with open(filepath, 'w') as fh:
        fh.write(new_contents)


def do_jarsigner(filepath, keystore):
    """Uses APKTool to create a new APK"""
    output = subprocess.getoutput("jarsigner -verbose -keystore {} -storepass password -keypass password {} android".format(keystore, filepath))
    if 'jar signed.' not in output:
        print("[-] An error occurred during jarsigner: \n{}".format(output))
    else:
        print("[*] File located in: " +  filepath)
        print("[*] Signed!")


def install_apk(filepath):
    """ Use to install the APK file  """
    output = subprocess.getoutput("adb install {}".format(filepath))
    if 'Exception in' in output:
        log("Some error occur")
    else:
        log("APK installed")


def main():
    # Decompile the app with APKTool
    log("Decompiling {}...".format(file))
    apk_decompile(file)
    project_dir = file.replace('.apk', '_out')
    add_network_security_config(project_dir)
    manifest_filepath = project_dir + os.sep + "AndroidManifest.xml"
    log(manifest_filepath)
    edit_manifest(manifest_filepath)
    log('Rebuilding the APK...')
    
    if not apk_build(project_dir):
        exit()
    new_apk = os.path.join(project_dir, 'dist', os.listdir(project_dir + os.sep + 'dist')[0])
    do_jarsigner(new_apk, keystore)
    install_apk(new_apk)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Some description")
    parser.add_argument('-apk', help='APK input file')
    parser.add_argument('-key', help='Key store file')
    args = parser.parse_args()
    file = args.apk
    keystore = args.key
    main()
