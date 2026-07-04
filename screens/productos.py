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

class ProductosScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name="productos", **kw)
        self._session  = session
        self._navigate = navigate
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BgWidget(bg=hex_rgba(T["bg"]), orientation="vertical", padding=dp(14), spacing=dp(8))
        bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        bar.add_widget(Label(text="Productos", font_size=sp(18), bold=True, color=TEXT, halign="left"))
        new_btn = PosButton("+ Nuevo", bg_color=ACCENT, size_hint_x=None, width=dp(110))
        new_btn.bind(on_release=lambda *a: self._form_popup(None))
        bar.add_widget(new_btn)
        root.add_widget(bar)
        self._search = PosInput(hint="Buscar producto...")
        self._search.size_hint_y = None; self._search.height = dp(42)
        self._search.bind(text=lambda i,t: self._load(t))
        root.add_widget(self._search)
        scroll = PosScroll()
        self._box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self._box.bind(minimum_height=self._box.setter("height"))
        scroll.add_widget(self._box); root.add_widget(scroll); self.add_widget(root)
        self._load()
    def _load(self, busq=""):
        self._box.clear_widgets()
        prods = db.get_productos(True, busq)
        if not prods:
            self._box.add_widget(Label(text="Sin productos. Toca + Nuevo para agregar.", font_size=sp(13), color=TEXT_DIM, size_hint_y=None, height=dp(50))); return
        for p in prods:
            row = BgWidget(bg=hex_rgba(T["surface"]), orientation="horizontal", size_hint_y=None, height=dp(52), padding=[dp(12),0], spacing=dp(8))
            info = BoxLayout(orientation="vertical", size_hint_x=0.55)
            info.add_widget(Label(text=p["nombre"], font_size=sp(13), bold=True, color=TEXT, halign="left"))
            info.add_widget(Label(text=f'{p.get("cat_nombre","General")}  |  Cod: {p["codigo"]}', font_size=sp(10), color=TEXT_DIM, halign="left"))
            row.add_widget(info)
            stk_c = SUCCESS if p["stock"]>p["stock_min"] else WARNING if p["stock"]>0 else DANGER
            row.add_widget(Label(text=f'Stock: {p["stock"]}', font_size=sp(12), color=stk_c, size_hint_x=0.18))
            row.add_widget(Label(text=f'{MON}{p["precio_venta"]:.2f}', font_size=sp(13), bold=True, color=ACCENT, size_hint_x=0.18))
            edit = PosButton("✎", bg_color=hex_rgba(T["surface2"]), text_color=TEXT, font_size=sp(14), size_hint_x=None, width=dp(40))
            edit.bind(on_release=lambda b, pr=p: self._form_popup(pr))
            row.add_widget(edit)
            self._box.add_widget(row)
    def _form_popup(self, producto):
        cats = db.get_categorias(); cat_names = [c["nombre"] for c in cats]; cat_ids = [c["id"] for c in cats]
        p = producto or {}
        content = BgWidget(bg=hex_rgba(T["surface"]), orientation="vertical", spacing=dp(8), padding=dp(14))
        scroll = PosScroll(); box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        fields = {}
        for lbl, key, default in [("Codigo *","codigo",p.get("codigo","")),("Nombre *","nombre",p.get("nombre","")),
            ("Descripcion","descripcion",p.get("descripcion","")),("Precio venta *","precio_venta",str(p.get("precio_venta","0"))),
            ("Precio costo","precio_costo",str(p.get("precio_costo","0"))),("Stock","stock",str(p.get("stock","0"))),
            ("Stock minimo","stock_min",str(p.get("stock_min","5"))),("Unidad","unidad",p.get("unidad","unidad"))]:
            box.add_widget(Label(text=lbl, font_size=sp(11), color=TEXT_DIM, size_hint_y=None, height=dp(20), halign="left"))
            inp = PosInput(hint=lbl, text=default); inp.size_hint_y=None; inp.height=dp(42)
            fields[key] = inp; box.add_widget(inp)
        scroll.add_widget(box); content.add_widget(scroll)
        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        popup = Popup(title="Editar producto" if producto else "Nuevo producto", content=content, size_hint=(0.75,0.92), background_color=SURFACE, title_color=TEXT, separator_color=ACCENT)
        cancel = PosButton("Cancelar", bg_color=SURFACE2, text_color=TEXT); cancel.bind(on_release=lambda *a: popup.dismiss())
        def _save(*a):
            try:
                codigo=fields["codigo"].text.strip(); nombre=fields["nombre"].text.strip()
                if not codigo or not nombre: Toast.show(self,"Codigo y nombre requeridos","error"); return
                pv=float(fields["precio_venta"].text or 0); pc=float(fields["precio_costo"].text or 0)
                stock=int(float(fields["stock"].text or 0)); smin=int(float(fields["stock_min"].text or 5))
                cat_id=None
                if cat_names: cat_id=cat_ids[0]
                if producto:
                    ok,msg=db.actualizar_producto(producto["id"],codigo,nombre,fields["descripcion"].text,cat_id,pc,pv,stock,smin,fields["unidad"].text or "unidad")
                else:
                    ok,msg=db.crear_producto(codigo,nombre,fields["descripcion"].text,cat_id,pc,pv,stock,smin,fields["unidad"].text or "unidad")
                if ok: Toast.show(self,"Guardado correctamente","success"); popup.dismiss(); self._load()
                else: Toast.show(self,msg,"error")
            except Exception as e: Toast.show(self,f"Error: {e}","error")
        save = PosButton("GUARDAR", bg_color=ACCENT); save.bind(on_release=_save)
        if producto and self._session["rol"]=="admin":
            def _del(*a):
                def _do(): db.eliminar_producto(producto["id"]); Toast.show(self,"Eliminado","warning"); popup.dismiss(); self._load()
                ConfirmPopup("Eliminar",f"Eliminar {producto["nombre"]}?",on_confirm=_do,danger=True).open()
            del_btn=PosButton("Eliminar",bg_color=DANGER,size_hint_x=None,width=dp(90)); del_btn.bind(on_release=_del); btn_row.add_widget(del_btn)
        btn_row.add_widget(cancel); btn_row.add_widget(save)
        content.add_widget(btn_row); popup.open()
    def on_enter(self): self._build()

