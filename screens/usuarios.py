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

class UsuariosScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name="usuarios", **kw)
        self._session  = session
        self._navigate = navigate
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BgWidget(bg=hex_rgba(T["bg"]), orientation="vertical", padding=dp(14), spacing=dp(8))
        bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        bar.add_widget(Label(text="Usuarios", font_size=sp(18), bold=True, color=TEXT, halign="left"))
        new_btn = PosButton("+ Nuevo", bg_color=ACCENT, size_hint_x=None, width=dp(110))
        new_btn.bind(on_release=lambda *a: self._form(None)); bar.add_widget(new_btn)
        root.add_widget(bar)
        scroll = PosScroll()
        self._box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        self._box.bind(minimum_height=self._box.setter("height"))
        scroll.add_widget(self._box); root.add_widget(scroll); self.add_widget(root); self._load()
    def _load(self):
        self._box.clear_widgets()
        for u in db.get_usuarios():
            row = BgWidget(bg=hex_rgba(T["surface"]), orientation="horizontal", size_hint_y=None, height=dp(52), padding=[dp(10),0], spacing=dp(8))
            info = BoxLayout(orientation="vertical", size_hint_x=0.65)
            color = ACCENT if u["rol"]=="admin" else TEXT
            info.add_widget(Label(text=u["nombre"], font_size=sp(13), bold=True, color=color, halign="left"))
            info.add_widget(Label(text=f'@{u["username"]}  |  {u["rol"].upper()}  |  {"Activo" if u["activo"] else "Inactivo"}', font_size=sp(10), color=TEXT_DIM, halign="left"))
            row.add_widget(info)
            edit = PosButton("✎", bg_color=SURFACE2, text_color=TEXT, size_hint_x=None, width=dp(40))
            edit.bind(on_release=lambda b, usr=u: self._form(usr)); row.add_widget(edit)
            if u["rol"] != "admin":
                d = PosButton("X", bg_color=DANGER, font_size=sp(12), size_hint_x=None, width=dp(36))
                d.bind(on_release=lambda b, uid=u["id"]: self._del(uid)); row.add_widget(d)
            self._box.add_widget(row)
    def _del(self, uid):
        def _do(): db.eliminar_usuario(uid); Toast.show(self,"Eliminado","warning"); self._load()
        ConfirmPopup("Eliminar usuario","Eliminar este usuario?",on_confirm=_do,danger=True).open()
    def _form(self, usuario):
        p = usuario or {}
        content = BgWidget(bg=SURFACE, orientation="vertical", spacing=dp(8), padding=dp(14))
        fields = {}
        for lbl, key in [("Nombre completo *","nombre"),("Usuario *","username")]:
            content.add_widget(Label(text=lbl, font_size=sp(11), color=TEXT_DIM, size_hint_y=None, height=dp(20)))
            inp = PosInput(hint=lbl, text=p.get(key,"")); inp.size_hint_y=None; inp.height=dp(42)
            fields[key]=inp; content.add_widget(inp)
        pw_lbl = Label(text="Contrasena *" if not usuario else "Nueva contrasena (vacio=sin cambio)", font_size=sp(11), color=TEXT_DIM, size_hint_y=None, height=dp(20))
        pw_in  = PosInput(hint="contrasena", password=True); pw_in.size_hint_y=None; pw_in.height=dp(42)
        content.add_widget(pw_lbl); content.add_widget(pw_in)
        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        popup = Popup(title="Usuario", content=content, size_hint=(0.65,0.7), background_color=SURFACE, title_color=TEXT, separator_color=ACCENT)
        cancel = PosButton("Cancelar", bg_color=SURFACE2, text_color=TEXT); cancel.bind(on_release=lambda *a: popup.dismiss())
        def _save(*a):
            nombre=fields["nombre"].text.strip(); username=fields["username"].text.strip()
            if not nombre or not username: Toast.show(self,"Nombre y usuario requeridos","error"); return
            if usuario:
                db.actualizar_usuario(usuario["id"],nombre,usuario["rol"],usuario["activo"])
                if pw_in.text: db.cambiar_password(usuario["id"],pw_in.text)
            else:
                pw=pw_in.text
                if not pw: Toast.show(self,"Contrasena requerida","error"); return
                ok,msg=db.crear_usuario(username,pw,nombre,"cajero")
                if not ok: Toast.show(self,msg,"error"); return
            Toast.show(self,"Guardado","success"); popup.dismiss(); self._load()
        save = PosButton("GUARDAR", bg_color=ACCENT); save.bind(on_release=_save)
        btn_row.add_widget(cancel); btn_row.add_widget(save); content.add_widget(btn_row); popup.open()
    def on_enter(self): self._build()

