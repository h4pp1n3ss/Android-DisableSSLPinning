# Android-DisableSSLPinning

A small Python tool that disables Android SSL pinning by injecting a `network_security_config.xml` into a decompiled APK project, updating the app manifest to use it, rebuilding the APK, signing the rebuilt APK, and installing it on a connected device.

## What it does

- Decompiles the input APK using `apktool`
- Adds a network security config that trusts both system and user certificate authorities
- Updates `AndroidManifest.xml` to reference the injected network security config
- Rebuilds the APK with `apktool`
- Signs the rebuilt APK with `jarsigner`
- Installs the resulting APK to a connected Android device via `adb`

## Requirements

- Python 3
- `apktool` installed and available on `PATH`
- `adb` installed and available on `PATH`
- `jarsigner` and `keytool` available in the Java JDK on `PATH`

## Usage

Run the script from the repository root:

```bash
python disable-sslpining.py -apk path/to/app.apk
```

If you want to provide a custom keystore file:

```bash
python disable-sslpining.py -apk path/to/app.apk -key path/to/keystore.jks
```

If the keystore argument is omitted, the script will automatically generate a default `android_debug.keystore` next to the input APK.

## Notes

- The repository also contains `tools/apk.py`, which provides helper functions for decompiling, rebuilding, and installing APKs.
- Generated output and APK build artifacts are not part of the source; use `.gitignore` to keep them out of version control.

