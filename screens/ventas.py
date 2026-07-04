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

class VentasScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name="ventas", **kw)
        self._session  = session
        self._navigate = navigate
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BgWidget(bg=hex_rgba(T["bg"]), orientation="vertical", padding=dp(14), spacing=dp(8))
        bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        bar.add_widget(Label(text="Ventas", font_size=sp(18), bold=True, color=TEXT, halign="left"))
        ref = PosButton("Actualizar", bg_color=SURFACE2, text_color=TEXT, size_hint_x=None, width=dp(120))
        ref.bind(on_release=lambda *a: self._load()); bar.add_widget(ref)
        root.add_widget(bar)
        from datetime import date
        hoy = date.today().strftime("%Y-%m-%d")
        filter_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        filter_row.add_widget(Label(text="Desde:", font_size=sp(11), color=TEXT_DIM, size_hint_x=None, width=dp(50)))
        self._fi = PosInput(hint="YYYY-MM-DD", text=hoy); self._fi.size_hint_x=0.3
        filter_row.add_widget(self._fi)
        filter_row.add_widget(Label(text="Hasta:", font_size=sp(11), color=TEXT_DIM, size_hint_x=None, width=dp(50)))
        self._ff = PosInput(hint="YYYY-MM-DD", text=hoy); self._ff.size_hint_x=0.3
        filter_row.add_widget(self._ff)
        fb = PosButton("Filtrar", bg_color=ACCENT, size_hint_x=None, width=dp(80)); fb.bind(on_release=lambda *a: self._load())
        filter_row.add_widget(fb); root.add_widget(filter_row)
        self._status = Label(text="", font_size=sp(11), color=TEXT_DIM, size_hint_y=None, height=dp(22), halign="left")
        root.add_widget(self._status)
        scroll = PosScroll()
        self._box = BoxLayout(orientation="vertical", spacing=dp(3), size_hint_y=None)
        self._box.bind(minimum_height=self._box.setter("height"))
        scroll.add_widget(self._box); root.add_widget(scroll); self.add_widget(root)
        self._ventas = []; self._load()
    def _load(self):
        self._box.clear_widgets()
        uid = None if self._session["rol"]=="admin" else self._session["id"]
        self._ventas = db.get_ventas(self._fi.text or None, self._ff.text or None, True, uid)
        total = sum(v["total"] for v in self._ventas)
        self._status.text = f'{len(self._ventas)} ventas  |  Total: {MON}{total:,.2f}'
        for v in self._ventas:
            row = BgWidget(bg=hex_rgba(T["surface"]), orientation="horizontal", size_hint_y=None, height=dp(50), padding=[dp(10),0], spacing=dp(6))
            info = BoxLayout(orientation="vertical", size_hint_x=0.55)
            info.add_widget(Label(text=v["folio"], font_size=sp(12), bold=True, color=ACCENT, halign="left"))
            info.add_widget(Label(text=f'{v["fecha"][:16].replace("T"," ")}  |  {v.get("cajero","")}', font_size=sp(10), color=TEXT_DIM, halign="left"))
            row.add_widget(info)
            row.add_widget(Label(text=f'{MON}{v["total"]:.2f}', font_size=sp(14), bold=True, color=TEXT, size_hint_x=0.22))
            row.add_widget(Label(text=v["metodo_pago"].capitalize(), font_size=sp(11), color=TEXT_DIM, size_hint_x=0.15))
            if self._session["rol"]=="admin":
                anular = PosButton("Anular", bg_color=DANGER, font_size=sp(11), size_hint_x=None, width=dp(64))
                anular.bind(on_release=lambda b, vt=v: self._anular(vt)); row.add_widget(anular)
            self._box.add_widget(row)
    def _anular(self, venta):
        def _do(): db.anular_venta(venta["id"], self._session["id"]); Toast.show(self,"Venta anulada","warning"); self._load()
        ConfirmPopup("Anular venta", f"Anular {venta["folio"]}?", on_confirm=_do, danger=True).open()
    def on_enter(self): self._build()

