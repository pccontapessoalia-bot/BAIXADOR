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
from kivy.uix.widget import Widget
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.utils import rgba
from kivy.metrics import dp, sp
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

BG = rgba('#0A0A0F')
SURFACE = rgba('#16161E')
SURFACE2 = rgba('#1E1E2A')
PRIMARY = rgba('#7C5CFC')
PRIMARY_DARK = rgba('#5A3FD6')
TEXT = rgba('#FFFFFF')
TEXT2 = rgba('#8B8BA3')
TEXT3 = rgba('#5A5A72')

Window.clearcolor = BG


class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*SURFACE)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[dp(16)])
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class RoundedInput(TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_color', SURFACE2)
        kwargs.setdefault('foreground_color', TEXT)
        kwargs.setdefault('hint_text_color', TEXT3)
        kwargs.setdefault('padding', [dp(16), dp(16)])
        kwargs.setdefault('font_size', sp(15))
        kwargs.setdefault('cursor_color', PRIMARY)
        kwargs.setdefault('border', [dp(14), dp(14), dp(14), dp(14)])
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(52))
        super().__init__(**kwargs)


class PrimaryButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_down', '')
        kwargs.setdefault('background_color', PRIMARY)
        kwargs.setdefault('font_size', sp(16))
        kwargs.setdefault('bold', True)
        kwargs.setdefault('color', TEXT)
        kwargs.setdefault('border', [dp(14), dp(14), dp(14), dp(14)])
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(54))
        super().__init__(**kwargs)
        self._bg = PRIMARY
        self._bg_down = PRIMARY_DARK

    def on_state(self, *args):
        self.background_color = self._bg_down if self.state == 'down' else self._bg


class Chip(ToggleButton):
    def __init__(self, **kwargs):
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_down', '')
        kwargs.setdefault('color', TEXT2)
        kwargs.setdefault('font_size', sp(13))
        kwargs.setdefault('size_hint_x', None)
        kwargs.setdefault('height', dp(36))
        kwargs.setdefault('width', dp(80))
        kwargs.setdefault('border', [dp(18), dp(18), dp(18), dp(18)])
        super().__init__(**kwargs)

    def on_state(self, *args):
        if self.state == 'down':
            self.background_color = PRIMARY
            self.color = TEXT
        else:
            self.background_color = SURFACE2
            self.color = TEXT2


class LogArea(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log_label = Label(
            text='', size_hint_y=None, halign='left', valign='top',
            text_size=(Window.width * 0.85, None), font_size=sp(12),
            color=TEXT2
        )
        self.add_widget(self.log_label)
        with self.canvas.before:
            Color(*SURFACE)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[dp(12)])
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    @mainthread
    def append(self, text):
        current = self.log_label.text
        new = f"{current}\n{text}" if current else text
        self.log_label.text = new
        self.log_label.texture_update()
        self.log_label.height = self.log_label.texture_size[1]
        self.scroll_to(self.log_label)


class Header(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(size_hint_y=0.12, padding=[dp(20), dp(10), dp(20), dp(15)], **kwargs)
        with self.canvas.before:
            Color(*PRIMARY)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(pos=self._update, size=self._update)
        label = Label(
            text='Baixador de Links', font_size=sp(22), bold=True, color=TEXT,
            size_hint_x=0.7, halign='left', valign='middle'
        )
        label.bind(size=label.setter('text_size'))
        self.add_widget(label)
        subtitle = Label(
            text='YouTube, Instagram, TikTok', font_size=sp(11), color=rgba('#FFFFFFAA'),
            size_hint_x=0.3, halign='right', valign='middle'
        )
        subtitle.bind(size=subtitle.setter('text_size'))
        self.add_widget(subtitle)

    def _update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class SectionLabel(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', sp(13))
        kwargs.setdefault('color', TEXT3)
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(20))
        kwargs.setdefault('halign', 'left')
        kwargs.setdefault('bold', True)
        super().__init__(**kwargs)


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
        self.add_widget(Header())

        body = BoxLayout(
            orientation='vertical', spacing=dp(12), padding=[dp(20), dp(12), dp(20), dp(12)]
        )
        self.add_widget(body)

        card = Card(orientation='vertical', spacing=dp(10), padding=dp(16),
                     size_hint_y=None, height=dp(180))
        card.add_widget(SectionLabel(text='Cole o link do video'))
        self.url_input = RoundedInput(hint_text='https://youtube.com/...', multiline=False)
        card.add_widget(self.url_input)
        self.download_btn = PrimaryButton(text='Baixar')
        self.download_btn.bind(on_press=self.start_download)
        card.add_widget(self.download_btn)
        body.add_widget(card)

        card2 = Card(orientation='vertical', spacing=dp(8), padding=dp(16),
                      size_hint_y=None, height=dp(130))
        card2.add_widget(SectionLabel(text='Formato'))
        chips_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        self.format_chips = {}
        for fmt in ['MP4', 'MP3']:
            chip = Chip(text=fmt, group='format')
            chip.bind(on_press=self.on_format_chip)
            chips_row.add_widget(chip)
            self.format_chips[fmt] = chip
        self.format_chips['MP4'].state = 'down'
        self.format_chips['MP4'].on_state()
        self.format_chips['MP3'].on_state()
        chips_row.add_widget(Widget())
        card2.add_widget(chips_row)
        self.quality_box = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        self._build_quality_chips(is_audio=False)
        card2.add_widget(self.quality_box)
        body.add_widget(card2)

        card3 = Card(orientation='vertical', spacing=dp(6), padding=[dp(16), dp(12)],
                      size_hint_y=None, height=dp(60))
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(4))
        card3.add_widget(self.progress_bar)
        self.status_label = Label(
            text='Pronto para baixar', font_size=sp(12),
            color=TEXT3, size_hint_y=None, height=dp(18)
        )
        card3.add_widget(self.status_label)
        body.add_widget(card3)

        body.add_widget(SectionLabel(text='Log'))
        self.log_area = LogArea()
        body.add_widget(self.log_area)

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
        self.chip_set_default(default)
        self.quality_box.add_widget(Widget())

    def chip_set_default(self, default):
        for name, chip in self.quality_chips.items():
            chip.state = 'down' if name == default else 'normal'
            chip.on_state()

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
            chip.state = 'down' if chip == instance else 'normal'
            chip.on_state()
        self._build_quality_chips(is_audio=is_mp3)

    def on_quality_chip(self, instance):
        for name, chip in self.quality_chips.items():
            chip.state = 'down' if chip == instance else 'normal'
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
