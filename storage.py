import os
import sys

def is_android():
    return sys.platform == 'android'


def get_app_storage_dir(subdir=''):
    if is_android():
        try:
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            dir_type = Environment.DIRECTORY_MOVIES if 'audio' not in subdir else Environment.DIRECTORY_MUSIC
            base = activity.getExternalFilesDir(dir_type).getAbsolutePath()
        except Exception:
            base = os.path.join(os.path.expanduser('~'), subdir or 'Downloads')
    else:
        base = os.path.join(os.path.expanduser('~'), subdir or 'Downloads')
    path = os.path.join(base, 'Baixador')
    os.makedirs(path, exist_ok=True)
    return path


def get_download_path(is_audio=False):
    return get_app_storage_dir('Music' if is_audio else 'Movies')


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
        intent.setData(Uri.fromFile(File(filepath)))
        activity.sendBroadcast(intent)
    except Exception:
        pass
