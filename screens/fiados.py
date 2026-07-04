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

class FiadosScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name="fiados", **kw)
        self._session  = session
        self._navigate = navigate
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BgWidget(bg=hex_rgba(T["bg"]), orientation="vertical", padding=dp(14), spacing=dp(8))
        bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        bar.add_widget(Label(text="Fiados", font_size=sp(18), bold=True, color=TEXT, halign="left"))
        ref = PosButton("Actualizar", bg_color=SURFACE2, text_color=TEXT, size_hint_x=None, width=dp(120))
        ref.bind(on_release=lambda *a: self._load()); bar.add_widget(ref)
        root.add_widget(bar)
        self._status = Label(text="", font_size=sp(11), color=TEXT_DIM, size_hint_y=None, height=dp(22))
        root.add_widget(self._status)
        scroll = PosScroll()
        self._box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self._box.bind(minimum_height=self._box.setter("height"))
        scroll.add_widget(self._box); root.add_widget(scroll); self.add_widget(root); self._load()
    def _load(self):
        self._box.clear_widgets()
        fiados = db.get_fiados(estado="pendiente")
        total_deuda = sum(f["total"]-f["pagado"] for f in fiados)
        self._status.text = f'{len(fiados)} fiados pendientes  |  Deuda total: {MON}{total_deuda:,.2f}'
        for f in fiados:
            deuda = f["total"] - f["pagado"]
            row = BgWidget(bg=hex_rgba(T["surface"]), orientation="horizontal", size_hint_y=None, height=dp(56), padding=[dp(10),0], spacing=dp(8))
            info = BoxLayout(orientation="vertical", size_hint_x=0.55)
            info.add_widget(Label(text=f.get("cliente_nombre",""), font_size=sp(13), bold=True, color=TEXT, halign="left"))
            info.add_widget(Label(text=f'Total: {MON}{f["total"]:.2f}  |  Pagado: {MON}{f["pagado"]:.2f}', font_size=sp(10), color=TEXT_DIM, halign="left"))
            row.add_widget(info)
            row.add_widget(Label(text=f'Deuda: {MON}{deuda:.2f}', font_size=sp(12), bold=True, color=DANGER, size_hint_x=0.28))
            pay = PosButton("Pagar", bg_color=SUCCESS, text_color=(0,0,0,1), font_size=sp(12), size_hint_x=None, width=dp(64))
            pay.bind(on_release=lambda b, fiad=f: self._pagar(fiad)); row.add_widget(pay)
            self._box.add_widget(row)
    def _pagar(self, fiado):
        deuda = fiado["total"] - fiado["pagado"]
        content = BgWidget(bg=SURFACE, orientation="vertical", spacing=dp(10), padding=dp(16))
        content.add_widget(Label(text=f'{fiado.get("cliente_nombre","")}', font_size=sp(14), bold=True, color=TEXT, size_hint_y=None, height=dp(30)))
        content.add_widget(Label(text=f'Deuda restante: {MON}{deuda:.2f}', font_size=sp(13), color=DANGER, size_hint_y=None, height=dp(26)))
        monto = PosInput(hint=f"Monto a pagar (max {MON}{deuda:.2f})", text=f"{deuda:.2f}", input_filter="float")
        monto.size_hint_y=None; monto.height=dp(44); content.add_widget(monto)
        notas = PosInput(hint="Notas opcionales"); notas.size_hint_y=None; notas.height=dp(42); content.add_widget(notas)
        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        popup = Popup(title="Registrar Pago", content=content, size_hint=(0.6,0.55), background_color=SURFACE, title_color=TEXT, separator_color=SUCCESS)
        cancel = PosButton("Cancelar", bg_color=SURFACE2, text_color=TEXT); cancel.bind(on_release=lambda *a: popup.dismiss())
        def _save(*a):
            try: m = float(monto.text or 0)
            except: Toast.show(self,"Monto invalido","error"); return
            if m<=0: Toast.show(self,"Monto debe ser > 0","error"); return
            if m>deuda+0.01: Toast.show(self,f"Maximo: {MON}{deuda:.2f}","error"); return
            db.registrar_pago_fiado(fiado["id"],m,self._session["id"],notas.text)
            msg = "Deuda cancelada!" if m>=deuda else f"Pago registrado. Resta: {MON}{deuda-m:.2f}"
            Toast.show(self,msg,"success"); popup.dismiss(); self._load()
        save = PosButton("GUARDAR PAGO", bg_color=SUCCESS, text_color=(0,0,0,1)); save.bind(on_release=_save)
        btn_row.add_widget(cancel); btn_row.add_widget(save); content.add_widget(btn_row); popup.open()
    def on_enter(self): self._build()

