# ============================================================
#  CONFIGURACIÓN — edita solo este archivo
# ============================================================
TIENDA = {
    "nombre":    "Mi Tienda",
    "slogan":    "Calidad y servicio",
    "telefono":  "+502 0000-0000",
    "direccion": "Ciudad, País",
    "moneda":    "Q",
    "impuesto":  0,
    "logo":      "assets/logo.png",
}

FIADO = {
    "maximo_por_cliente": 500,
}

DB_PATH = "pos_data.db"

TEMA = {
    "bg":       "#0F0F13",
    "surface":  "#1A1A24",
    "surface2": "#252535",
    "border":   "#2E2E45",
    "accent":   "#6C63FF",
    "text":     "#E8E8F0",
    "text_dim": "#7070A0",
    "success":  "#43D9AD",
    "warning":  "#FFB347",
    "danger":   "#FF6584",
}

# ── Cargar overrides locales ──────────────────────────────────
# Si existe config_local.json, sus valores sobreescriben los de arriba
import json, os

def _cfg_path():
    try:
        from android.storage import app_storage_path
        return os.path.join(app_storage_path(), 'config_local.json')
    except Exception:
        return 'config_local.json'

try:
    with open(_cfg_path(), 'r', encoding='utf-8') as _f:
        _local = json.load(_f)
    # Aplicar overrides de TIENDA
    for _k, _v in _local.get('tienda', {}).items():
        if _k in TIENDA:
            TIENDA[_k] = _v
    # Aplicar overrides de TEMA
    for _k, _v in _local.get('tema', {}).items():
        if _k in TEMA:
            TEMA[_k] = _v
    # Aplicar overrides de FIADO
    for _k, _v in _local.get('fiado', {}).items():
        if _k in FIADO:
            FIADO[_k] = _v
except Exception:
    pass
