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

class GastosScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name="gastos", **kw)
        self._session  = session
        self._navigate = navigate
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BgWidget(bg=hex_rgba(T["bg"]), orientation="vertical", padding=dp(14), spacing=dp(8))
        bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        bar.add_widget(Label(text="Gastos", font_size=sp(18), bold=True, color=TEXT, halign="left"))
        new_btn = PosButton("+ Registrar", bg_color=ACCENT, size_hint_x=None, width=dp(120))
        new_btn.bind(on_release=lambda *a: self._form()); bar.add_widget(new_btn)
        root.add_widget(bar)
        self._status = Label(text="", font_size=sp(11), color=TEXT_DIM, size_hint_y=None, height=dp(22))
        root.add_widget(self._status)
        scroll = PosScroll()
        self._box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self._box.bind(minimum_height=self._box.setter("height"))
        scroll.add_widget(self._box); root.add_widget(scroll); self.add_widget(root); self._load()
    def _load(self):
        self._box.clear_widgets()
        from datetime import date
        hoy = date.today().strftime("%Y-%m-%d")
        gastos = db.get_gastos(hoy, hoy)
        total = sum(g["monto"] for g in gastos)
        self._status.text = f'{len(gastos)} gastos hoy  |  Total: {MON}{total:,.2f}'
        for g in gastos:
            row = BgWidget(bg=hex_rgba(T["surface"]), orientation="horizontal", size_hint_y=None, height=dp(48), padding=[dp(10),0])
            info = BoxLayout(orientation="vertical", size_hint_x=0.75)
            info.add_widget(Label(text=g["concepto"], font_size=sp(12), bold=True, color=TEXT, halign="left"))
            info.add_widget(Label(text=f'{g["categoria"]}  |  {g["fecha"][:10]}', font_size=sp(10), color=TEXT_DIM, halign="left"))
            row.add_widget(info)
            row.add_widget(Label(text=f'{MON}{g["monto"]:.2f}', font_size=sp(13), bold=True, color=WARNING))
            if self._session["rol"]=="admin":
                d = PosButton("X", bg_color=DANGER, font_size=sp(12), size_hint_x=None, width=dp(36))
                d.bind(on_release=lambda b, gid=g["id"]: self._del(gid)); row.add_widget(d)
            self._box.add_widget(row)
    def _del(self, gid):
        def _do(): db.eliminar_gasto(gid); Toast.show(self,"Eliminado","warning"); self._load()
        ConfirmPopup("Eliminar","Eliminar este gasto?",on_confirm=_do,danger=True).open()
    def _form(self):
        content = BgWidget(bg=SURFACE, orientation="vertical", spacing=dp(8), padding=dp(14))
        concepto = PosInput(hint="Concepto *"); concepto.size_hint_y=None; concepto.height=dp(44)
        monto    = PosInput(hint="Monto *", input_filter="float"); monto.size_hint_y=None; monto.height=dp(44)
        notas    = PosInput(hint="Notas"); notas.size_hint_y=None; notas.height=dp(44)
        for w in [Label(text="Concepto",font_size=sp(11),color=TEXT_DIM,size_hint_y=None,height=dp(20)), concepto,
                  Label(text="Monto",font_size=sp(11),color=TEXT_DIM,size_hint_y=None,height=dp(20)), monto,
                  Label(text="Notas",font_size=sp(11),color=TEXT_DIM,size_hint_y=None,height=dp(20)), notas]:
            content.add_widget(w)
        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        popup = Popup(title="Nuevo Gasto", content=content, size_hint=(0.65,0.65), background_color=SURFACE, title_color=TEXT, separator_color=ACCENT)
        cancel = PosButton("Cancelar", bg_color=SURFACE2, text_color=TEXT); cancel.bind(on_release=lambda *a: popup.dismiss())
        def _save(*a):
            c = concepto.text.strip()
            if not c: Toast.show(self,"Concepto requerido","error"); return
            try: m = float(monto.text or 0)
            except: Toast.show(self,"Monto invalido","error"); return
            if m<=0: Toast.show(self,"Monto debe ser > 0","error"); return
            db.registrar_gasto(c,"General",m,self._session["id"],notas.text)
            Toast.show(self,"Gasto registrado","success"); popup.dismiss(); self._load()
        save = PosButton("GUARDAR", bg_color=ACCENT); save.bind(on_release=_save)
        btn_row.add_widget(cancel); btn_row.add_widget(save); content.add_widget(btn_row); popup.open()
    def on_enter(self): self._build()

