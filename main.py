import os
os.environ.setdefault('KIVY_NO_ENV_CONFIG','1')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window

import database as db
from components import *
from config import TEMA as T, TIENDA

from screens.dashboard  import DashboardScreen
from screens.pos        import POSScreen
from screens.productos  import ProductosScreen
from screens.inventario import InventarioScreen
from screens.ventas     import VentasScreen
from screens.clientes   import ClientesScreen
from screens.gastos     import GastosScreen
from screens.fiados     import FiadosScreen
from screens.corte      import CorteScreen
from screens.usuarios   import UsuariosScreen

Window.clearcolor = hex_rgba(T['bg'])

MENU = [
    ('dashboard',  '⊞', 'Dashboard',   False),
    ('pos',        '🛒', 'Nueva Venta', False),
    ('productos',  '📦', 'Productos',   False),
    ('inventario', '📊', 'Inventario',  True),
    ('ventas',     '🧾', 'Ventas',      False),
    ('fiados',     '🤝', 'Fiados',      False),
    ('clientes',   '👥', 'Clientes',    False),
    ('gastos',     '💸', 'Gastos',      False),
    ('corte',      '🗂', 'Corte',       True),
    ('usuarios',      '🔐', 'Usuarios',      True),
    ('configuracion','⚙',  'Configuracion', True),
]

SCREENS = {
    'dashboard': DashboardScreen, 'pos': POSScreen,
    'productos': ProductosScreen, 'inventario': InventarioScreen,
    'ventas': VentasScreen,       'clientes': ClientesScreen,
    'gastos': GastosScreen,       'fiados': FiadosScreen,
    'corte': CorteScreen,         'usuarios': UsuariosScreen,
}


class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name='login', **kw)
        root = BgWidget(bg=hex_rgba(T['bg']), orientation='vertical', padding=dp(20), spacing=dp(16))
        root.add_widget(Widget())
        root.add_widget(Label(text=TIENDA['nombre'], font_size=sp(30), bold=True,
                              color=TEXT, size_hint_y=None, height=dp(44)))
        if TIENDA.get('slogan'):
            root.add_widget(Label(text=TIENDA['slogan'], font_size=sp(14),
                                  color=TEXT_DIM, size_hint_y=None, height=dp(26)))

        card = Card(orientation='vertical', spacing=dp(10),
                    size_hint=(0.38, None), height=dp(290),
                    pos_hint={'center_x': 0.5})

        card.add_widget(Label(text='Iniciar sesión', font_size=sp(17), bold=True,
                              color=TEXT, size_hint_y=None, height=dp(30)))

        for lbl, attr, pw in [('Usuario','user_in',False),('Contraseña','pw_in',True)]:
            card.add_widget(Label(text=lbl, font_size=sp(11), color=TEXT_DIM,
                                  size_hint_y=None, height=dp(20), halign='left'))
            inp = PosInput(hint=lbl.lower(), password=pw)
            inp.size_hint_y = None; inp.height = dp(44)
            setattr(self, attr, inp)
            card.add_widget(inp)

        self.pw_in.bind(on_text_validate=lambda *a: self._login())
        self.err_lbl = Label(text='', font_size=sp(11), color=DANGER,
                              size_hint_y=None, height=dp(22))
        card.add_widget(self.err_lbl)

        btn = PosButton('ENTRAR', bg_color=ACCENT, size_hint_y=None, height=dp(48))
        btn.bind(on_release=lambda *a: self._login())
        card.add_widget(btn)

        root.add_widget(card)
        root.add_widget(Widget())
        self.add_widget(root)

    def _login(self):
        user = self.user_in.text.strip()
        pw   = self.pw_in.text
        if not user or not pw:
            self.err_lbl.text = 'Completa todos los campos'; return
        result = db.login(user, pw)
        if result:
            app = App.get_running_app()
            app.session = result
            app.build_main(result)
            self.manager.current = 'main'
        else:
            self.err_lbl.text = 'Usuario o contraseña incorrectos'
            self.pw_in.text   = ''


class MainScreen(Screen):
    def __init__(self, session, **kw):
        super().__init__(name='main', **kw)
        self._session = session
        self._current = None
        root = BoxLayout(orientation='horizontal')

        # Sidebar
        self._sidebar = BgWidget(bg=hex_rgba(T['surface']), orientation='vertical',
                                  size_hint=(None,1), width=dp(195),
                                  padding=[dp(8),dp(10),dp(8),dp(10)], spacing=dp(3))
        self._sidebar.add_widget(Label(text=TIENDA['nombre'], font_size=sp(14),
                                        bold=True, color=TEXT,
                                        size_hint_y=None, height=dp(38)))
        self._sidebar.add_widget(HSep())
        self._sidebar.add_widget(Widget(size_hint_y=None, height=dp(6)))

        self._nav_btns = {}
        is_admin  = session['rol'] == 'admin'
        admin_set = {'usuarios','inventario','corte'}

        for item_id, icon, label, _ in MENU:
            if item_id in admin_set and not is_admin:
                continue
            btn = ToggleButton(text=f'  {icon}  {label}',
                               group='nav', font_size=sp(13),
                               background_normal='', background_down='',
                               background_color=hex_rgba(T['surface']),
                               color=TEXT_DIM, halign='left',
                               size_hint_y=None, height=dp(44))
            btn.bind(on_release=lambda b, i=item_id: self._navigate(i))
            self._nav_btns[item_id] = btn
            self._sidebar.add_widget(btn)

        self._sidebar.add_widget(Widget())
        self._sidebar.add_widget(HSep())

        user_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
        user_row.add_widget(Label(text=f"● {session['nombre'].split()[0]}",
                                   font_size=sp(11), color=SUCCESS))
        logout = PosButton('⏻', bg_color=DANGER, size_hint_x=None, width=dp(38))
        logout.bind(on_release=lambda *a: self._logout())
        user_row.add_widget(logout)
        self._sidebar.add_widget(user_row)
        root.add_widget(self._sidebar)

        # Content
        content = BoxLayout(orientation='vertical')
        topbar  = BgWidget(bg=hex_rgba(T['surface']), orientation='horizontal',
                            size_hint_y=None, height=dp(46), padding=[dp(14),0])
        self._page_title = Label(text='', font_size=sp(15), bold=True, color=TEXT, halign='left')
        self._clock_lbl  = Label(text='', font_size=sp(11), color=TEXT_DIM, halign='right')
        topbar.add_widget(self._page_title)
        topbar.add_widget(self._clock_lbl)
        content.add_widget(topbar)
        content.add_widget(HSep())

        self._sm = ScreenManager(transition=FadeTransition(duration=0.15))
        content.add_widget(self._sm)
        root.add_widget(content)
        self.add_widget(root)
        Clock.schedule_interval(self._tick, 1)
        self._navigate('dashboard')

    def _navigate(self, view_id):
        if self._current and self._current in self._nav_btns:
            b = self._nav_btns[self._current]
            b.background_color = hex_rgba(T['surface'])
            b.color = TEXT_DIM; b.bold = False
        self._current = view_id
        if view_id in self._nav_btns:
            b = self._nav_btns[view_id]
            b.background_color = hex_rgba(T['surface2'])
            b.color = ACCENT; b.bold = True; b.state = 'down'
        labels = {v[0]:v[2] for v in MENU}
        self._page_title.text = labels.get(view_id,'')
        if view_id not in self._sm.screen_names:
            cls = SCREENS.get(view_id)
            if cls:
                self._sm.add_widget(cls(session=self._session, navigate=self._navigate))
        self._sm.current = view_id

    def _tick(self, dt):
        from datetime import datetime
        self._clock_lbl.text = datetime.now().strftime('%H:%M  %d/%m/%Y')

    def _logout(self):
        def _do():
            self.manager.current = 'login'
        ConfirmPopup('Cerrar sesión','¿Deseas cerrar la sesión?',on_confirm=_do).open()


class POSApp(App):
    title   = TIENDA['nombre']
    session = None

    def build(self):
        db.init_db()
        self.sm = ScreenManager(transition=FadeTransition(duration=0.2))
        self.sm.add_widget(LoginScreen())
        return self.sm

    def build_main(self, session):
        if 'main' in self.sm.screen_names:
            self.sm.remove_widget(self.sm.get_screen('main'))
        self.sm.add_widget(MainScreen(session=session))


if __name__ == '__main__':
    POSApp().run()
