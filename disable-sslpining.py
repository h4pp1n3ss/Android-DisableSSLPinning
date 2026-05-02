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
import logging
import textwrap
from pathlib import Path
from xml.etree import ElementTree as ET
from tools.apk import (
    apk_build,
    apk_decompile,
    install_apk
)

ANDROID_NS = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", ANDROID_NS)

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def add_network_security_config(basedir: str):
    """Create an Android network security configuration XML file.

    The file is written to ``<basedir>/res/xml/network_security_config.xml`` and
    configures the app to trust both system and user-installed certificate
    authorities.

    Args:
        basedir: Root directory of the decompiled APK project.
    """
    print("\n[*] Creating network security config...")
    xml = textwrap.dedent("""\
        <network-security-config>
            <base-config>
                <trust-anchors>
                    <!-- Trust preinstalled CAs -->
                    <certificates src="system" />
                    <!-- Additionally trust user added CAs -->
                    <certificates src="user" />
                </trust-anchors>
            </base-config>
        </network-security-config>
    """)
    out_path = Path(basedir) / "res" / "xml"
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "network_security_config.xml").write_text(xml, encoding="utf-8")
    print(f"[+] Network security config created: {out_path / 'network_security_config.xml'}")


def edit_manifest(filepath: str):
    """Update the Android manifest to reference the network security config.

    Args:
        filepath: Path to the decompiled AndroidManifest.xml file.

    Raises:
        ValueError: If no <application> element is found in the manifest.
    """
    print("[*] Editing AndroidManifest.xml...")
    tree = ET.parse(filepath)
    root = tree.getroot()
    app = root.find("application")
    if app is None:
        raise ValueError("AndroidManifest.xml has no <application> element")

    app.set(f"{{{ANDROID_NS}}}networkSecurityConfig", "@xml/network_security_config")
    tree.write(filepath, encoding="utf-8", xml_declaration=True)
    print(f"[+] Manifest updated with network security config")


def do_jarsigner(apk_path: str, keystore: str) -> None:
    """Sign an APK using jarsigner with the provided keystore."""
    print(f"\n[*] Signing APK with jarsigner...")
    command = [
        "jarsigner",
        "-verbose",
        "-keystore",
        keystore,
        "-storepass",
        "password",
        "-keypass",
        "password",
        apk_path,
        "android",
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0 or "jar signed." not in result.stdout:
        raise RuntimeError(
            "jarsigner failed:\n{}\n{}".format(result.stdout.strip(), result.stderr.strip())
        )

    print(f"[+] APK signed successfully: {apk_path}")


def generate_keystore(keystore_path: str, alias: str = "android") -> None:
    """Generate a keystore for signing APKs using keytool."""
    keystore_path = Path(keystore_path)
    if keystore_path.exists():
        print(f"[*] Keystore already exists: {keystore_path}")
        return

    print(f"\n[*] Generating keystore: {keystore_path}")
    command = [
        "keytool",
        "-genkey",
        "-v",
        "-keystore",
        str(keystore_path),
        "-keyalg",
        "RSA",
        "-keysize",
        "2048",
        "-validity",
        "10000",
        "-alias",
        alias,
        "-storepass",
        "password",
        "-keypass",
        "password",
        "-dname",
        "CN=Android,O=Development,C=US",
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "keytool failed:\n{}\n{}".format(result.stdout.strip(), result.stderr.strip())
        )

    print(f"[+] Keystore generated: {keystore_path}")


def main(apk_path: str, keystore: str = None) -> None:
    """Run the full SSL pinning bypass workflow for an APK.

    This includes decompiling the APK, injecting a network security config,
    rebuilding the APK, signing it, and installing it via adb.

    Args:
        apk_path: Path to the input APK file.
        keystore: Optional keystore path. If omitted, a default
            ``android_debug.keystore`` is generated in the APK directory.

    Raises:
        FileNotFoundError: If the input APK or rebuilt APK cannot be found.
        RuntimeError: If rebuild or signing fails.
    """
    print("\n" + "="*60)
    print("[*] Starting SSL Pinning Bypass Process")
    print("="*60)

    apk_path = Path(apk_path)
    if not apk_path.exists():
        raise FileNotFoundError(f"APK not found: {apk_path}")
    print(f"[+] APK found: {apk_path}")

    # Set default keystore path if not provided
    if keystore is None:
        keystore = str(apk_path.parent / "android_debug.keystore")
    
    keystore_path = Path(keystore)
    if not keystore_path.exists():
        print(f"[*] Keystore not found; generating...")
        generate_keystore(str(keystore_path))
    else:
        print(f"[+] Keystore found: {keystore_path}")

    print(f"\n[*] Decompiling APK...")
    apk_decompile(str(apk_path))
    print(f"[+] APK decompiled successfully")

    project_dir = apk_path.with_suffix("").with_name(apk_path.stem + "_out")
    add_network_security_config(str(project_dir))

    manifest_filepath = project_dir / "AndroidManifest.xml"
    edit_manifest(str(manifest_filepath))

    print(f"\n[*] Rebuilding APK...")
    if not apk_build(str(project_dir)):
        raise RuntimeError("APK rebuild failed")
    print(f"[+] APK rebuilt successfully")

    dist_dir = project_dir / "dist"
    apk_files = list(dist_dir.glob("*.apk"))
    if not apk_files:
        raise FileNotFoundError(f"No rebuilt APK found in: {dist_dir}")

    new_apk = str(apk_files[0])
    print(f"[+] New APK found: {new_apk}")
    do_jarsigner(new_apk, keystore)
    install_apk(new_apk)
    
    print(f"\n" + "="*60)
    print("[+] SSL Pinning Bypass Completed Successfully!")
    print("="*60 + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Disable SSL Pinning in Android APKs")
    parser.add_argument('-apk', required=True, help='APK input file')
    parser.add_argument('-key', required=False, default=None, help='Keystore file (optional, auto-generated if not provided)')
    args = parser.parse_args()
    try:
        main(args.apk, args.key)
    except Exception as e:
        print(f"\n[-] Error: {e}\n")
        sys.exit(1)
