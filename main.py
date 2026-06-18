import os
import threading

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle

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


class RoundedInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (1, 1, 1, 0)
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[12])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        with self.canvas.before:
            Color(0.2, 0.5, 1, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[12])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class Chip(ToggleButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.color = (1, 1, 1, 0.7)
        self.font_size = 13
        self.size_hint_y = None
        self.height = 40
        with self.canvas.before:
            Color(0.15, 0.15, 0.2, 1)
            self.rect_normal = RoundedRectangle(size=self.size, pos=self.pos, radius=[20])
        with self.canvas.before:
            Color(0.2, 0.5, 1, 1)
            self.rect_down = RoundedRectangle(size=(0, 0), pos=self.pos, radius=[20])
        self.bind(pos=self._update_rect, size=self._update_rect, state=self._update_state)

    def _update_rect(self, *args):
        self.rect_normal.pos = self.pos
        self.rect_normal.size = self.size
        self.rect_down.pos = self.pos

    def _update_state(self, *args):
        if self.state == 'down':
            self.rect_down.size = self.size
            self.rect_normal.size = (0, 0)
            self.color = (1, 1, 1, 1)
        else:
            self.rect_down.size = (0, 0)
            self.rect_normal.size = self.size
            self.color = (1, 1, 1, 0.7)


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
        with self.canvas.before:
            Color(0.08, 0.08, 0.12, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(pos=self._update_bg, size=self._update_bg)

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
            text='Cole o link do vídeo', font_size=14,
            color=(0.6, 0.6, 0.7, 1), size_hint_y=None, height=20, halign='left'
        ))

        self.url_input = RoundedInput(
            hint_text='https://youtube.com/...', multiline=False,
            size_hint_y=None, height=50, foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.4, 0.4, 0.5, 1), padding=[15, 15],
            font_size=14
        )
        body.add_widget(self.url_input)

        self.download_btn = RoundedButton(
            text='Baixar', font_size=17, bold=True,
            size_hint_y=None, height=52, color=(1, 1, 1, 1)
        )
        self.download_btn.bind(on_press=self.start_download)
        body.add_widget(self.download_btn)

        body.add_widget(Label(
            text='Formato', font_size=13,
            color=(0.6, 0.6, 0.7, 1), size_hint_y=None, height=18, halign='left'
        ))

        chips = BoxLayout(size_hint_y=None, height=44, spacing=8)
        self.format_chips = {}
        for fmt in ['MP4', 'MP3']:
            chip = Chip(text=fmt, group='format', size_hint_x=None, width=70)
            chip.bind(on_press=self.on_format_chip)
            chips.add_widget(chip)
            self.format_chips[fmt] = chip
        self.format_chips['MP4'].state = 'down'
        chips.add_widget(Label(size_hint_x=1))
        body.add_widget(chips)

        quality_box = BoxLayout(size_hint_y=None, height=40, spacing=6)
        self.quality_chips = {}
        for q in ['Melhor', '1080p', '720p', '480p']:
            chip = Chip(text=q, group='quality', size_hint_x=None, width=75)
            chip.bind(on_press=self.on_quality_chip)
            quality_box.add_widget(chip)
            self.quality_chips[q] = chip
        self.quality_chips['Melhor'].state = 'down'
        quality_box.add_widget(Label(size_hint_x=1))
        body.add_widget(quality_box)

        body.add_widget(BoxLayout(size_hint_y=0.02))

        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=6)
        with self.progress_bar.canvas.before:
            Color(0.15, 0.15, 0.2, 1)
            self.pb_bg = RoundedRectangle(size=self.progress_bar.size, pos=self.progress_bar.pos, radius=[3])
        self.progress_bar.bind(pos=self._update_pb, size=self._update_pb)
        body.add_widget(self.progress_bar)

        self.status_label = Label(
            text='Pronto para baixar', font_size=12,
            color=(0.5, 0.5, 0.6, 1), size_hint_y=None, height=18
        )
        body.add_widget(self.status_label)

        self.log_area = LogArea(size_hint_y=0.25)
        body.add_widget(self.log_area)

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def _update_header(self, *args):
        if hasattr(self, 'header_rect'):
            p = self.children[-1]
            self.header_rect.size = p.size
            self.header_rect.pos = p.pos

    def _update_pb(self, *args):
        self.pb_bg.size = self.progress_bar.size
        self.pb_bg.pos = self.progress_bar.pos

    def get_format_string(self):
        quality_map = {'Melhor': 'best', '1080p': '1080p', '720p': '720p', '480p': '480p'}
        fmt = 'MP3' if self.format_chips['MP3'].state == 'down' else 'MP4'
        q = 'best'
        for name, chip in self.quality_chips.items():
            if chip.state == 'down':
                q = quality_map[name]
                break
        if fmt == 'MP3':
            return 'Melhor Áudio (MP3)'
        if q == 'best':
            return 'Melhor Vídeo (MP4)'
        return f'Vídeo {q} (MP4)'

    def on_format_chip(self, instance):
        is_mp3 = instance.text == 'MP3'
        for name, chip in self.format_chips.items():
            if chip != instance:
                chip.state = 'normal'
        for name, chip in self.quality_chips.items():
            chip.disabled = is_mp3
            if is_mp3:
                chip.state = 'normal'

    def on_quality_chip(self, instance):
        for name, chip in self.quality_chips.items():
            if chip != instance:
                chip.state = 'normal'

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
        is_audio = 'MP3' in fmt or 'áudio' in fmt.lower()
        output_path = get_download_path(is_audio=is_audio)
        try:
            success, result, title = self.downloader.download(url, output_path, fmt)
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
