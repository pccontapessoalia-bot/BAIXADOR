import os
import threading

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.utils import rgba
from kivy.graphics import Color, Rectangle

from downloader import Downloader
from storage import get_download_path, scan_file

try:
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.READ_MEDIA_VIDEO,
        Permission.READ_MEDIA_AUDIO,
    ])
except ImportError:
    pass

Window.clearcolor = rgba('#14141E')


class RoundedInput(TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_color', rgba('#262630'))
        kwargs.setdefault('foreground_color', (1, 1, 1, 1))
        kwargs.setdefault('hint_text_color', rgba('#666680'))
        kwargs.setdefault('padding', [15, 15])
        kwargs.setdefault('font_size', 14)
        kwargs.setdefault('cursor_color', (1, 1, 1, 1))
        kwargs.setdefault('border', [12, 12, 12, 12])
        super().__init__(**kwargs)


class RoundedButton(Button):
    def __init__(self, **kwargs):
        bg = rgba('#3366FF')
        bg_down = rgba('#2952CC')
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_down', '')
        kwargs.setdefault('background_color', bg)
        kwargs.setdefault('font_size', 17)
        kwargs.setdefault('bold', True)
        kwargs.setdefault('color', (1, 1, 1, 1))
        kwargs.setdefault('border', [12, 12, 12, 12])
        super().__init__(**kwargs)
        self._bg = bg
        self._bg_down = bg_down

    def on_state(self, *args):
        if self.state == 'down':
            self.background_color = self._bg_down
        else:
            self.background_color = self._bg


class Chip(ToggleButton):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_down', '')
        kwargs.setdefault('color', rgba('#AAAABB'))
        kwargs.setdefault('font_size', 13)
        kwargs.setdefault('size_hint_x', None)
        kwargs.setdefault('width', 75)
        kwargs.setdefault('border', [20, 20, 20, 20])
        super().__init__(**kwargs)

    def on_state(self, *args):
        if self.state == 'down':
            self.background_color = rgba('#3366FF')
            self.color = (1, 1, 1, 1)
        else:
            self.background_color = rgba('#262630')
            self.color = rgba('#AAAABB')


class LogArea(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log_label = Label(
            text='', size_hint_y=None, halign='left', valign='top',
            text_size=(Window.width * 0.85, None), font_size=12,
            color=(0.7, 0.7, 0.7, 1)
        )
        self.add_widget(self.log_label)

    @mainthread
    def append(self, text):
        current = self.log_label.text
        new = f"{current}\n{text}" if current else text
        self.log_label.text = new
        self.log_label.texture_update()
        self.log_label.height = self.log_label.texture_size[1]
        self.scroll_to(self.log_label)


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=0, padding=0, **kwargs)
        self.download_dir = os.path.expanduser('~')
        self.downloader = Downloader(
            progress_callback=self.on_progress,
            status_callback=self.on_status
        )
        self._build_ui()

    def _build_ui(self):
        header = BoxLayout(size_hint_y=0.1, padding=[20, 10])
        with header.canvas.before:
            Color(0.12, 0.12, 0.16, 1)
            self.header_rect = Rectangle(size=header.size, pos=header.pos)
        header.bind(pos=self._update_header, size=self._update_header)
        hlabel = Label(text='Baixador de Links', font_size=20, bold=True, color=(1, 1, 1, 1))
        header.add_widget(hlabel)
        self.add_widget(header)

        body = BoxLayout(orientation='vertical', spacing=15, padding=[20, 15])
        self.add_widget(body)

        body.add_widget(Label(
            text='Cole o link do video', font_size=14,
            color=(0.6, 0.6, 0.7, 1), size_hint_y=None, height=20, halign='left'
        ))

        self.url_input = RoundedInput(
            hint_text='https://youtube.com/...', multiline=False,
            size_hint_y=None, height=50
        )
        body.add_widget(self.url_input)

        self.download_btn = RoundedButton(text='Baixar', size_hint_y=None, height=52)
        self.download_btn.bind(on_press=self.start_download)
        body.add_widget(self.download_btn)

        body.add_widget(Label(
            text='Formato', font_size=13,
            color=(0.6, 0.6, 0.7, 1), size_hint_y=None, height=18, halign='left'
        ))

        chips = BoxLayout(size_hint_y=None, height=44, spacing=8)
        self.format_chips = {}
        for fmt in ['MP4', 'MP3']:
            chip = Chip(text=fmt, group='format')
            chip.bind(on_press=self.on_format_chip)
            chips.add_widget(chip)
            self.format_chips[fmt] = chip
        self.format_chips['MP4'].state = 'down'
        self.format_chips['MP4'].on_state()
        self.format_chips['MP3'].on_state()
        chips.add_widget(Label(size_hint_x=1))
        body.add_widget(chips)

        self.quality_box = BoxLayout(size_hint_y=None, height=40, spacing=6)
        self._build_quality_chips(is_audio=False)
        body.add_widget(self.quality_box)

        body.add_widget(BoxLayout(size_hint_y=0.02))

        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=6)
        body.add_widget(self.progress_bar)

        self.status_label = Label(
            text='Pronto para baixar', font_size=12,
            color=(0.5, 0.5, 0.6, 1), size_hint_y=None, height=18
        )
        body.add_widget(self.status_label)

        self.log_area = LogArea(size_hint_y=0.25)
        body.add_widget(self.log_area)

    def _update_header(self, *args):
        if hasattr(self, 'header_rect'):
            p = self.children[-1]
            self.header_rect.size = p.size
            self.header_rect.pos = p.pos

    def _build_quality_chips(self, is_audio=False):
        self.quality_box.clear_widgets()
        self.quality_chips = {}
        if is_audio:
            items = ['320kbps', '192kbps', '128kbps']
            default = '192kbps'
        else:
            items = ['Melhor', '1080p', '720p', '480p']
            default = 'Melhor'
        for q in items:
            chip = Chip(text=q, group='quality')
            chip.bind(on_press=self.on_quality_chip)
            self.quality_box.add_widget(chip)
            self.quality_chips[q] = chip
        self.quality_chips[default].state = 'down'
        for chip in self.quality_chips.values():
            chip.on_state()
        self.quality_box.add_widget(Label(size_hint_x=1))

    def get_format_string(self):
        quality_map = {'Melhor': 'best', '1080p': '1080p', '720p': '720p', '480p': '480p'}
        fmt = 'MP3' if self.format_chips['MP3'].state == 'down' else 'MP4'
        if fmt == 'MP3':
            return 'Melhor Audio (MP3)'
        q = 'best'
        for name, chip in self.quality_chips.items():
            if chip.state == 'down':
                q = quality_map.get(name, 'best')
                break
        if q == 'best':
            return 'Melhor Video (MP4)'
        return f'Video {q} (MP4)'

    def get_audio_quality(self):
        for name, chip in self.quality_chips.items():
            if chip.state == 'down':
                return name
        return '192kbps'

    def on_format_chip(self, instance):
        is_mp3 = instance.text == 'MP3'
        for name, chip in self.format_chips.items():
            if chip != instance:
                chip.state = 'normal'
            chip.on_state()
        self._build_quality_chips(is_audio=is_mp3)

    def on_quality_chip(self, instance):
        for name, chip in self.quality_chips.items():
            if chip != instance:
                chip.state = 'normal'
            chip.on_state()

    @mainthread
    def on_progress(self, value):
        self.progress_bar.value = value

    @mainthread
    def on_status(self, text):
        self.status_label.text = text

    def log(self, msg):
        self.log_area.append(msg)

    def start_download(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = 'Cole um link primeiro!'
            return

        self.download_btn.disabled = True
        self.download_btn.text = 'Baixando...'
        self.progress_bar.value = 0
        self.status_label.text = 'Iniciando...'
        self.log_area.log_label.text = ''

        thread = threading.Thread(target=self._do_download, args=(url,), daemon=True)
        thread.start()

    def _do_download(self, url):
        fmt = self.get_format_string()
        audio_q = self.get_audio_quality()
        is_audio = 'MP3' in fmt or 'audio' in fmt.lower()
        output_path = get_download_path(is_audio=is_audio)
        try:
            success, result, title = self.downloader.download(url, output_path, fmt, audio_q)
            if success:
                scan_file(result)
                self.on_success(result, title)
            else:
                self.on_error(result)
        except Exception as e:
            self.on_error(str(e))

    @mainthread
    def on_success(self, filepath, title):
        self.progress_bar.value = 100
        self.status_label.text = 'Download concluido!'
        self.log(f'OK: {title}')
        self.log(f'Arquivo salvo em: {filepath}')
        self.download_btn.disabled = False
        self.download_btn.text = 'Baixar'

    @mainthread
    def on_error(self, error_msg):
        self.progress_bar.value = 0
        self.status_label.text = 'Erro no download'
        self.log(f'Erro: {error_msg}')
        self.download_btn.disabled = False
        self.download_btn.text = 'Baixar'


class BaixadorApp(App):
    def build(self):
        self.title = 'Baixador de Links'
        return MainLayout()


if __name__ == '__main__':
    BaixadorApp().run()
