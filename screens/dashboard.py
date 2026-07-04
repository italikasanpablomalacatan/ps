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

class DashboardScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name="dashboard", **kw)
        self._session  = session
        self._navigate = navigate
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BgWidget(bg=hex_rgba(T["bg"]), orientation="vertical", padding=dp(14), spacing=dp(10))
        scroll = PosScroll()
        inner = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        inner.bind(minimum_height=inner.setter("height"))
        from datetime import datetime
        hora = datetime.now().hour
        saludo = "Buenos dias" if hora < 12 else "Buenas tardes" if hora < 19 else "Buenas noches"
        inner.add_widget(Label(text=f"{saludo}, {self._session["nombre"].split()[0]}!", font_size=sp(20), bold=True, color=TEXT, size_hint_y=None, height=dp(36), halign="left"))
        stats = db.stats_hoy()
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(190))
        for title, val, sub, color, icon in [
            ("Ventas hoy", str(stats["ventas_num"]), "transacciones", ACCENT, "Ventas"),
            ("Ingresos", f"{MON}{stats["ventas_total"]:,.2f}", "", SUCCESS, "Ingresos"),
            ("Gastos", f"{MON}{stats["gasto_hoy"]:,.2f}", "", WARNING, "Gastos"),
            ("Utilidad", f"{MON}{stats["utilidad"]:,.2f}", "", SUCCESS if stats["utilidad"]>=0 else DANGER, "Utilidad"),
        ]:
            grid.add_widget(StatCard(title, val, sub, color, icon))
        inner.add_widget(grid)
        bajo = db.productos_stock_bajo()
        if bajo:
            a = BgWidget(bg=hex_rgba("#1A0800"), size_hint_y=None, height=dp(40), padding=dp(8))
            a.add_widget(Label(text=f"Stock bajo en {len(bajo)} productos", font_size=sp(13), color=WARNING, bold=True))
            inner.add_widget(a)
        inner.add_widget(Label(text="Accesos rapidos", font_size=sp(13), color=TEXT_DIM, size_hint_y=None, height=dp(24), halign="left"))
        btn_grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(100))
        for label, target, color in [("Nueva Venta","pos",ACCENT),("Productos","productos",SUCCESS),("Ventas","ventas",SURFACE2),("Corte","corte",SURFACE2)]:
            if target == "corte" and self._session["rol"] != "admin":
                btn_grid.add_widget(Widget()); continue
            btn = PosButton(label, bg_color=color, text_color=(0,0,0,1) if color==SUCCESS else (1,1,1,1))
            btn.bind(on_release=lambda b, t=target: self._navigate(t))
            btn_grid.add_widget(btn)
        inner.add_widget(btn_grid)
        top = db.top_productos(5, 30)
        if top:
            inner.add_widget(Label(text="Top 5 productos", font_size=sp(13), bold=True, color=ACCENT, size_hint_y=None, height=dp(26), halign="left"))
            for i, p in enumerate(top, 1):
                row = BgWidget(bg=hex_rgba(T["surface"]), orientation="horizontal", size_hint_y=None, height=dp(36), padding=[dp(10),0])
                row.add_widget(Label(text=f"{i}. {p["nombre"][:26]}", font_size=sp(11), color=TEXT, halign="left"))
                row.add_widget(Label(text=f"{p["qty"]} uds  {MON}{p["total"]:.2f}", font_size=sp(11), color=ACCENT, halign="right"))
                inner.add_widget(row)
        inner.add_widget(Widget(size_hint_y=None, height=dp(20)))
        scroll.add_widget(inner); root.add_widget(scroll); self.add_widget(root)
    def on_enter(self): self.clear_widgets(); self._build()

