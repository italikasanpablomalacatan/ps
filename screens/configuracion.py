"""
screens/configuracion.py — Configuración de la tienda desde la app
Los cambios se guardan en config_local.json y sobreescriben los valores de config.py
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import dp, sp
from components import *
from config import TEMA as T, TIENDA, FIADO
import json, os

# Archivo donde se guardan los cambios locales
def _cfg_path():
    try:
        from android.storage import app_storage_path
        return os.path.join(app_storage_path(), 'config_local.json')
    except Exception:
        return 'config_local.json'

def cargar_config_local():
    """Lee config_local.json y devuelve dict con overrides."""
    try:
        with open(_cfg_path(), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def guardar_config_local(data):
    """Guarda los cambios en config_local.json."""
    with open(_cfg_path(), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_valor(seccion, clave, default):
    """Lee el valor local si existe, si no el default del config.py."""
    local = cargar_config_local()
    return local.get(seccion, {}).get(clave, default)


class ConfiguracionScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name='configuracion', **kw)
        self._session  = session
        self._navigate = navigate
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BgWidget(bg=hex_rgba(T['bg']), orientation='vertical',
                        padding=dp(14), spacing=dp(8))

        # Toolbar
        bar = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        bar.add_widget(Label(text='Configuracion', font_size=sp(18),
                              bold=True, color=TEXT, halign='left'))
        save_btn = PosButton('GUARDAR TODO', bg_color=ACCENT,
                              font_size=sp(13),
                              size_hint_x=None, width=dp(160))
        save_btn.bind(on_release=lambda *a: self._guardar_todo())
        bar.add_widget(save_btn)
        root.add_widget(bar)

        # Scroll con todas las secciones
        scroll = PosScroll()
        box    = BoxLayout(orientation='vertical', spacing=dp(10),
                            size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))

        self._campos = {}
        local = cargar_config_local()

        # ── SECCIÓN: Datos de la tienda ───────────────────────
        box.add_widget(self._seccion('Datos de la tienda'))
        tienda_fields = [
            ('nombre',    'Nombre de la tienda *', TIENDA.get('nombre', '')),
            ('slogan',    'Slogan',                TIENDA.get('slogan', '')),
            ('telefono',  'Telefono',               TIENDA.get('telefono', '')),
            ('direccion', 'Direccion',              TIENDA.get('direccion', '')),
            ('correo',    'Correo',                 TIENDA.get('correo', '')),
        ]
        for key, lbl, default in tienda_fields:
            val = local.get('tienda', {}).get(key, default)
            box.add_widget(self._campo(lbl, 'tienda', key, val))

        # ── SECCIÓN: Moneda e impuestos ───────────────────────
        box.add_widget(self._seccion('Moneda e Impuestos'))
        for key, lbl, default in [
            ('moneda',   'Simbolo de moneda  (Q, $, €)', TIENDA.get('moneda', 'Q')),
            ('impuesto', 'IVA / Impuesto en %  (0 = desactivado)', str(TIENDA.get('impuesto', 0))),
        ]:
            val = local.get('tienda', {}).get(key, default)
            box.add_widget(self._campo(lbl, 'tienda', key, str(val)))

        # ── SECCIÓN: Fiados ───────────────────────────────────
        box.add_widget(self._seccion('Fiados'))
        fiado_max = local.get('fiado', {}).get('maximo_por_cliente',
                               FIADO.get('maximo_por_cliente', 500))
        box.add_widget(self._campo(
            'Limite maximo de fiado por cliente',
            'fiado', 'maximo_por_cliente', str(fiado_max)))

        # ── SECCIÓN: Tema / Colores ───────────────────────────
        box.add_widget(self._seccion('Tema Visual  (colores en formato #RRGGBB)'))
        colores = [
            ('bg',       'Fondo principal',           T['bg']),
            ('surface',  'Fondo de tarjetas',         T['surface']),
            ('surface2', 'Fondo de inputs',           T['surface2']),
            ('accent',   'Color de acento (botones)', T['accent']),
            ('success',  'Color exito (verde)',        T['success']),
            ('warning',  'Color advertencia (naranja)',T['warning']),
            ('danger',   'Color peligro (rojo)',       T['danger']),
            ('text',     'Color de texto principal',  T['text']),
            ('text_dim', 'Color de texto secundario', T['text_dim']),
        ]
        for key, lbl, default in colores:
            val = local.get('tema', {}).get(key, default)
            row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))

            # Preview del color
            preview = BgWidget(bg=hex_rgba(val), radius=6,
                                size_hint_x=None, width=dp(36))
            row.add_widget(preview)

            lbl_w = Label(text=lbl, font_size=sp(11), color=TEXT_DIM,
                           halign='left', size_hint_x=0.45)
            lbl_w.bind(size=lambda w,s: setattr(w,'text_size',s))
            row.add_widget(lbl_w)

            inp = PosInput(hint='#RRGGBB', text=val)
            inp.size_hint_y = None; inp.height = dp(42)

            # Actualizar preview en tiempo real
            def _upd_preview(instance, value, prev=preview, inp_ref=inp):
                try:
                    if len(value) == 7 and value.startswith('#'):
                        prev.set_bg(hex_rgba(value))
                except Exception:
                    pass

            inp.bind(text=_upd_preview)
            row.add_widget(inp)

            self._campos[('tema', key)] = inp
            box.add_widget(row)

        # ── SECCIÓN: Temas predefinidos ───────────────────────
        box.add_widget(self._seccion('Temas Predefinidos  (aplica de un toque)'))
        temas_grid = GridLayout(cols=2, spacing=dp(8),
                                 size_hint_y=None, height=dp(220))
        presets = [
            ('Oscuro Violeta (default)', {
                'bg':'#0F0F13','surface':'#1A1A24','surface2':'#252535',
                'accent':'#6C63FF','success':'#43D9AD','warning':'#FFB347',
                'danger':'#FF6584','text':'#E8E8F0','text_dim':'#7070A0'}),
            ('Oscuro Azul', {
                'bg':'#0A192F','surface':'#112240','surface2':'#1D3557',
                'accent':'#64FFDA','success':'#64FFDA','warning':'#FFCC02',
                'danger':'#FF6584','text':'#CCD6F6','text_dim':'#8892B0'}),
            ('Oscuro Verde', {
                'bg':'#0D1117','surface':'#161B22','surface2':'#21262D',
                'accent':'#3FB950','success':'#3FB950','warning':'#D29922',
                'danger':'#F85149','text':'#E6EDF3','text_dim':'#7D8590'}),
            ('Oscuro Rojo', {
                'bg':'#13000A','surface':'#200010','surface2':'#2D0018',
                'accent':'#FF2D55','success':'#43D9AD','warning':'#FFB347',
                'danger':'#FF2D55','text':'#F0E0E5','text_dim':'#9A7080'}),
            ('Claro Blanco', {
                'bg':'#F5F5F7','surface':'#FFFFFF','surface2':'#EBEBEF',
                'accent':'#5856D6','success':'#34C759','warning':'#FF9500',
                'danger':'#FF3B30','text':'#1C1C1E','text_dim':'#8E8E93'}),
            ('Naranja Cafe', {
                'bg':'#1A1200','surface':'#271B00','surface2':'#342400',
                'accent':'#FF9F0A','success':'#43D9AD','warning':'#FF9F0A',
                'danger':'#FF6584','text':'#F0E8D0','text_dim':'#9A8860'}),
        ]
        for nombre, colores_preset in presets:
            btn = PosButton(nombre, bg_color=hex_rgba(colores_preset['accent']),
                             text_color=hex_rgba(colores_preset['text']),
                             font_size=sp(12))
            btn.bind(on_release=lambda b, cp=colores_preset: self._aplicar_preset(cp))
            temas_grid.add_widget(btn)
        box.add_widget(temas_grid)

        # ── SECCIÓN: Ticket ───────────────────────────────────
        box.add_widget(self._seccion('Ticket / Recibo'))
        pie_default = TIENDA.get('recibo', {})
        if isinstance(pie_default, dict):
            pie_default = pie_default.get('pie_de_pagina', '¡Gracias por su compra!')
        else:
            pie_default = '¡Gracias por su compra!'
        pie_val = local.get('tienda', {}).get('pie_ticket', pie_default)
        box.add_widget(self._campo('Mensaje pie de ticket', 'tienda', 'pie_ticket', pie_val))

        box.add_widget(Widget(size_hint_y=None, height=dp(20)))
        scroll.add_widget(box)
        root.add_widget(scroll)

        # Botón guardar abajo también
        save2 = PosButton('GUARDAR CONFIGURACION', bg_color=ACCENT,
                           font_size=sp(14),
                           size_hint_y=None, height=dp(54))
        save2.bind(on_release=lambda *a: self._guardar_todo())
        root.add_widget(save2)

        self.add_widget(root)
        self._box = box

    def _seccion(self, titulo):
        row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        row.add_widget(BgWidget(bg=ACCENT, radius=0,
                                 size_hint_x=None, width=dp(4)))
        row.add_widget(Label(text=titulo, font_size=sp(12), bold=True,
                              color=ACCENT, halign='left'))
        return row

    def _campo(self, lbl, seccion, key, default):
        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        lbl_w = Label(text=lbl, font_size=sp(11), color=TEXT_DIM,
                       halign='left', size_hint_x=0.45)
        lbl_w.bind(size=lambda w,s: setattr(w,'text_size',s))
        row.add_widget(lbl_w)
        inp = PosInput(hint=lbl, text=str(default))
        inp.size_hint_y = None; inp.height = dp(42)
        self._campos[(seccion, key)] = inp
        row.add_widget(inp)
        return row

    def _aplicar_preset(self, colores_preset):
        """Rellena los inputs de color con el preset seleccionado."""
        for key, val in colores_preset.items():
            inp = self._campos.get(('tema', key))
            if inp:
                inp.text = val
        Toast.show(self, 'Preset aplicado. Toca GUARDAR para confirmar.', 'info')

    def _guardar_todo(self):
        local = cargar_config_local()

        # Recoger todos los campos
        for (seccion, key), inp in self._campos.items():
            val = inp.text.strip()
            if seccion not in local:
                local[seccion] = {}
            # Convertir tipos
            if key in ('impuesto', 'maximo_por_cliente'):
                try: val = float(val)
                except: val = 0
            local[seccion][key] = val

        guardar_config_local(local)
        Toast.show(self, 'Configuracion guardada. Reinicia la app para ver cambios de color.', 'success')

    def on_enter(self):
        self._build()
