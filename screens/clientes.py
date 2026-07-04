from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from components import *
from config import TEMA as T, TIENDA
import database as db

MON = TIENDA["moneda"]
IMP = TIENDA["impuesto"]

class ClientesScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name="clientes", **kw)
        self._session  = session
        self._navigate = navigate
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BgWidget(bg=hex_rgba(T["bg"]), orientation="vertical", padding=dp(14), spacing=dp(8))
        bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        bar.add_widget(Label(text="Clientes", font_size=sp(18), bold=True, color=TEXT, halign="left"))
        new_btn = PosButton("+ Nuevo", bg_color=ACCENT, size_hint_x=None, width=dp(110))
        new_btn.bind(on_release=lambda *a: self._form(None)); bar.add_widget(new_btn)
        root.add_widget(bar)
        self._search = PosInput(hint="Buscar cliente..."); self._search.size_hint_y=None; self._search.height=dp(42)
        self._search.bind(text=lambda i,t: self._load(t)); root.add_widget(self._search)
        scroll = PosScroll()
        self._box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self._box.bind(minimum_height=self._box.setter("height"))
        scroll.add_widget(self._box); root.add_widget(scroll); self.add_widget(root); self._load()
    def _load(self, busq=""):
        self._box.clear_widgets()
        cls = db.get_clientes(busq)
        for c in cls:
            deuda = db.deuda_cliente(c["id"])
            row = BgWidget(bg=hex_rgba(T["surface"]), orientation="horizontal", size_hint_y=None, height=dp(52), padding=[dp(10),0], spacing=dp(8))
            info = BoxLayout(orientation="vertical", size_hint_x=0.65)
            info.add_widget(Label(text=c["nombre"], font_size=sp(13), bold=True, color=TEXT, halign="left"))
            info.add_widget(Label(text=f'{c["telefono"]}  |  NIT: {c["nit"]}', font_size=sp(10), color=TEXT_DIM, halign="left"))
            row.add_widget(info)
            if deuda > 0:
                row.add_widget(Label(text=f"Deuda: {MON}{deuda:.2f}", font_size=sp(11), color=DANGER, bold=True, size_hint_x=0.22))
            edit = PosButton("✎", bg_color=SURFACE2, text_color=TEXT, size_hint_x=None, width=dp(40))
            edit.bind(on_release=lambda b, cl=c: self._form(cl)); row.add_widget(edit)
            self._box.add_widget(row)
    def _form(self, cliente):
        p = cliente or {}
        content = BgWidget(bg=SURFACE, orientation="vertical", spacing=dp(8), padding=dp(14))
        fields = {}
        for lbl, key in [("Nombre *","nombre"),("Telefono","telefono"),("Correo","correo"),("Direccion","direccion"),("NIT","nit")]:
            content.add_widget(Label(text=lbl, font_size=sp(11), color=TEXT_DIM, size_hint_y=None, height=dp(20), halign="left"))
            inp = PosInput(hint=lbl, text=p.get(key,"")); inp.size_hint_y=None; inp.height=dp(42)
            fields[key]=inp; content.add_widget(inp)
        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        popup = Popup(title="Cliente", content=content, size_hint=(0.7,0.88), background_color=SURFACE, title_color=TEXT, separator_color=ACCENT)
        cancel = PosButton("Cancelar", bg_color=SURFACE2, text_color=TEXT); cancel.bind(on_release=lambda *a: popup.dismiss())
        def _save(*a):
            nombre = fields["nombre"].text.strip()
            if not nombre: Toast.show(self,"Nombre requerido","error"); return
            if cliente: db.actualizar_cliente(cliente["id"],nombre,fields["telefono"].text,fields["correo"].text,fields["direccion"].text,fields["nit"].text or "CF")
            else: db.crear_cliente(nombre,fields["telefono"].text,fields["correo"].text,fields["direccion"].text,fields["nit"].text or "CF")
            Toast.show(self,"Guardado","success"); popup.dismiss(); self._load()
        save = PosButton("GUARDAR", bg_color=ACCENT); save.bind(on_release=_save)
        btn_row.add_widget(cancel); btn_row.add_widget(save); content.add_widget(btn_row); popup.open()
    def on_enter(self): self._build()

