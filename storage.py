import os
import sys

DOWNLOAD_FOLDER = 'Baixador'

def is_android():
    return sys.platform == 'android'


def get_videos_dir():
    if is_android():
        try:
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            path = Environment.getExternalStoragePublicDirectory(
                Environment.DIRECTORY_MOVIES
            ).getAbsolutePath()
            return os.path.join(path, DOWNLOAD_FOLDER)
        except Exception:
            pass
    return os.path.join(os.path.expanduser('~'), 'Videos', DOWNLOAD_FOLDER)


def get_audio_dir():
    if is_android():
        try:
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            path = Environment.getExternalStoragePublicDirectory(
                Environment.DIRECTORY_MUSIC
            ).getAbsolutePath()
            return os.path.join(path, DOWNLOAD_FOLDER)
        except Exception:
            pass
    return os.path.join(os.path.expanduser('~'), 'Music', DOWNLOAD_FOLDER)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def scan_file(filepath):
    if not is_android():
        return
    try:
        from jnius import autoclass
        Intent = autoclass('android.content.Intent')
        File = autoclass('java.io.File')
        Uri = autoclass('android.net.Uri')

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity

        intent = Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE)
        file = File(filepath)
        uri = Uri.fromFile(file)
        intent.setData(uri)
        activity.sendBroadcast(intent)
    except Exception:
        pass


def get_download_path(is_audio=False):
    base = get_audio_dir() if is_audio else get_videos_dir()
    return ensure_dir(base)
