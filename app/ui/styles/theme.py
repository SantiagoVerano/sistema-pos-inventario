"""
Módulo de Estilos Visuales y Tema QSS (app/ui/styles/theme.py)

Responsabilidad Arquitectónica:
-------------------------------
Definir la paleta de colores, tipografías y reglas de estilo CSS para Qt (QSS).
Proporciona una interfaz moderna, limpia, oscura y empresarial para todo el sistema POS.
"""

PALETA = {
    "bg_principal": "#121824",      # Fondo oscuro profundo
    "bg_secundario": "#1a2234",     # Fondo de tarjetas y paneles
    "bg_terciario": "#242e42",      # Fondo de inputs y hover
    "bg_sidebar": "#0d131f",        # Fondo de barra lateral
    "accent_primary": "#00a884",    # Verde esmeralda POS principal
    "accent_hover": "#00c49a",      # Hover del botón de cobro
    "accent_blue": "#2563eb",       # Azul para acciones primarias
    "accent_blue_hover": "#3b82f6",
    "text_primary": "#ffffff",      # Texto blanco de alto contraste
    "text_secondary": "#94a3b8",    # Texto gris tenue informativo
    "text_muted": "#64748b",        # Texto gris oscuro
    "border": "#334155",            # Bordes sutiles
    "danger": "#ef4444",            # Rojo de alerta / anulación
    "danger_hover": "#dc2626",
    "warning": "#f59e0b",           # Amarillo de advertencia de stock
    "success": "#10b981",           # Verde de éxito
}

TEMA_GLOBAL_QSS = f"""
/* ==========================================================================
   CONFIGURACIÓN BASE
   ========================================================================== */
QWidget {{
    background-color: {PALETA['bg_principal']};
    color: {PALETA['text_primary']};
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}}

/* ==========================================================================
   INPUTS Y CAMPOS DE TEXTO
   ========================================================================== */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
    background-color: {PALETA['bg_terciario']};
    color: {PALETA['text_primary']};
    border: 1px solid {PALETA['border']};
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: {PALETA['accent_primary']};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
    border: 1px solid {PALETA['accent_primary']};
    background-color: {PALETA['bg_secundario']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

/* ==========================================================================
   BOTONES
   ========================================================================== */
QPushButton {{
    background-color: {PALETA['bg_terciario']};
    color: {PALETA['text_primary']};
    border: 1px solid {PALETA['border']};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {PALETA['border']};
    border-color: {PALETA['text_secondary']};
}}

QPushButton:pressed {{
    background-color: {PALETA['bg_secundario']};
}}

QPushButton:disabled {{
    background-color: {PALETA['bg_principal']};
    color: {PALETA['text_muted']};
    border-color: {PALETA['bg_terciario']};
}}

/* Botón de Acción Principal (Verde / Cobrar) */
QPushButton#btn_primary, QPushButton[tipo="primary"] {{
    background-color: {PALETA['accent_primary']};
    color: #ffffff;
    border: none;
    font-size: 14px;
    font-weight: bold;
}}

QPushButton#btn_primary:hover, QPushButton[tipo="primary"]:hover {{
    background-color: {PALETA['accent_hover']};
}}

/* Botón Azul */
QPushButton#btn_blue, QPushButton[tipo="blue"] {{
    background-color: {PALETA['accent_blue']};
    color: #ffffff;
    border: none;
}}

QPushButton#btn_blue:hover, QPushButton[tipo="blue"]:hover {{
    background-color: {PALETA['accent_blue_hover']};
}}

/* Botón de Peligro / Anulación */
QPushButton#btn_danger, QPushButton[tipo="danger"] {{
    background-color: {PALETA['danger']};
    color: #ffffff;
    border: none;
}}

QPushButton#btn_danger:hover, QPushButton[tipo="danger"]:hover {{
    background-color: {PALETA['danger_hover']};
}}

/* ==========================================================================
   TABLAS (QTableWidget / QTableView)
   ========================================================================== */
QTableWidget, QTableView {{
    background-color: {PALETA['bg_secundario']};
    border: 1px solid {PALETA['border']};
    border-radius: 8px;
    gridline-color: {PALETA['border']};
    selection-background-color: {PALETA['bg_terciario']};
    selection-color: {PALETA['accent_primary']};
}}

QHeaderView::section {{
    background-color: {PALETA['bg_principal']};
    color: {PALETA['text_secondary']};
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid {PALETA['border']};
    font-weight: bold;
    text-transform: uppercase;
    font-size: 11px;
}}

QTableWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {PALETA['border']};
}}

QTableWidget::item:selected {{
    background-color: {PALETA['bg_terciario']};
    color: {PALETA['text_primary']};
    border-left: 3px solid {PALETA['accent_primary']};
}}

/* ==========================================================================
   PANELES Y TARJETAS (Frames)
   ========================================================================== */
QFrame#card, QFrame[tipo="card"] {{
    background-color: {PALETA['bg_secundario']};
    border: 1px solid {PALETA['border']};
    border-radius: 8px;
    padding: 16px;
}}

/* ==========================================================================
   BARRA DE NAVEGACIÓN LATERAL (Sidebar)
   ========================================================================== */
QFrame#sidebar {{
    background-color: {PALETA['bg_sidebar']};
    border-right: 1px solid {PALETA['border']};
}}

QPushButton#btn_nav {{
    background-color: transparent;
    color: {PALETA['text_secondary']};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
}}

QPushButton#btn_nav:hover {{
    background-color: {PALETA['bg_terciario']};
    color: {PALETA['text_primary']};
}}

QPushButton#btn_nav:checked, QPushButton#btn_nav[activo="true"] {{
    background-color: {PALETA['bg_terciario']};
    color: {PALETA['accent_primary']};
    font-weight: bold;
    border-left: 4px solid {PALETA['accent_primary']};
}}

/* ==========================================================================
   SCROLLBARS
   ========================================================================== */
QScrollBar:vertical {{
    background: {PALETA['bg_principal']};
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {PALETA['border']};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {PALETA['text_muted']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""
