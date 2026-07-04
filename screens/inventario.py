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

class InventarioScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name="inventario", **kw)
        self._session  = session
        self._navigate = navigate
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BgWidget(bg=hex_rgba(T["bg"]), orientation="vertical", padding=dp(14), spacing=dp(8))
        root.add_widget(Label(text="Inventario", font_size=sp(18), bold=True, color=TEXT, size_hint_y=None, height=dp(36), halign="left"))
        val = db.inventario_valor()
        root.add_widget(Label(text=f'Valor en costo: {MON}{val["costo"]:,.2f}  |  Valor venta: {MON}{val["venta"]:,.2f}', font_size=sp(12), color=TEXT_DIM, size_hint_y=None, height=dp(24)))
        scroll = PosScroll()
        self._box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self._box.bind(minimum_height=self._box.setter("height"))
        scroll.add_widget(self._box); root.add_widget(scroll)
        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        for label, tipo, color in [("+ Entrada","entrada",SUCCESS),("- Salida","salida",DANGER),("Ajuste","ajuste",WARNING)]:
            b = PosButton(label, bg_color=color, text_color=(0,0,0,1) if color in (SUCCESS,WARNING) else (1,1,1,1))
            b.bind(on_release=lambda b2, t=tipo: self._ajustar(t)); btn_row.add_widget(b)
        root.add_widget(btn_row); self.add_widget(root); self._load()
        self._selected = None
    def _load(self):
        self._box.clear_widgets()
        prods = db.get_productos(True)
        for p in prods:
            stk_c = SUCCESS if p["stock"]>p["stock_min"] else WARNING if p["stock"]>0 else DANGER
            estado = "OK" if p["stock"]>p["stock_min"] else "BAJO" if p["stock"]>0 else "AGOTADO"
            row = BgWidget(bg=hex_rgba(T["surface"]), orientation="horizontal", size_hint_y=None, height=dp(48), padding=[dp(10),0], spacing=dp(6))
            row.add_widget(Label(text=p["nombre"][:28], font_size=sp(12), color=TEXT, halign="left", size_hint_x=0.5))
            row.add_widget(Label(text=f'Stock: {p["stock"]}', font_size=sp(12), color=stk_c, size_hint_x=0.2))
            row.add_widget(Label(text=f'Min: {p["stock_min"]}', font_size=sp(11), color=TEXT_DIM, size_hint_x=0.15))
            row.add_widget(Label(text=estado, font_size=sp(11), color=stk_c, bold=True, size_hint_x=0.15))
            row.bind(on_touch_down=lambda w,t,pr=p: setattr(self,"_selected",pr) if w.collide_point(*t.pos) else None)
            self._box.add_widget(row)
    def _ajustar(self, tipo):
        if not self._selected: Toast.show(self,"Selecciona un producto primero","warning"); return
        p = self._selected
        content = BgWidget(bg=SURFACE, orientation="vertical", spacing=dp(10), padding=dp(16))
        content.add_widget(Label(text=f'{p["nombre"]} - Stock actual: {p["stock"]}', font_size=sp(13), color=TEXT, size_hint_y=None, height=dp(30)))
        qty_in = PosInput(hint="Cantidad", input_filter="int"); qty_in.size_hint_y=None; qty_in.height=dp(44)
        mot_in = PosInput(hint="Motivo (opcional)"); mot_in.size_hint_y=None; mot_in.height=dp(44)
        content.add_widget(qty_in); content.add_widget(mot_in)
        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        popup = Popup(title=f"Ajuste: {tipo}", content=content, size_hint=(0.6,0.5), background_color=SURFACE, title_color=TEXT, separator_color=ACCENT)
        cancel = PosButton("Cancelar", bg_color=SURFACE2, text_color=TEXT); cancel.bind(on_release=lambda *a: popup.dismiss())
        def _save(*a):
            try:
                qty = int(qty_in.text or 0)
                if qty<=0: Toast.show(self,"Cantidad debe ser > 0","error"); return
                db.ajustar_stock(p["id"], qty, tipo, mot_in.text, self._session["id"])
                Toast.show(self,"Inventario actualizado","success"); popup.dismiss(); self._load()
            except: Toast.show(self,"Cantidad invalida","error")
        save = PosButton("GUARDAR", bg_color=ACCENT); save.bind(on_release=_save)
        btn_row.add_widget(cancel); btn_row.add_widget(save); content.add_widget(btn_row); popup.open()
    def on_enter(self): self._build()

