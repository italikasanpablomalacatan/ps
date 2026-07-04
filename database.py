import sqlite3, hashlib, os
from datetime import datetime, date
from config import DB_PATH

def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def get_conn():
    try:
        from android.storage import app_storage_path
        path = os.path.join(app_storage_path(), DB_PATH)
    except Exception:
        path = DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, nombre TEXT NOT NULL, rol TEXT NOT NULL DEFAULT 'cajero',
        activo INTEGER NOT NULL DEFAULT 1, creado_en TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL, color TEXT DEFAULT '#6C63FF');
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL,
        descripcion TEXT DEFAULT '', categoria_id INTEGER, precio_costo REAL NOT NULL DEFAULT 0,
        precio_venta REAL NOT NULL DEFAULT 0, stock INTEGER NOT NULL DEFAULT 0,
        stock_min INTEGER NOT NULL DEFAULT 5, unidad TEXT DEFAULT 'unidad',
        activo INTEGER NOT NULL DEFAULT 1, creado_en TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, telefono TEXT DEFAULT '',
        correo TEXT DEFAULT '', direccion TEXT DEFAULT '', nit TEXT DEFAULT 'CF', creado_en TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT UNIQUE NOT NULL,
        usuario_id INTEGER, cliente_id INTEGER, subtotal REAL NOT NULL DEFAULT 0,
        impuesto REAL NOT NULL DEFAULT 0, descuento REAL NOT NULL DEFAULT 0,
        total REAL NOT NULL DEFAULT 0, metodo_pago TEXT NOT NULL DEFAULT 'efectivo',
        monto_pagado REAL NOT NULL DEFAULT 0, cambio REAL NOT NULL DEFAULT 0,
        estado TEXT NOT NULL DEFAULT 'completada', notas TEXT DEFAULT '', fecha TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS venta_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL, nombre_snap TEXT NOT NULL, precio_snap REAL NOT NULL,
        cantidad INTEGER NOT NULL, descuento REAL NOT NULL DEFAULT 0, subtotal REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, concepto TEXT NOT NULL,
        categoria TEXT DEFAULT 'General', monto REAL NOT NULL,
        usuario_id INTEGER, fecha TEXT NOT NULL, notas TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS fiados (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER NOT NULL,
        usuario_id INTEGER NOT NULL, subtotal REAL NOT NULL DEFAULT 0,
        impuesto REAL NOT NULL DEFAULT 0, descuento REAL NOT NULL DEFAULT 0,
        total REAL NOT NULL DEFAULT 0, pagado REAL NOT NULL DEFAULT 0,
        estado TEXT NOT NULL DEFAULT 'pendiente', notas TEXT DEFAULT '', fecha TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS fiado_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fiado_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL, nombre_snap TEXT NOT NULL,
        precio_snap REAL NOT NULL, cantidad INTEGER NOT NULL, subtotal REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS fiado_pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fiado_id INTEGER NOT NULL,
        monto REAL NOT NULL, usuario_id INTEGER, fecha TEXT NOT NULL, notas TEXT DEFAULT '');
    """)
    if not c.execute("SELECT id FROM usuarios WHERE username='admin'").fetchone():
        c.execute("INSERT INTO usuarios(username,password,nombre,rol,activo,creado_en) VALUES(?,?,?,?,1,?)",
                  ('admin',_hash('admin123'),'Administrador','admin',datetime.now().isoformat()))
    if not c.execute("SELECT id FROM clientes WHERE nit='CF'").fetchone():
        c.execute("INSERT INTO clientes(nombre,nit,creado_en) VALUES('Consumidor Final','CF',?)",(datetime.now().isoformat(),))
    for cat in ['General','Bebidas','Alimentos','Electrónica','Ropa','Hogar']:
        try: c.execute("INSERT INTO categorias(nombre) VALUES(?)",(cat,))
        except: pass
    conn.commit(); conn.close()

def login(username, password):
    conn = get_conn()
    row = conn.execute("SELECT * FROM usuarios WHERE username=? AND password=? AND activo=1",
                       (username,_hash(password))).fetchone()
    conn.close(); return dict(row) if row else None

def get_usuarios():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM usuarios ORDER BY nombre").fetchall()
    conn.close(); return [dict(r) for r in rows]

def crear_usuario(username, password, nombre, rol='cajero'):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO usuarios(username,password,nombre,rol,activo,creado_en) VALUES(?,?,?,?,1,?)",
                     (username,_hash(password),nombre,rol,datetime.now().isoformat()))
        conn.commit(); return True,"OK"
    except sqlite3.IntegrityError: return False,"Usuario ya existe"
    finally: conn.close()

def actualizar_usuario(uid,nombre,rol,activo):
    conn=get_conn(); conn.execute("UPDATE usuarios SET nombre=?,rol=?,activo=? WHERE id=?",(nombre,rol,activo,uid))
    conn.commit(); conn.close()

def cambiar_password(uid,nueva):
    conn=get_conn(); conn.execute("UPDATE usuarios SET password=? WHERE id=?",(_hash(nueva),uid))
    conn.commit(); conn.close()

def eliminar_usuario(uid):
    conn=get_conn(); conn.execute("DELETE FROM usuarios WHERE id=? AND rol!='admin'",(uid,))
    conn.commit(); conn.close()

def get_categorias():
    conn=get_conn(); rows=conn.execute("SELECT * FROM categorias ORDER BY nombre").fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_productos(solo_activos=True, busqueda=''):
    conn=get_conn()
    q="SELECT p.*, c.nombre as cat_nombre FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id WHERE 1=1"
    params=[]
    if solo_activos: q+=" AND p.activo=1"
    if busqueda: q+=" AND (p.nombre LIKE ? OR p.codigo LIKE ?)"; params+=[f'%{busqueda}%']*2
    q+=" ORDER BY p.nombre"
    rows=conn.execute(q,params).fetchall(); conn.close(); return [dict(r) for r in rows]

def get_producto_by_codigo(codigo):
    conn=get_conn()
    row=conn.execute("SELECT p.*, c.nombre as cat_nombre FROM productos p LEFT JOIN categorias c ON p.categoria_id=c.id WHERE p.codigo=? AND p.activo=1",(codigo,)).fetchone()
    conn.close(); return dict(row) if row else None

def crear_producto(codigo,nombre,descripcion,categoria_id,precio_costo,precio_venta,stock,stock_min,unidad):
    conn=get_conn()
    try:
        conn.execute("INSERT INTO productos(codigo,nombre,descripcion,categoria_id,precio_costo,precio_venta,stock,stock_min,unidad,activo,creado_en) VALUES(?,?,?,?,?,?,?,?,?,1,?)",
                     (codigo,nombre,descripcion,categoria_id,precio_costo,precio_venta,stock,stock_min,unidad,datetime.now().isoformat()))
        conn.commit(); return True,"OK"
    except sqlite3.IntegrityError: return False,"Código ya existe"
    finally: conn.close()

def actualizar_producto(pid,codigo,nombre,descripcion,categoria_id,precio_costo,precio_venta,stock,stock_min,unidad):
    conn=get_conn()
    try:
        conn.execute("UPDATE productos SET codigo=?,nombre=?,descripcion=?,categoria_id=?,precio_costo=?,precio_venta=?,stock=?,stock_min=?,unidad=? WHERE id=?",
                     (codigo,nombre,descripcion,categoria_id,precio_costo,precio_venta,stock,stock_min,unidad,pid))
        conn.commit(); return True,"OK"
    except sqlite3.IntegrityError: return False,"Código ya existe"
    finally: conn.close()

def eliminar_producto(pid):
    conn=get_conn(); conn.execute("UPDATE productos SET activo=0 WHERE id=?",(pid,)); conn.commit(); conn.close()

def ajustar_stock(pid,cantidad,tipo,motivo,usuario_id):
    conn=get_conn()
    if tipo=='entrada': conn.execute("UPDATE productos SET stock=stock+? WHERE id=?",(cantidad,pid))
    elif tipo=='salida': conn.execute("UPDATE productos SET stock=MAX(0,stock-?) WHERE id=?",(cantidad,pid))
    else: conn.execute("UPDATE productos SET stock=? WHERE id=?",(cantidad,pid))
    conn.commit(); conn.close()

def productos_stock_bajo():
    conn=get_conn(); rows=conn.execute("SELECT * FROM productos WHERE stock<=stock_min AND activo=1 ORDER BY stock").fetchall()
    conn.close(); return [dict(r) for r in rows]

def inventario_valor():
    conn=get_conn(); row=conn.execute("SELECT COALESCE(SUM(precio_costo*stock),0) as costo, COALESCE(SUM(precio_venta*stock),0) as venta FROM productos WHERE activo=1").fetchone()
    conn.close(); return dict(row)

def get_clientes(busqueda=''):
    conn=get_conn()
    q="SELECT * FROM clientes WHERE 1=1"; params=[]
    if busqueda: q+=" AND (nombre LIKE ? OR telefono LIKE ? OR nit LIKE ?)"; params+=[f'%{busqueda}%']*3
    q+=" ORDER BY nombre"
    rows=conn.execute(q,params).fetchall(); conn.close(); return [dict(r) for r in rows]

def crear_cliente(nombre,telefono='',correo='',direccion='',nit='CF'):
    conn=get_conn(); conn.execute("INSERT INTO clientes(nombre,telefono,correo,direccion,nit,creado_en) VALUES(?,?,?,?,?,?)",
                                   (nombre,telefono,correo,direccion,nit,datetime.now().isoformat())); conn.commit(); conn.close()

def actualizar_cliente(cid,nombre,telefono,correo,direccion,nit):
    conn=get_conn(); conn.execute("UPDATE clientes SET nombre=?,telefono=?,correo=?,direccion=?,nit=? WHERE id=?",(nombre,telefono,correo,direccion,nit,cid)); conn.commit(); conn.close()

def _gen_folio():
    conn=get_conn(); n=conn.execute("SELECT COUNT(*) as n FROM ventas").fetchone()['n']; conn.close()
    return f"V{datetime.now().strftime('%Y%m%d')}{(n+1):05d}"

def registrar_venta(usuario_id,cliente_id,items,subtotal,impuesto,descuento,total,metodo_pago,monto_pagado,cambio,notas=''):
    conn=get_conn(); c=conn.cursor(); folio=_gen_folio()
    c.execute("INSERT INTO ventas(folio,usuario_id,cliente_id,subtotal,impuesto,descuento,total,metodo_pago,monto_pagado,cambio,estado,notas,fecha) VALUES(?,?,?,?,?,?,?,?,?,?,'completada',?,?)",
              (folio,usuario_id,cliente_id,subtotal,impuesto,descuento,total,metodo_pago,monto_pagado,cambio,notas,datetime.now().isoformat()))
    vid=c.lastrowid
    for it in items:
        c.execute("INSERT INTO venta_items(venta_id,producto_id,nombre_snap,precio_snap,cantidad,descuento,subtotal) VALUES(?,?,?,?,?,?,?)",
                  (vid,it['id'],it['nombre'],it['precio_venta'],it['cantidad'],it.get('descuento',0),it['precio_venta']*it['cantidad']))
        c.execute("UPDATE productos SET stock=MAX(0,stock-?) WHERE id=?",(it['cantidad'],it['id']))
    conn.commit(); conn.close(); return folio,vid

def get_ventas(fecha_ini=None,fecha_fin=None,solo_activas=True,usuario_id=None):
    conn=get_conn()
    q="SELECT v.*, u.nombre as cajero, c.nombre as cliente_nombre FROM ventas v LEFT JOIN usuarios u ON v.usuario_id=u.id LEFT JOIN clientes c ON v.cliente_id=c.id WHERE 1=1"
    params=[]
    if solo_activas: q+=" AND v.estado='completada'"
    if fecha_ini: q+=" AND date(v.fecha)>=?"; params.append(fecha_ini)
    if fecha_fin: q+=" AND date(v.fecha)<=?"; params.append(fecha_fin)
    if usuario_id: q+=" AND v.usuario_id=?"; params.append(usuario_id)
    q+=" ORDER BY v.fecha DESC"
    rows=conn.execute(q,params).fetchall(); conn.close(); return [dict(r) for r in rows]

def get_venta_items(vid):
    conn=get_conn(); rows=conn.execute("SELECT * FROM venta_items WHERE venta_id=?",(vid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def anular_venta(vid,usuario_id):
    conn=get_conn()
    items=conn.execute("SELECT * FROM venta_items WHERE venta_id=?",(vid,)).fetchall()
    for it in items: conn.execute("UPDATE productos SET stock=stock+? WHERE id=?",(it['cantidad'],it['producto_id']))
    conn.execute("UPDATE ventas SET estado='anulada' WHERE id=?",(vid,)); conn.commit(); conn.close()

def registrar_gasto(concepto,categoria,monto,usuario_id,notas=''):
    conn=get_conn(); conn.execute("INSERT INTO gastos(concepto,categoria,monto,usuario_id,fecha,notas) VALUES(?,?,?,?,?,?)",
                                   (concepto,categoria,monto,usuario_id,datetime.now().isoformat(),notas)); conn.commit(); conn.close()

def get_gastos(fecha_ini=None,fecha_fin=None):
    conn=get_conn(); q="SELECT g.*, u.nombre as usuario FROM gastos g LEFT JOIN usuarios u ON g.usuario_id=u.id WHERE 1=1"; params=[]
    if fecha_ini: q+=" AND date(g.fecha)>=?"; params.append(fecha_ini)
    if fecha_fin: q+=" AND date(g.fecha)<=?"; params.append(fecha_fin)
    q+=" ORDER BY g.fecha DESC"; rows=conn.execute(q,params).fetchall(); conn.close(); return [dict(r) for r in rows]

def eliminar_gasto(gid):
    conn=get_conn(); conn.execute("DELETE FROM gastos WHERE id=?",(gid,)); conn.commit(); conn.close()

def registrar_fiado(usuario_id,cliente_id,items,subtotal,impuesto,descuento,total,notas=''):
    conn=get_conn(); c=conn.cursor()
    c.execute("INSERT INTO fiados(cliente_id,usuario_id,subtotal,impuesto,descuento,total,pagado,estado,notas,fecha) VALUES(?,?,?,?,?,?,0,'pendiente',?,?)",
              (cliente_id,usuario_id,subtotal,impuesto,descuento,total,notas,datetime.now().isoformat()))
    fid=c.lastrowid
    for it in items:
        c.execute("INSERT INTO fiado_items(fiado_id,producto_id,nombre_snap,precio_snap,cantidad,subtotal) VALUES(?,?,?,?,?,?)",
                  (fid,it['id'],it['nombre'],it['precio_venta'],it['cantidad'],it['precio_venta']*it['cantidad']))
        c.execute("UPDATE productos SET stock=MAX(0,stock-?) WHERE id=?",(it['cantidad'],it['id']))
    conn.commit(); conn.close(); return fid

def get_fiados(estado=None,cliente_id=None):
    conn=get_conn()
    q="SELECT f.*, c.nombre as cliente_nombre, u.nombre as cajero FROM fiados f LEFT JOIN clientes c ON f.cliente_id=c.id LEFT JOIN usuarios u ON f.usuario_id=u.id WHERE 1=1"; params=[]
    if estado: q+=" AND f.estado=?"; params.append(estado)
    if cliente_id: q+=" AND f.cliente_id=?"; params.append(cliente_id)
    q+=" ORDER BY f.fecha DESC"; rows=conn.execute(q,params).fetchall(); conn.close(); return [dict(r) for r in rows]

def get_fiado_items(fid):
    conn=get_conn(); rows=conn.execute("SELECT * FROM fiado_items WHERE fiado_id=?",(fid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def get_fiado_pagos(fid):
    conn=get_conn(); rows=conn.execute("SELECT fp.*, u.nombre as cajero FROM fiado_pagos fp LEFT JOIN usuarios u ON fp.usuario_id=u.id WHERE fp.fiado_id=? ORDER BY fp.fecha",(fid,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def registrar_pago_fiado(fiado_id,monto,usuario_id,notas=''):
    conn=get_conn(); c=conn.cursor()
    c.execute("INSERT INTO fiado_pagos(fiado_id,monto,usuario_id,fecha,notas) VALUES(?,?,?,?,?)",(fiado_id,monto,usuario_id,datetime.now().isoformat(),notas))
    c.execute("UPDATE fiados SET pagado=pagado+? WHERE id=?",(monto,fiado_id))
    row=c.execute("SELECT total,pagado FROM fiados WHERE id=?",(fiado_id,)).fetchone()
    if row and row['pagado']>=row['total']:
        c.execute("UPDATE fiados SET estado='cancelado' WHERE id=?",(fiado_id,))
        frow=c.execute("SELECT * FROM fiados WHERE id=?",(fiado_id,)).fetchone()
        folio=f"F{datetime.now().strftime('%Y%m%d')}{fiado_id:05d}"
        c.execute("INSERT INTO ventas(folio,usuario_id,cliente_id,subtotal,impuesto,descuento,total,metodo_pago,monto_pagado,cambio,estado,notas,fecha) VALUES(?,?,?,?,?,?,?,'fiado',?,0,'completada',?,?)",
                  (folio,frow['usuario_id'],frow['cliente_id'],frow['subtotal'],frow['impuesto'],frow['descuento'],frow['total'],frow['total'],f"Fiado #{fiado_id}",datetime.now().isoformat()))
        vid=c.lastrowid
        for it in c.execute("SELECT * FROM fiado_items WHERE fiado_id=?",(fiado_id,)).fetchall():
            c.execute("INSERT INTO venta_items(venta_id,producto_id,nombre_snap,precio_snap,cantidad,descuento,subtotal) VALUES(?,?,?,?,?,0,?)",(vid,it['producto_id'],it['nombre_snap'],it['precio_snap'],it['cantidad'],it['subtotal']))
    conn.commit(); conn.close()

def deuda_cliente(cliente_id):
    conn=get_conn(); row=conn.execute("SELECT COALESCE(SUM(total-pagado),0) as deuda FROM fiados WHERE cliente_id=? AND estado='pendiente'",(cliente_id,)).fetchone()
    conn.close(); return row['deuda'] if row else 0

def stats_hoy():
    hoy=date.today().strftime('%Y-%m-%d'); conn=get_conn()
    v=conn.execute("SELECT COUNT(*) as num, COALESCE(SUM(total),0) as total FROM ventas WHERE date(fecha)=? AND estado='completada'",(hoy,)).fetchone()
    g=conn.execute("SELECT COALESCE(SUM(monto),0) as g FROM gastos WHERE date(fecha)=?",(hoy,)).fetchone()
    b=conn.execute("SELECT COUNT(*) as n FROM productos WHERE stock<=stock_min AND activo=1").fetchone()
    f=conn.execute("SELECT COUNT(*) as n FROM fiados WHERE estado='pendiente'").fetchone()
    conn.close()
    return {'ventas_num':v['num'],'ventas_total':v['total'],'gasto_hoy':g['g'],'utilidad':v['total']-g['g'],'stock_bajo':b['n'],'fiados_pendientes':f['n']}

def ventas_por_dia(dias=30):
    conn=get_conn(); rows=conn.execute("SELECT date(fecha) as dia, COUNT(*) as num, SUM(total) as total FROM ventas WHERE estado='completada' AND date(fecha)>=date('now',?) GROUP BY dia ORDER BY dia",(f'-{dias} days',)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def top_productos(limite=8,dias=30):
    conn=get_conn(); rows=conn.execute("SELECT vi.nombre_snap as nombre, SUM(vi.cantidad) as qty, SUM(vi.subtotal) as total FROM venta_items vi JOIN ventas v ON vi.venta_id=v.id WHERE v.estado='completada' AND date(v.fecha)>=date('now',?) GROUP BY vi.nombre_snap ORDER BY qty DESC LIMIT ?",(f'-{dias} days',limite)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def corte_diario(fecha=None):
    fecha=fecha or date.today().strftime('%Y-%m-%d'); conn=get_conn()
    v=conn.execute("SELECT COUNT(*) as num, COALESCE(SUM(total),0) as total, COALESCE(SUM(impuesto),0) as impuesto, COALESCE(SUM(descuento),0) as descuento FROM ventas WHERE date(fecha)=? AND estado='completada'",(fecha,)).fetchone()
    g=conn.execute("SELECT COALESCE(SUM(monto),0) as total, COUNT(*) as num FROM gastos WHERE date(fecha)=?",(fecha,)).fetchone()
    mt=conn.execute("SELECT metodo_pago, COUNT(*) as num, SUM(total) as total FROM ventas WHERE date(fecha)=? AND estado='completada' GROUP BY metodo_pago",(fecha,)).fetchall()
    dv=conn.execute("SELECT v.folio,v.fecha,v.total,v.metodo_pago,u.nombre as cajero FROM ventas v LEFT JOIN usuarios u ON v.usuario_id=u.id WHERE date(v.fecha)=? AND v.estado='completada' ORDER BY v.fecha",(fecha,)).fetchall()
    dg=conn.execute("SELECT * FROM gastos WHERE date(fecha)=? ORDER BY fecha",(fecha,)).fetchall()
    conn.close()
    return {'fecha':fecha,'ventas':dict(v),'gastos':dict(g),'metodos':[dict(r) for r in mt],'detalle_ventas':[dict(r) for r in dv],'detalle_gastos':[dict(r) for r in dg]}
