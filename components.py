from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.animation import Animation
from config import TEMA as T

def hex_rgba(h, a=1.0):
    h = h.lstrip('#')
    return (int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255, a)

BG       = hex_rgba(T['bg'])
SURFACE  = hex_rgba(T['surface'])
SURFACE2 = hex_rgba(T['surface2'])
BORDER   = hex_rgba(T['border'])
ACCENT   = hex_rgba(T['accent'])
TEXT     = hex_rgba(T['text'])
TEXT_DIM = hex_rgba(T['text_dim'])
SUCCESS  = hex_rgba(T['success'])
WARNING  = hex_rgba(T['warning'])
DANGER   = hex_rgba(T['danger'])


class BgWidget(BoxLayout):
    def __init__(self, bg=None, radius=8, **kw):
        super().__init__(**kw)
        self._bg = bg or BG
        with self.canvas.before:
            Color(*self._bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._rect.pos = self.pos; self._rect.size = self.size


class Card(BgWidget):
    def __init__(self, **kw):
        super().__init__(bg=SURFACE, radius=12, **kw)
        self.padding = [dp(14), dp(10), dp(14), dp(10)]
        self.spacing = dp(8)


class PosButton(Button):
    def __init__(self, text='', bg_color=None, text_color=None, font_size=None, **kw):
        self._bg = bg_color or ACCENT
        super().__init__(
            text=text,
            background_normal='', background_color=self._bg,
            color=text_color or (1,1,1,1),
            font_size=font_size or sp(14), bold=True, **kw)
        self.bind(on_press=lambda *a: Animation(background_color=self._darken(self._bg), duration=0.07).start(self),
                  on_release=lambda *a: Animation(background_color=self._bg, duration=0.12).start(self))

    def _darken(self, c): return tuple(max(0,x-0.1) if i<3 else x for i,x in enumerate(c))


class PosInput(TextInput):
    def __init__(self, hint='', **kw):
        super().__init__(
            hint_text=hint, background_color=SURFACE2,
            foreground_color=TEXT, hint_text_color=TEXT_DIM,
            cursor_color=ACCENT, multiline=False,
            padding=[dp(12), dp(10)], font_size=sp(14), **kw)


class HSep(Widget):
    def __init__(self, **kw):
        super().__init__(size_hint_y=None, height=dp(1), **kw)
        with self.canvas:
            Color(*BORDER)
            self._r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *a: setattr(self._r,'pos',self.pos),
                  size=lambda *a: setattr(self._r,'size',self.size))


class PosScroll(ScrollView):
    def __init__(self, **kw):
        super().__init__(do_scroll_x=False,
                          bar_color=hex_rgba(T['accent'],0.6),
                          bar_inactive_color=hex_rgba(T['border']),
                          bar_width=dp(4), **kw)


class StatCard(Card):
    def __init__(self, title, value, subtitle='', color=None, icon='', **kw):
        super().__init__(orientation='vertical', **kw)
        color = color or ACCENT
        self.add_widget(Label(text=f'{icon} {title}' if icon else title,
                              font_size=sp(10), color=TEXT_DIM))
        self.add_widget(Label(text=value, font_size=sp(22), bold=True, color=color))
        if subtitle:
            self.add_widget(Label(text=subtitle, font_size=sp(9), color=TEXT_DIM))


class Toast(BoxLayout):
    def __init__(self, message, tipo='success', duration=2.5, **kw):
        super().__init__(size_hint=(None,None), height=dp(48), **kw)
        colors = {'success':SUCCESS,'error':DANGER,'warning':WARNING,'info':ACCENT}
        bg = colors.get(tipo, ACCENT)
        icons = {'success':'✓','error':'✕','warning':'⚠','info':'ℹ'}
        with self.canvas.before:
            Color(*bg)
            self._r = RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
        self.bind(pos=lambda *a: setattr(self._r,'pos',self.pos),
                  size=lambda *a: setattr(self._r,'size',self.size))
        fc = (0,0,0,1) if tipo in ('success','warning') else (1,1,1,1)
        self.add_widget(Label(text=f' {icons.get(tipo,"ℹ")}  {message} ',
                              font_size=sp(13), bold=True, color=fc))
        Clock.schedule_once(lambda dt: self._hide(), duration)

    def _hide(self):
        anim = Animation(opacity=0, duration=0.3)
        anim.bind(on_complete=lambda *a: self.parent.remove_widget(self) if self.parent else None)
        anim.start(self)

    @classmethod
    def show(cls, parent, message, tipo='success', duration=2.5):
        t = cls(message, tipo, duration,
                pos_hint={'center_x':0.5,'y':0.04}, size_hint=(0.7,None))
        parent.add_widget(t)


class ConfirmPopup(Popup):
    def __init__(self, title, message, on_confirm, danger=False, **kw):
        content = BgWidget(bg=SURFACE, orientation='vertical', padding=dp(20), spacing=dp(12))
        content.add_widget(Label(text=message, font_size=sp(13), color=TEXT_DIM,
                                  halign='center', size_hint_y=None, height=dp(40)))
        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        cancel = PosButton('Cancelar', bg_color=SURFACE2, text_color=TEXT)
        ok_btn = PosButton('Confirmar', bg_color=DANGER if danger else ACCENT)
        cancel.bind(on_release=lambda *a: self.dismiss())
        ok_btn.bind(on_release=lambda *a: (on_confirm(), self.dismiss()))
        btn_row.add_widget(cancel); btn_row.add_widget(ok_btn)
        content.add_widget(btn_row)
        super().__init__(title=title, content=content,
                          size_hint=(None,None), size=(dp(360),dp(200)),
                          background_color=SURFACE, title_color=TEXT,
                          separator_color=ACCENT, **kw)
