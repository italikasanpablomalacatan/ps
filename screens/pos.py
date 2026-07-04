from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import dp, sp
from components import *
from config import TEMA as T, TIENDA
import database as db

MON = TIENDA['moneda']
IMP = TIENDA['impuesto']


class POSScreen(Screen):
    def __init__(self, session, navigate, **kw):
        super().__init__(name='pos', **kw)
        self._session        = session
        self._navigate       = navigate
        self._carrito        = []
        self._cliente_id     = None
        self._cliente_nombre = 'Consumidor Final'
        self._metodo         = 'efectivo'
        cls = db.get_clientes('Consumidor Final')
        if cls:
            self._cliente_id = cls[0]['id']
        self._build()

    def _build(self):
        self.clear_widgets()
        root = BoxLayout(orientation='horizontal', spacing=dp(8), padding=dp(8))

        left = BoxLayout(orientation='vertical', size_hint_x=0.58, spacing=dp(8))
        self._search_in = PosInput(hint='Buscar producto o codigo...')
        self._search_in.size_hint_y = None
        self._search_in.height      = dp(46)
        self._search_in.bind(text=lambda i, t: self._load_prods(t))
        left.add_widget(self._search_in)

        self._prod_scroll = PosScroll()
        self._prod_grid   = GridLayout(cols=3, spacing=dp(8), size_hint_y=None,
                                        row_default_height=dp(96))
        self._prod_grid.bind(minimum_height=self._prod_grid.setter('height'))
        self._prod_scroll.add_widget(self._prod_grid)
        left.add_widget(self._prod_scroll)
        root.add_widget(left)

        right = BgWidget(bg=hex_rgba(T['surface']), orientation='vertical',
                          size_hint_x=0.42, spacing=dp(6), padding=dp(10))

        cust_row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        self._cust_lbl = Label(text=f'Cliente: {self._cliente_nombre}',
                                font_size=sp(12), color=ACCENT, halign='left')
        cust_row.add_widget(self._cust_lbl)
        chg = PosButton('Cambiar', bg_color=hex_rgba(T['surface2']),
                         text_color=TEXT, font_size=sp(11),
                         size_hint_x=None, width=dp(80))
        chg.bind(on_release=lambda *a: self._select_cliente())
        cust_row.add_widget(chg)
        right.add_widget(cust_row)
        right.add_widget(HSep())

        self._cart_scroll = PosScroll(size_hint_y=0.42)
        self._cart_box    = BoxLayout(orientation='vertical', spacing=dp(2),
                                       size_hint_y=None)
        self._cart_box.bind(minimum_height=self._cart_box.setter('height'))
        self._cart_scroll.add_widget(self._cart_box)
        right.add_widget(self._cart_scroll)
        right.add_widget(HSep())

        for attr, txt in [('_sub_lbl', 'Subtotal: --'),
                           ('_imp_lbl', f'IVA {IMP}%: --'),
                           ('_tot_lbl', 'TOTAL: --')]:
            big  = attr == '_tot_lbl'
            lbl  = Label(text=txt,
                          font_size=sp(16 if big else 12),
                          bold=big, color=ACCENT if big else TEXT_DIM,
                          halign='right', size_hint_y=None, height=dp(28))
            lbl.bind(size=lambda w, s: setattr(w, 'text_size', s))
            setattr(self, attr, lbl)
            right.add_widget(lbl)
        right.add_widget(HSep())

        desc_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        desc_row.add_widget(Label(text='Desc. Q:', font_size=sp(12), color=TEXT_DIM,
                                   size_hint_x=None, width=dp(60)))
        self._desc_in = PosInput(hint='0.00', input_filter='float')
        self._desc_in.bind(text=lambda *a: self._update_totals())
        desc_row.add_widget(self._desc_in)
        right.add_widget(desc_row)

        pay_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(4))
        for m, icon in [('efectivo','Efec'), ('tarjeta','Tarj'),
                         ('transferencia','Transf'), ('otro','Otro')]:
            tb = ToggleButton(text=icon, group='metodo',
                               font_size=sp(11),
                               background_normal='',
                               background_down='',
                               background_color=hex_rgba(T['surface2']),
                               color=TEXT)
            if m == 'efectivo':
                tb.state = 'down'
                tb.background_color = ACCENT
            tb.bind(on_release=lambda b, mt=m: self._set_metodo(mt, b))
            pay_row.add_widget(tb)
        right.add_widget(pay_row)

        monto_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        monto_row.add_widget(Label(text='Recibido:', font_size=sp(12), color=TEXT_DIM,
                                    size_hint_x=None, width=dp(72)))
        self._monto_in = PosInput(hint='0.00', input_filter='float')
        self._monto_in.bind(text=lambda *a: self._update_cambio())
        monto_row.add_widget(self._monto_in)
        right.add_widget(monto_row)

        self._cambio_lbl = Label(text='Cambio: --', font_size=sp(14), bold=True,
                                  color=SUCCESS, halign='right',
                                  size_hint_y=None, height=dp(28))
        right.add_widget(self._cambio_lbl)
        right.add_widget(HSep())

        btn_row = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8))
        cobrar = PosButton('COBRAR', bg_color=SUCCESS,
                            text_color=(0, 0, 0, 1), font_size=sp(16))
        cobrar.bind(on_release=lambda *a: self._cobrar())
        fiar   = PosButton('FIAR', bg_color=hex_rgba(T['warning']),
                            text_color=(0, 0, 0, 1), font_size=sp(16))
        fiar.bind(on_release=lambda *a: self._fiar())
        btn_row.add_widget(cobrar)
        btn_row.add_widget(fiar)
        right.add_widget(btn_row)

        vaciar = PosButton('Vaciar carrito',
                            bg_color=hex_rgba(T['surface2']),
                            text_color=hex_rgba(T['danger']),
                            font_size=sp(12),
                            size_hint_y=None, height=dp(38))
        vaciar.bind(on_release=lambda *a: self._clear())
        right.add_widget(vaciar)

        root.add_widget(right)
        self.add_widget(root)
        self._load_prods()

    def on_enter(self):
        self._load_prods()

    def _set_metodo(self, metodo, btn):
        self._metodo = metodo
        btn.background_color = ACCENT

    def _load_prods(self, busq=''):
        self._prod_grid.clear_widgets()
        prods = db.get_productos(True, busq)
        cols  = 3
        rows  = max(1, -(-len(prods) // cols))
        self._prod_grid.rows = rows
        for p in prods:
            self._prod_grid.add_widget(self._prod_card(p))

    def _prod_card(self, p):
        ok = p['stock'] > 0
        card = BgWidget(bg=hex_rgba(T['surface']), orientation='vertical',
                         padding=dp(8), spacing=dp(3), radius=8)
        card.add_widget(Label(text=p['nombre'][:20],
                               font_size=sp(11), bold=True,
                               color=TEXT if ok else TEXT_DIM,
                               halign='center', valign='top'))
        card.add_widget(Label(text=f"{MON} {p['precio_venta']:.2f}",
                               font_size=sp(14), bold=True,
                               color=ACCENT if ok else TEXT_DIM))
        stk_c = SUCCESS if p['stock'] > p['stock_min'] else (
                hex_rgba(T['warning']) if p['stock'] > 0 else DANGER)
        card.add_widget(Label(text=f'Stock: {p["stock"]}',
                               font_size=sp(10), color=stk_c))
        if ok:
            card.bind(on_touch_down=lambda w, t, pr=p:
                      self._add_to_cart(pr) if w.collide_point(*t.pos) else None)
        return card

    def _add_to_cart(self, prod):
        if prod['stock'] <= 0:
            Toast.show(self, 'Sin stock disponible', 'warning'); return
        for item in self._carrito:
            if item['id'] == prod['id']:
                if item['cantidad'] >= prod['stock']:
                    Toast.show(self, 'Stock maximo alcanzado', 'warning'); return
                item['cantidad'] += 1
                self._refresh_cart(); return
        self._carrito.append({**prod, 'cantidad': 1})
        self._refresh_cart()
        Toast.show(self, f"+ {prod['nombre'][:20]}", 'success')

    def _refresh_cart(self):
        self._cart_box.clear_widgets()
        for item in self._carrito:
            row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
            row.add_widget(Label(
                text=f"{item['cantidad']}x  {item['nombre'][:18]}",
                font_size=sp(11), color=TEXT, size_hint_x=0.55))
            row.add_widget(Label(
                text=f"{MON}{item['precio_venta']*item['cantidad']:.2f}",
                font_size=sp(11), color=ACCENT, size_hint_x=0.25))
            minus = PosButton('-', bg_color=hex_rgba(T['surface2']),
                               text_color=TEXT, font_size=sp(14),
                               size_hint_x=None, width=dp(32))
            plus  = PosButton('+', bg_color=hex_rgba(T['surface2']),
                               text_color=TEXT, font_size=sp(14),
                               size_hint_x=None, width=dp(32))
            rm    = PosButton('X', bg_color=DANGER, font_size=sp(12),
                               size_hint_x=None, width=dp(32))
            minus.bind(on_release=lambda b, i=item: self._dec_qty(i))
            plus.bind(on_release=lambda b, i=item: self._inc_qty(i))
            rm.bind(on_release=lambda b, i=item: self._rm_item(i))
            row.add_widget(minus); row.add_widget(plus); row.add_widget(rm)
            self._cart_box.add_widget(row)
        self._update_totals()

    def _inc_qty(self, item):
        if item['cantidad'] < item['stock']:
            item['cantidad'] += 1
            self._refresh_cart()

    def _dec_qty(self, item):
        if item['cantidad'] > 1:
            item['cantidad'] -= 1
        else:
            self._carrito.remove(item)
        self._refresh_cart()

    def _rm_item(self, item):
        if item in self._carrito:
            self._carrito.remove(item)
        self._refresh_cart()

    def _clear(self):
        def _do(): self._carrito = []; self._refresh_cart()
        if self._carrito:
            ConfirmPopup('Vaciar carrito', 'Vaciar el carrito?', on_confirm=_do).open()

    def _get_totals(self):
        sub = sum(i['precio_venta'] * i['cantidad'] for i in self._carrito)
        try: desc = float(self._desc_in.text or 0)
        except: desc = 0.0
        desc  = max(0, min(desc, sub))
        imp   = round((sub - desc) * IMP / 100, 2) if IMP else 0
        total = round(sub - desc + imp, 2)
        return sub, desc, imp, total

    def _update_totals(self):
        sub, desc, imp, total = self._get_totals()
        self._sub_lbl.text = f'Subtotal: {MON} {sub:.2f}'
        self._imp_lbl.text = f'IVA {IMP}%: {MON} {imp:.2f}'
        self._tot_lbl.text = f'TOTAL: {MON} {total:.2f}'
        self._update_cambio()

    def _update_cambio(self):
        try:
            _, _, _, total = self._get_totals()
            monto  = float(self._monto_in.text or 0)
            cambio = round(monto - total, 2)
            self._cambio_lbl.text  = f'Cambio: {MON} {cambio:.2f}'
            self._cambio_lbl.color = SUCCESS if cambio >= 0 else DANGER
        except Exception:
            pass

    def _select_cliente(self):
        content = BgWidget(bg=hex_rgba(T['surface']), orientation='vertical',
                            spacing=dp(8), padding=dp(12))
        search  = PosInput(hint='Buscar cliente...')
        search.size_hint_y = None; search.height = dp(42)
        content.add_widget(search)

        scroll = PosScroll()
        box    = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))
        box.bind(minimum_height=box.setter('height'))
        scroll.add_widget(box)
        content.add_widget(scroll)

        popup = Popup(title='Seleccionar cliente', content=content,
                       size_hint=(0.8, 0.85),
                       background_color=hex_rgba(T['surface']),
                       title_color=TEXT, separator_color=ACCENT)

        def _load(q=''):
            box.clear_widgets()
            for c in db.get_clientes(q):
                deuda = db.deuda_cliente(c['id'])
                txt   = f"{c['nombre']}  -  {c['nit']}"
                if deuda > 0:
                    txt += f"  (Debe {MON}{deuda:.2f})"
                btn = PosButton(txt, bg_color=hex_rgba(T['surface2']),
                                 text_color=TEXT, font_size=sp(12),
                                 size_hint_y=None, height=dp(44))
                def _sel(b, cl=c):
                    self._cliente_id     = cl['id']
                    self._cliente_nombre = cl['nombre']
                    self._cust_lbl.text  = f'Cliente: {cl["nombre"]}'
                    popup.dismiss()
                btn.bind(on_release=_sel)
                box.add_widget(btn)

        search.bind(text=lambda i, t: _load(t))
        _load()
        popup.open()

    def _cobrar(self):
        if not self._carrito:
            Toast.show(self, 'El carrito esta vacio', 'warning'); return
        sub, desc, imp, total = self._get_totals()
        metodo = self._metodo
        try: monto = float(self._monto_in.text or 0)
        except: monto = 0.0
        if metodo == 'efectivo':
            if monto <= 0:
                Toast.show(self, 'Ingresa el monto recibido', 'warning'); return
            if monto < total:
                Toast.show(self, f'Monto insuficiente', 'error'); return
        else:
            monto = total
        cambio = round(monto - total, 2)
        folio, vid = db.registrar_venta(
            self._session['id'], self._cliente_id, self._carrito,
            sub, imp, desc, total, metodo, monto, cambio)
        Toast.show(self, f'Venta {folio} registrada', 'success')
        self._show_ticket(folio, vid, sub, imp, desc, total, monto, cambio, metodo)
        self._carrito = []; self._monto_in.text = ''; self._desc_in.text = ''
        self._refresh_cart(); self._load_prods()

    def _fiar(self):
        if not self._carrito:
            Toast.show(self, 'El carrito esta vacio', 'warning'); return
        sub, desc, imp, total = self._get_totals()

        def _on_success():
            self._carrito = []; self._refresh_cart(); self._load_prods()

        NuevoFiadoPopup(self._carrito, self._session,
                         sub, imp, desc, total, _on_success).open()

    def _show_ticket(self, folio, vid, sub, imp, desc, total, monto, cambio, metodo):
        items = db.get_venta_items(vid)
        content = BgWidget(bg=hex_rgba(T['surface']), orientation='vertical',
                            spacing=dp(6), padding=dp(16))
        scroll = PosScroll()
        box    = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))
        box.bind(minimum_height=box.setter('height'))

        def _row(txt, size=12, bold=False, color=None):
            l = Label(text=txt, font_size=sp(size), bold=bold,
                       color=color or TEXT, halign='center',
                       size_hint_y=None, height=dp(size + 10))
            l.bind(size=lambda w, s: setattr(w, 'text_size', s))
            box.add_widget(l)

        _row(TIENDA['nombre'], 16, True)
        _row(f'Folio: {folio}', 13, True, ACCENT)
        _row('-' * 32, 9, color=TEXT_DIM)
        for it in items:
            _row(f"{it['cantidad']}x  {it['nombre_snap'][:24]}   {MON}{it['subtotal']:.2f}", 11)
        _row('-' * 32, 9, color=TEXT_DIM)
        _row(f'Subtotal: {MON}{sub:.2f}', 11, color=TEXT_DIM)
        if IMP and imp: _row(f'IVA {IMP}%: {MON}{imp:.2f}', 11, color=TEXT_DIM)
        if desc:        _row(f'Descuento: {MON}{desc:.2f}', 11, color=TEXT_DIM)
        _row(f'TOTAL: {MON}{total:.2f}', 16, True, ACCENT)
        if metodo == 'efectivo':
            _row(f'Recibido: {MON}{monto:.2f}', 11)
            _row(f'Cambio: {MON}{cambio:.2f}', 13, True, SUCCESS)
        _row('-' * 32, 9, color=TEXT_DIM)
        _row('Gracias por su compra!', 11, color=TEXT_DIM)

        scroll.add_widget(box)
        content.add_widget(scroll)
        close = PosButton('Cerrar', bg_color=hex_rgba(T['surface2']),
                           text_color=TEXT, size_hint_y=None, height=dp(48))
        content.add_widget(close)
        popup = Popup(title=f'Ticket - {folio}', content=content,
                       size_hint=(0.5, 0.92),
                       background_color=hex_rgba(T['surface']),
                       title_color=TEXT, separator_color=ACCENT)
        close.bind(on_release=lambda *a: popup.dismiss())
        popup.open()


class NuevoFiadoPopup(Popup):
    def __init__(self, carrito, session, subtotal, impuesto, descuento, total, on_success, **kw):
        from config import FIADO
        self._carrito    = carrito
        self._session    = session
        self._subtotal   = subtotal
        self._impuesto   = impuesto
        self._descuento  = descuento
        self._total      = total
        self._on_success = on_success
        self._cliente_id = None
        self._max        = FIADO.get('maximo_por_cliente', 500)

        content = BgWidget(bg=hex_rgba(T['surface']), orientation='vertical',
                            spacing=dp(10), padding=dp(16))

        content.add_widget(Label(text='Seleccionar cliente  *',
                                  font_size=sp(12), color=TEXT_DIM,
                                  size_hint_y=None, height=dp(22), halign='left'))

        search = PosInput(hint='Buscar cliente...')
        search.size_hint_y = None; search.height = dp(42)
        content.add_widget(search)

        scroll = PosScroll(size_hint_y=0.4)
        box    = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))
        box.bind(minimum_height=box.setter('height'))
        scroll.add_widget(box)
        content.add_widget(scroll)

        self._cust_sel = Label(text='Ningun cliente seleccionado',
                                font_size=sp(12), color=TEXT_DIM,
                                size_hint_y=None, height=dp(26))
        content.add_widget(self._cust_sel)

        content.add_widget(Label(
            text=f'Total a fiar: {MON} {total:.2f}',
            font_size=sp(16), bold=True, color=hex_rgba(T['warning']),
            size_hint_y=None, height=dp(30)))

        notas_in = PosInput(hint='Notas (opcional)')
        notas_in.size_hint_y = None; notas_in.height = dp(42)
        content.add_widget(notas_in)
        self._notas_in = notas_in

        btn_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        cancel  = PosButton('Cancelar', bg_color=hex_rgba(T['surface2']), text_color=TEXT)
        save    = PosButton('REGISTRAR FIADO',
                             bg_color=hex_rgba(T['warning']), text_color=(0,0,0,1))
        cancel.bind(on_release=lambda *a: self.dismiss())
        save.bind(on_release=lambda *a: self._save())
        btn_row.add_widget(cancel); btn_row.add_widget(save)
        content.add_widget(btn_row)

        def _load(q=''):
            box.clear_widgets()
            for c in db.get_clientes(q):
                deuda = db.deuda_cliente(c['id'])
                txt = f"{c['nombre']}  [{c['nit']}]"
                if deuda > 0: txt += f"  Debe: {MON}{deuda:.2f}"
                btn = PosButton(txt, bg_color=hex_rgba(T['surface2']),
                                 text_color=TEXT, font_size=sp(11),
                                 size_hint_y=None, height=dp(42))
                def _sel(b, cl=c):
                    self._cliente_id = cl['id']
                    self._cliente_nombre = cl['nombre']
                    self._cust_sel.text  = f'Seleccionado: {cl["nombre"]}'
                    self._cust_sel.color = ACCENT
                btn.bind(on_release=_sel)
                box.add_widget(btn)

        search.bind(text=lambda i, t: _load(t))
        _load()

        super().__init__(title='Registrar Fiado', content=content,
                          size_hint=(0.75, 0.92),
                          background_color=hex_rgba(T['surface']),
                          title_color=TEXT, separator_color=hex_rgba(T['warning']),
                          **kw)

    def _save(self):
        if not self._cliente_id:
            Toast.show(self, 'Selecciona un cliente', 'error'); return
        deuda = db.deuda_cliente(self._cliente_id)
        if deuda + self._total > self._max:
            Toast.show(self,
                f'Limite superado: {MON}{deuda+self._total:.2f} > max {MON}{self._max:.2f}',
                'error'); return
        db.registrar_fiado(
            self._session['id'], self._cliente_id, self._carrito,
            self._subtotal, self._impuesto, self._descuento,
            self._total, self._notas_in.text)
        Toast.show(self, 'Fiado registrado', 'success')
        self._on_success()
        self.dismiss()
