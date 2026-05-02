import subprocess
import logging
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


def install_apk(filepath: str) -> None:
    """Install the APK file using adb.

    Args:
        filepath: Path to the APK file to install.

    Raises:
        RuntimeError: If adb install fails.
    """
    apk_path = Path(filepath)
    command = ["adb", "install", str(apk_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("ADB install failed: %s", result.stderr.strip())
        raise RuntimeError(f"Failed to install APK: {apk_path}")
    logger.info("APK installed: %s", apk_path)


def apk_decompile(filename: str) -> bool:
    """Decompile an APK using apktool into the output folder.

    Args:
        filename: Path to the input APK file.

    Returns:
        True if decompile succeeded, False otherwise.
    """
    apk_path = Path(filename)
    output_dir = apk_path.with_name(apk_path.stem + "_out")
    logger.info("Decompiling APK %s to %s", apk_path, output_dir)
    command = ["apktool", "d", str(apk_path), "-o", str(output_dir)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("APKTool decompile failed: %s", result.stderr.strip() or result.stdout.strip())
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
        return False
    return True


def apk_build(filepath: str) -> bool:
    """Build an APK from an apktool project.

    Args:
        filepath: Path to the decompiled apktool project directory.

    Returns:
        True if the build succeeded and the dist directory exists.
    """
    project_dir = Path(filepath)
    logger.info("Building APK from project: %s", project_dir)
    command = ["apktool", "b", str(project_dir), "--use-aapt2"]
    result = subprocess.run(command, capture_output=True, text=True)
    dist_dir = project_dir / "dist"
    if result.returncode != 0 or not dist_dir.exists():
        logger.error("APKTool build failed: %s", result.stderr.strip() or result.stdout.strip())
        return False
    return True