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

class CorteScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name="corte", **kw)
        self._session  = session
        self._navigate = navigate
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BgWidget(bg=hex_rgba(T["bg"]), orientation="vertical", padding=dp(14), spacing=dp(8))
        root.add_widget(Label(text="Corte de Caja", font_size=sp(18), bold=True, color=TEXT, size_hint_y=None, height=dp(36), halign="left"))
        from datetime import date
        hoy = date.today().strftime("%Y-%m-%d")
        data = db.corte_diario(hoy)
        v = data["ventas"]; g = data["gastos"]; neto = v["total"]-g["total"]
        root.add_widget(Label(text=f"Corte del dia: {hoy}", font_size=sp(14), color=TEXT_DIM, size_hint_y=None, height=dp(26)))
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(180))
        for title, val, color in [
            ("Ventas", str(v["num"]), ACCENT),
            ("Ingresos", f"{MON}{v["total"]:,.2f}", SUCCESS),
            ("Gastos", f"{MON}{g["total"]:,.2f}", WARNING),
            ("Neto", f"{MON}{neto:,.2f}", SUCCESS if neto>=0 else DANGER),
        ]:
            c = Card(orientation="vertical")
            c.add_widget(Label(text=title, font_size=sp(11), color=TEXT_DIM))
            c.add_widget(Label(text=val, font_size=sp(20), bold=True, color=color))
            grid.add_widget(c)
        root.add_widget(grid)
        if data["metodos"]:
            root.add_widget(Label(text="Por metodo de pago:", font_size=sp(12), color=ACCENT, size_hint_y=None, height=dp(26), halign="left"))
            for m in data["metodos"]:
                row = BgWidget(bg=hex_rgba(T["surface"]), orientation="horizontal", size_hint_y=None, height=dp(36), padding=[dp(10),0])
                row.add_widget(Label(text=m["metodo_pago"].capitalize(), font_size=sp(12), color=TEXT))
                row.add_widget(Label(text=f'{m["num"]} ventas  —  {MON}{m["total"]:.2f}', font_size=sp(12), color=ACCENT, halign="right"))
                root.add_widget(row)
        total_card = Card(orientation="vertical", size_hint_y=None, height=dp(100))
        total_card.add_widget(Label(text=f"Ingresos:  {MON}{v["total"]:,.2f}", font_size=sp(13), color=SUCCESS))
        total_card.add_widget(Label(text=f"Gastos:    {MON}{g["total"]:,.2f}", font_size=sp(13), color=WARNING))
        total_card.add_widget(Label(text=f"NETO:      {MON}{neto:,.2f}", font_size=sp(15), bold=True, color=SUCCESS if neto>=0 else DANGER))
        root.add_widget(total_card)
        self.add_widget(root)
    def on_enter(self): self._build()

