import sqlite3
import datetime
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, BooleanProperty, StringProperty, NumericProperty
from kivy.factory import Factory
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.clock import Clock

# --- BASE DE DATOS LOCAL (VERSIÓN 32 - AI MAX) ---
DB_NAME = "dinerek_pro_v32_max.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS tarjetas (id INTEGER PRIMARY KEY, banco TEXT, digitos TEXT, limite REAL, corte TEXT, pago TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS ingresos (id INTEGER PRIMARY KEY, tipo TEXT, monto REAL, frecuencia TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS deudas (id INTEGER PRIMARY KEY, concepto TEXT, tipo_acreedor TEXT, acreedor TEXT, monto_original REAL, cuota REAL, plazo INTEGER, total REAL, frecuencia TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS abonos (id INTEGER PRIMARY KEY, deuda_id INTEGER, monto REAL, fecha TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS fijos (id INTEGER PRIMARY KEY, concepto TEXT, monto REAL, frecuencia TEXT, fecha_pago TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS canasta (id INTEGER PRIMARY KEY, producto TEXT, precio REAL)''')
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error BD:", e)

def parse_float(val):
    try:
        if not val: return 0.0
        return float(str(val).replace(',', ''))
    except:
        return 0.0

def get_next_date(day_str, today):
    try:
        d = int(day_str)
        if d < today.day:
            if today.month == 12:
                return datetime.date(today.year + 1, 1, d)
            else:
                return datetime.date(today.year, today.month + 1, d)
        else:
            return datetime.date(today.year, today.month, d)
    except:
        return today

# --- COMPONENTES VISUALES AVANZADOS ---

class DonutChart(Widget):
    pct_fijos = NumericProperty(0.0)
    pct_deudas = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas,
                  pct_fijos=self.update_canvas, pct_deudas=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            cx, cy = self.center_x, self.center_y
            r = min(self.width, self.height) / 2 - dp(8)
            thickness = dp(14)

            Color(rgba=get_color_from_hex('#10B981')) # Libre (Verde)
            Line(circle=(cx, cy, r), width=thickness)

            ang_f = min(360, self.pct_fijos * 360)
            ang_d = min(360 - ang_f, self.pct_deudas * 360)

            if ang_f > 0:
                Color(rgba=get_color_from_hex('#EF4444')) # Fijos (Rojo)
                Line(circle=(cx, cy, r, 0, ang_f), width=thickness)

            if ang_d > 0:
                Color(rgba=get_color_from_hex('#F59E0B')) # Deudas (Naranja)
                Line(circle=(cx, cy, r, ang_f, ang_f + ang_d), width=thickness)

class ProgressBarWidget(Widget):
    porcentaje = NumericProperty(0.0)
    color_barra = ListProperty(get_color_from_hex('#10B981'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, 
                  porcentaje=self.update_canvas, color_barra=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(rgba=get_color_from_hex('#334155'))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])
            w_llena = self.width * max(0.0, min(1.0, self.porcentaje))
            if w_llena > 0:
                Color(*self.color_barra)
                r = [dp(5)] if self.porcentaje >= 0.99 else [dp(5), 0, 0, dp(5)]
                RoundedRectangle(pos=self.pos, size=(w_llena, self.height), radius=r)

class VectorIcon(Widget):
    icon_type = StringProperty('home')
    color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, icon_type=self.update_canvas, color=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(*self.color)
            cx, cy = self.center_x, self.center_y
            x, y, w, h = self.x, self.y, self.width, self.height
            t, r = self.top, self.right

            if self.icon_type == 'home':
                Line(points=[cx, t, x+w*0.1, y+h*0.5, x+w*0.1, y, r-w*0.1, y, r-w*0.1, y+h*0.5], close=True, width=dp(1.5), joint='round')
            elif self.icon_type == 'wallet':
                Line(rounded_rectangle=(x, y + h*0.2, w, h*0.6, dp(3)), width=dp(1.5))
                Line(circle=(cx, cy, dp(2.5)), width=dp(1.5))
            elif self.icon_type == 'card':
                Line(rounded_rectangle=(x, y + h*0.2, w, h*0.6, dp(4)), width=dp(1.5))
                Line(points=[x, y + h*0.6, r, y + h*0.6], width=dp(1.5))
            elif self.icon_type == 'chart':
                Line(rounded_rectangle=(x + w*0.1, y, w*0.2, h*0.5, dp(2)), width=dp(1.5))
                Line(rounded_rectangle=(x + w*0.4, y, w*0.2, h*0.9, dp(2)), width=dp(1.5))
                Line(rounded_rectangle=(x + w*0.7, y, w*0.2, h*0.7, dp(2)), width=dp(1.5))
            elif self.icon_type == 'menu':
                Line(rounded_rectangle=(x, y + h*0.55, w*0.4, h*0.4, dp(3)), width=dp(1.5))
                Line(rounded_rectangle=(x + w*0.6, y + h*0.55, w*0.4, h*0.4, dp(3)), width=dp(1.5))
                Line(rounded_rectangle=(x, y, w*0.4, h*0.4, dp(3)), width=dp(1.5))
                Line(rounded_rectangle=(x + w*0.6, y, w*0.4, h*0.4, dp(3)), width=dp(1.5))
            elif self.icon_type == 'theme':
                Line(circle=(cx, cy, w*0.25), width=dp(1.5))
                Line(points=[cx, y, cx, y+h*0.15], width=dp(1.5))
                Line(points=[cx, t, cx, t-h*0.15], width=dp(1.5))
                Line(points=[x, cy, x+w*0.15, cy], width=dp(1.5))
                Line(points=[r, cy, r-w*0.15, cy], width=dp(1.5))
            elif self.icon_type == 'logo_pro':
                Line(rounded_rectangle=(x+w*0.2, y+h*0.2, w*0.6, h*0.6, dp(5)), width=dp(2.5))
                Line(points=[cx, y+h*0.4, cx, y+h*0.8], width=dp(2.5))
                Line(points=[x+w*0.3, y+h*0.6, r-w*0.3, y+h*0.6], width=dp(2.5))

class NavBtn(ButtonBehavior, BoxLayout):
    text = StringProperty('')
    icon_type = StringProperty('home')
    active = BooleanProperty(False)

class MenuCardBtn(ButtonBehavior, BoxLayout):
    icon_type = StringProperty('card')
    text_title = StringProperty('')
    text_sub = StringProperty('')

class PremiumCard(BoxLayout): pass
class ModernInput(TextInput): pass
class ModernSpinner(Spinner): pass
class ActionBtn(Button): pass

class AbonoCard(BoxLayout):
    info_text = StringProperty('')
    texto_progreso = StringProperty('')
    deuda_id = NumericProperty(0)
    cuota_sugerida = NumericProperty(0)
    progreso_pct = NumericProperty(0.0)

class FijoCard(BoxLayout):
    concepto = StringProperty('')
    detalle_text = StringProperty('')
    monto_text = StringProperty('')
    fijo_id = NumericProperty(0)

Factory.register('DonutChart', cls=DonutChart)
Factory.register('ProgressBarWidget', cls=ProgressBarWidget)
Factory.register('VectorIcon', cls=VectorIcon)
Factory.register('AbonoCard', cls=AbonoCard)
Factory.register('FijoCard', cls=FijoCard)
Factory.register('PremiumCard', cls=PremiumCard)
Factory.register('ModernInput', cls=ModernInput)
Factory.register('ModernSpinner', cls=ModernSpinner)
Factory.register('ActionBtn', cls=ActionBtn)
Factory.register('NavBtn', cls=NavBtn)
Factory.register('MenuCardBtn', cls=MenuCardBtn)

# --- INTERFAZ GRÁFICA KV ---
KV = '''
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import get_color_from_hex kivy.utils.get_color_from_hex

<AbonoCard>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(230)
    padding: dp(15)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: app.theme_card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(15)]
    Label:
        text: root.info_text
        markup: True
        color: app.theme_text
        halign: 'left'
        valign: 'top'
        text_size: self.size
        size_hint_y: 0.6
    
    # TEXTO DE EN QUÉ ABONO VA
    BoxLayout:
        size_hint_y: None
        height: dp(25)
        Label:
            text: root.texto_progreso
            markup: True
            color: get_color_from_hex('#0EA5E9')
            bold: True
            font_size: sp(14)
            halign: 'center'
            valign: 'middle'
            text_size: self.size

    # BARRA DE PROGRESO DEL PAGO
    ProgressBarWidget:
        porcentaje: root.progreso_pct
        color_barra: get_color_from_hex('#0EA5E9')
        size_hint_y: None
        height: dp(8)

    BoxLayout:
        size_hint_y: None
        height: dp(45)
        spacing: dp(10)
        TextInput:
            id: input_abono
            text: str(root.cuota_sugerida)
            input_filter: 'float'
            multiline: False
            background_color: app.theme_input_bg
            foreground_color: app.theme_input_text
            padding_y: [dp(12), 0]
            padding_x: [dp(10), dp(10)]
            font_size: sp(14)
        Button:
            text: 'Abonar'
            size_hint_x: 0.6
            bold: True
            background_normal: ''
            background_color: 0,0,0,0
            color: 1,1,1,1
            canvas.before:
                Color:
                    rgba: get_color_from_hex('#10B981')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(8)]
            on_release: app.hacer_abono_custom(root.deuda_id, input_abono.text)

<FijoCard>:
    size_hint_y: None
    height: dp(65)
    padding: dp(10)
    canvas.before:
        Color:
            rgba: app.theme_card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: root.concepto
            color: app.theme_text
            bold: True
            halign: 'left'
            valign: 'bottom'
            text_size: self.size
        Label:
            text: root.detalle_text
            color: app.theme_text_muted
            font_size: sp(11)
            halign: 'left'
            valign: 'top'
            text_size: self.size
    Label:
        text: root.monto_text
        color: app.theme_text
        halign: 'right'
        valign: 'middle'
        text_size: self.size
    Button:
        text: 'X'
        size_hint_x: None
        width: dp(40)
        background_normal: ''
        background_color: 0.9, 0.2, 0.2, 1
        bold: True
        on_release: app.eliminar_fijo(root.fijo_id)

<NavBtn>:
    orientation: 'vertical'
    padding: [0, dp(8), 0, dp(5)]
    spacing: dp(2)
    VectorIcon:
        icon_type: root.icon_type
        color: app.theme_accent if root.active else app.theme_text_muted
        size_hint: None, None
        size: dp(22), dp(22)
        pos_hint: {'center_x': 0.5}
    Label:
        text: root.text
        font_size: sp(10)
        bold: True
        color: app.theme_accent if root.active else app.theme_text_muted
        size_hint_y: None
        height: dp(15)

<MenuCardBtn>:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: app.theme_card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(20)]
    VectorIcon:
        icon_type: root.icon_type
        color: app.theme_accent
        size_hint: None, None
        size: dp(35), dp(35)
        pos_hint: {'center_x': 0.5}
    Label:
        text: root.text_title
        font_size: sp(14)
        bold: True
        color: app.theme_text
        size_hint_y: None
        height: dp(20)
    Label:
        text: root.text_sub
        font_size: sp(11)
        color: app.theme_text_muted
        size_hint_y: None
        height: dp(15)

<PremiumCard>:
    padding: dp(15)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: app.theme_card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(15)]

<ModernInput>:
    background_color: app.theme_input_bg
    foreground_color: app.theme_input_text
    hint_text_color: app.theme_text_muted
    cursor_color: app.theme_accent
    multiline: False
    size_hint_y: None
    height: dp(55)
    font_size: sp(15)
    padding_y: [dp(16), 0]
    padding_x: [dp(15), dp(15)]
    canvas.after:
        Color:
            rgba: app.theme_accent
        Line:
            rounded_rectangle: (self.pos[0], self.pos[1], self.size[0], self.size[1], dp(8))
            width: dp(1.5)

<ModernSpinner>:
    background_normal: ''
    background_color: app.theme_input_bg
    color: app.theme_input_text
    size_hint_y: None
    height: dp(55)
    font_size: sp(15)
    text_size: self.width - dp(40), None
    halign: 'left'
    valign: 'middle'
    padding_x: dp(15)
    canvas.after:
        Color:
            rgba: app.theme_accent
        Line:
            points: [self.right-dp(25), self.center_y+dp(2), self.right-dp(20), self.center_y-dp(3), self.right-dp(15), self.center_y+dp(2)]
            width: dp(1.5)

<SpinnerOption>:
    background_normal: ''
    background_color: app.theme_card
    color: app.theme_text
    font_size: sp(15)

<ActionBtn>:
    background_normal: ''
    background_color: 0, 0, 0, 0
    color: 1, 1, 1, 1
    bold: True
    font_size: sp(16)
    canvas.before:
        Color:
            rgba: app.theme_accent
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

BoxLayout:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: app.theme_bg
        Rectangle:
            pos: self.pos
            size: self.size
    
    # HEADER SUPERIOR
    BoxLayout:
        id: header_top
        opacity: 0 # Oculto en splash
        disabled: True
        size_hint_y: None
        height: dp(60)
        padding: [dp(20), dp(10), dp(20), dp(10)]
        canvas.before:
            Color:
                rgba: app.theme_card
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: 'Dinerek[b]Max[/b]'
            markup: True
            font_size: sp(20)
            color: app.theme_text
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        Button:
            size_hint_x: None
            width: dp(40)
            background_normal: ''
            background_color: 0, 0, 0, 0
            on_release: app.toggle_theme()
            VectorIcon:
                icon_type: 'theme'
                color: app.theme_accent
                size_hint: None, None
                size: dp(22), dp(22)
                pos: self.parent.center_x - dp(11), self.parent.center_y - dp(11)

    ScreenManager:
        id: sm
        
        # ==========================================
        #           PANTALLA DE INICIO (SPLASH)
        # ==========================================
        Screen:
            name: 'splash'
            BoxLayout:
                orientation: 'vertical'
                padding: dp(40)
                spacing: dp(20)
                canvas.before:
                    Color:
                        rgba: app.theme_bg
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Widget:
                VectorIcon:
                    icon_type: 'logo_pro'
                    color: app.theme_accent
                    size_hint: None, None
                    size: dp(100), dp(100)
                    pos_hint: {'center_x': 0.5}
                Label:
                    text: 'Dinerek[b]Max[/b]'
                    markup: True
                    font_size: sp(40)
                    color: app.theme_text
                    size_hint_y: None
                    height: dp(50)
                Label:
                    id: lbl_loading_text
                    text: 'Iniciando módulos de inteligencia...'
                    font_size: sp(14)
                    color: app.theme_text_muted
                    size_hint_y: None
                    height: dp(30)
                ProgressBarWidget:
                    id: splash_progress
                    porcentaje: 0.0
                    color_barra: get_color_from_hex('#0EA5E9')
                    size_hint_y: None
                    height: dp(8)
                Widget:

        # ==========================================
        #           PANTALLA HOME (DASHBOARD)
        # ==========================================
        Screen:
            name: 'home'
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(15)
                    spacing: dp(15)
                    size_hint_y: None
                    height: self.minimum_height
                    
                    # 1. CALENDARIO Y AHORROS
                    PremiumCard:
                        orientation: 'vertical'
                        size_hint_y: None
                        height: dp(130)
                        canvas.before:
                            Color:
                                rgba: get_color_from_hex('#0284C7')
                            RoundedRectangle:
                                pos: self.pos
                                size: self.size
                                radius: [dp(15)]
                        BoxLayout:
                            size_hint_y: 0.2
                            Label:
                                id: lbl_fecha
                                text: 'Cargando fecha...'
                                color: 1, 1, 1, 0.8
                                font_size: sp(13)
                                bold: True
                                text_size: self.size
                                halign: 'left'
                        BoxLayout:
                            size_hint_y: 0.6
                            orientation: 'vertical'
                            Label:
                                text: 'AHORRO TOTAL ACUMULADO'
                                color: 1, 1, 1, 0.9
                                font_size: sp(11)
                                text_size: self.size
                                halign: 'left'
                                valign: 'bottom'
                            Label:
                                id: h_ahorro_total
                                text: '$0.00'
                                color: 1, 1, 1, 1
                                font_size: sp(32)
                                bold: True
                                text_size: self.size
                                halign: 'left'
                                valign: 'middle'
                        BoxLayout:
                            size_hint_y: 0.2
                            Label:
                                id: h_ahorro_mes
                                text: 'Meta de ahorro este mes: $0.00'
                                color: 1, 1, 1, 0.8
                                font_size: sp(12)
                                text_size: self.size
                                halign: 'left'
                                valign: 'middle'

                    # NUEVO: PROYECCIÓN A 12 MESES
                    PremiumCard:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: dp(70)
                        canvas.before:
                            Color:
                                rgba: app.theme_card
                            RoundedRectangle:
                                pos: self.pos
                                size: self.size
                                radius: [dp(12)]
                            Color:
                                rgba: get_color_from_hex('#8B5CF6')
                            RoundedRectangle:
                                pos: self.pos[0], self.pos[1]
                                size: dp(6), self.size[1]
                                radius: [dp(12), 0, 0, dp(12)]
                        BoxLayout:
                            orientation: 'vertical'
                            padding: [dp(10), 0]
                            Label:
                                text: 'PROYECCIÓN ANUAL (Si ahorras lo libre)'
                                color: app.theme_text_muted
                                font_size: sp(11)
                                bold: True
                                text_size: self.size
                                halign: 'left'
                                valign: 'bottom'
                            Label:
                                id: h_proyeccion_anual
                                text: 'Calculando...'
                                color: get_color_from_hex('#8B5CF6')
                                font_size: sp(20)
                                bold: True
                                text_size: self.size
                                halign: 'left'
                                valign: 'top'

                    # 2. BALANCE DEL MES (Gráfica)
                    PremiumCard:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: dp(160)
                        BoxLayout:
                            orientation: 'vertical'
                            size_hint_x: 0.6
                            Label:
                                text: 'DINERO LIBRE ESTE MES'
                                color: app.theme_text_muted
                                font_size: sp(12)
                                bold: True
                                text_size: self.size
                                halign: 'left'
                                valign: 'top'
                                size_hint_y: 0.2
                            Label:
                                id: home_balance
                                text: '$0.00'
                                color: app.theme_text
                                font_size: sp(28)
                                bold: True
                                text_size: self.size
                                halign: 'left'
                                valign: 'middle'
                                size_hint_y: 0.4
                            Label:
                                text: ' [color=#10B981]■ Libre[/color]\\n [color=#EF4444]■ Fijos[/color]  [color=#F59E0B]■ Deudas[/color]'
                                markup: True
                                font_size: sp(11)
                                text_size: self.size
                                halign: 'left'
                                valign: 'bottom'
                                size_hint_y: 0.4
                        BoxLayout:
                            size_hint_x: 0.4
                            padding: dp(5)
                            DonutChart:
                                id: donut_grafica
                                pct_fijos: 0.0
                                pct_deudas: 0.0

                    # 3. MEGA-DESGLOSE FINANCIERO
                    Label:
                        text: 'RESUMEN FINANCIERO'
                        color: app.theme_text
                        bold: True
                        font_size: sp(14)
                        size_hint_y: None
                        height: dp(20)
                        text_size: self.size
                        halign: 'left'

                    GridLayout:
                        cols: 2
                        spacing: dp(10)
                        size_hint_y: None
                        height: dp(200)

                        # INGRESOS
                        PremiumCard:
                            orientation: 'vertical'
                            padding: dp(10)
                            canvas.before:
                                Color: 
                                    rgba: get_color_from_hex('#10B981')
                                RoundedRectangle: 
                                    pos: self.pos[0], self.pos[1]
                                    size: dp(4), self.size[1]
                                    radius: [dp(15), 0, 0, dp(15)]
                            Label: 
                                text: 'INGRESOS'
                                color: get_color_from_hex('#10B981')
                                bold: True
                                font_size: sp(12)
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.3
                            Label: 
                                id: h_ing_mes
                                text: 'Mes: $0'
                                color: app.theme_text
                                font_size: sp(15)
                                bold: True
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.4
                            Label: 
                                id: h_ing_sem
                                text: 'Sem: $0'
                                color: app.theme_text_muted
                                font_size: sp(12)
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.3

                        # FIJOS
                        PremiumCard:
                            orientation: 'vertical'
                            padding: dp(10)
                            canvas.before:
                                Color: 
                                    rgba: get_color_from_hex('#EF4444')
                                RoundedRectangle: 
                                    pos: self.pos[0], self.pos[1]
                                    size: dp(4), self.size[1]
                                    radius: [dp(15), 0, 0, dp(15)]
                            Label: 
                                text: 'GASTOS FIJOS'
                                color: get_color_from_hex('#EF4444')
                                bold: True
                                font_size: sp(12)
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.3
                            Label: 
                                id: h_fij_mes
                                text: 'Mes: $0'
                                color: app.theme_text
                                font_size: sp(15)
                                bold: True
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.4
                            Label: 
                                id: h_fij_sem
                                text: 'Sem: $0'
                                color: app.theme_text_muted
                                font_size: sp(12)
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.3
                            
                        # DEUDA (CUOTAS)
                        PremiumCard:
                            orientation: 'vertical'
                            padding: dp(10)
                            canvas.before:
                                Color: 
                                    rgba: get_color_from_hex('#F59E0B')
                                RoundedRectangle: 
                                    pos: self.pos[0], self.pos[1]
                                    size: dp(4), self.size[1]
                                    radius: [dp(15), 0, 0, dp(15)]
                            Label: 
                                text: 'PAGOS DEUDA'
                                color: get_color_from_hex('#F59E0B')
                                bold: True
                                font_size: sp(12)
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.3
                            Label: 
                                id: h_deu_mes
                                text: 'Mes: $0'
                                color: app.theme_text
                                font_size: sp(15)
                                bold: True
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.4
                            Label: 
                                id: h_deu_sem
                                text: 'Sem: $0'
                                color: app.theme_text_muted
                                font_size: sp(12)
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.3

                        # DEUDA (GLOBAL)
                        PremiumCard:
                            orientation: 'vertical'
                            padding: dp(10)
                            canvas.before:
                                Color: 
                                    rgba: get_color_from_hex('#8B5CF6')
                                RoundedRectangle: 
                                    pos: self.pos[0], self.pos[1]
                                    size: dp(4), self.size[1]
                                    radius: [dp(15), 0, 0, dp(15)]
                            Label: 
                                text: 'DEUDA TOTAL'
                                color: get_color_from_hex('#8B5CF6')
                                bold: True
                                font_size: sp(12)
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.3
                            Label: 
                                id: h_deuda_global
                                text: '$0'
                                color: app.theme_text
                                font_size: sp(15)
                                bold: True
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.4
                            Label: 
                                text: 'Histórica Pendiente'
                                color: app.theme_text_muted
                                font_size: sp(11)
                                text_size: self.size
                                halign: 'left'
                                size_hint_y: 0.3

                    # 4. TARJETAS REGISTRADAS (CON LÍMITE REAL ACTUALIZABLE)
                    Label:
                        text: 'CALENDARIO: PRÓXIMOS PAGOS (Tarjetas)'
                        color: app.theme_text
                        bold: True
                        font_size: sp(14)
                        size_hint_y: None
                        height: dp(30)
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'

                    ScrollView:
                        size_hint_y: None
                        height: dp(160)
                        do_scroll_x: True
                        do_scroll_y: False
                        BoxLayout:
                            id: home_tarjetas_lista
                            orientation: 'horizontal'
                            size_hint_x: None
                            width: self.minimum_width
                            spacing: dp(15)
                            padding: [0, 0, dp(15), 0]

        # ==========================================
        #           PANTALLA DEUDAS
        # ==========================================
        Screen:
            name: 'deudas'
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(20)
                    spacing: dp(15)
                    size_hint_y: None
                    height: self.minimum_height
                    
                    Label:
                        text: 'Registrar Deuda / Compra'
                        color: app.theme_text
                        bold: True
                        font_size: sp(20)
                        size_hint_y: None
                        height: dp(40)
                        text_size: self.size
                        halign: 'left'
                    
                    Label:
                        text: 'Concepto de deuda:'
                        color: app.theme_text
                        font_size: sp(13)
                        size_hint_y: None
                        height: dp(20)
                        text_size: self.size
                        halign: 'left'
                    ModernInput:
                        id: deu_concepto
                        hint_text: 'Ej. Celular, Préstamo'
                    
                    GridLayout:
                        cols: 2
                        spacing: dp(10)
                        size_hint_y: None
                        height: dp(85)
                        BoxLayout:
                            orientation: 'vertical'
                            Label:
                                text: 'A quién le debes:'
                                color: app.theme_text
                                font_size: sp(13)
                            ModernSpinner:
                                id: deu_acreedor_tipo
                                text: 'Tarjeta'
                                values: ('Tarjeta', 'Banco', 'Persona', 'Tienda')
                                on_text: app.check_deuda_tipo()
                        BoxLayout:
                            orientation: 'vertical'
                            Label:
                                text: 'Selecciona:'
                                color: app.theme_text
                                font_size: sp(13)
                            ModernSpinner:
                                id: deu_acreedor_spin
                                text: 'Selecciona Tarjeta'
                            ModernInput:
                                id: deu_acreedor_txt
                                hint_text: 'Nombre'
                                opacity: 0
                                disabled: True
                    
                    Label:
                        text: 'FORMATO DE REGISTRO'
                        color: app.theme_accent
                        bold: True
                        font_size: sp(13)
                        size_hint_y: None
                        height: dp(30)
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'

                    ModernSpinner:
                        id: deu_modo_registro
                        text: 'Cálculo por Cuotas (Meses)'
                        values: ('Cálculo por Cuotas (Meses)', 'Deuda Total Directa (Un solo pago)')
                        on_text: app.toggle_modo_deuda()
                        
                    # CAJA MODO CUOTAS
                    BoxLayout:
                        id: caja_modo_cuotas
                        orientation: 'vertical'
                        size_hint_y: None
                        height: dp(115)
                        spacing: dp(10)
                        GridLayout:
                            cols: 2
                            spacing: dp(10)
                            size_hint_y: None
                            height: dp(85)
                            BoxLayout:
                                orientation: 'vertical'
                                Label:
                                    text: 'Cuota ($):'
                                    color: app.theme_text
                                    font_size: sp(13)
                                ModernInput:
                                    id: deu_cuota
                                    hint_text: 'Ej. 500'
                                    input_filter: 'float'
                                    on_text: app.calcular_deuda_inversa()
                            BoxLayout:
                                orientation: 'vertical'
                                Label:
                                    text: 'Plazo (Pagos):'
                                    color: app.theme_text
                                    font_size: sp(13)
                                ModernInput:
                                    id: deu_plazo
                                    hint_text: 'Ej. 12'
                                    input_filter: 'int'
                                    on_text: app.calcular_deuda_inversa()
                        ModernSpinner:
                            id: deu_frecuencia
                            text: 'Mensual'
                            values: ('Semanal', 'Quincenal', 'Mensual')
                            on_text: app.calcular_deuda_inversa()

                    # CAJA MODO TOTAL DIRECTO
                    BoxLayout:
                        id: caja_modo_total
                        orientation: 'vertical'
                        size_hint_y: None
                        height: 0
                        opacity: 0
                        disabled: True
                        spacing: dp(10)
                        Label:
                            text: 'Monto Total de la Deuda ($):'
                            color: app.theme_text
                            font_size: sp(13)
                            size_hint_y: None
                            height: dp(20)
                            text_size: self.size
                            halign: 'left'
                        ModernInput:
                            id: deu_monto_total
                            hint_text: 'Ej. 5000'
                            input_filter: 'float'
                            on_text: app.calcular_deuda_inversa()
                    
                    PremiumCard:
                        orientation: 'vertical'
                        size_hint_y: None
                        height: dp(110)
                        Label:
                            text: 'RESUMEN DEL CÁLCULO'
                            color: app.theme_text_muted
                            font_size: sp(11)
                            bold: True
                        Label:
                            id: deu_calculo_vivo
                            text: 'Llena los datos para calcular...'
                            color: app.theme_text
                            bold: True
                            font_size: sp(15)
                            markup: True
                            text_size: self.width, None
                            halign: 'center'
                    
                    ActionBtn:
                        text: 'GUARDAR DEUDA'
                        size_hint_y: None
                        height: dp(55)
                        on_release: app.guardar_deuda()
                    
                    Label:
                        text: 'Tus Deudas Activas (Progreso)'
                        color: app.theme_text
                        bold: True
                        font_size: sp(18)
                        size_hint_y: None
                        height: dp(40)
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'

                    BoxLayout:
                        id: lista_abonos
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(15)

        # ==========================================
        #           PANTALLA MÁS FUNCIONES
        # ==========================================
        Screen:
            name: 'menu'
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(20)
                    spacing: dp(20)
                    size_hint_y: None
                    height: self.minimum_height
                    
                    Label:
                        text: 'Opciones'
                        color: app.theme_text
                        bold: True
                        font_size: sp(20)
                        size_hint_y: None
                        height: dp(40)
                        text_size: self.size
                        halign: 'left'
                    
                    GridLayout:
                        cols: 2
                        spacing: dp(15)
                        size_hint_y: None
                        height: dp(350)
                        
                        MenuCardBtn:
                            icon_type: 'card'
                            text_title: 'Tarjetas'
                            text_sub: 'Añadir Créditos'
                            on_release: sm.current = 'tarjetas'
                            
                        MenuCardBtn:
                            icon_type: 'home'
                            text_title: 'Fijos'
                            text_sub: 'Internet, Comida...'
                            on_release: sm.current = 'fijos'

                        MenuCardBtn:
                            icon_type: 'basket'
                            text_title: 'Canasta'
                            text_sub: 'Despensa IA'
                            on_release: sm.current = 'canasta'

        # ==========================================
        #           PANTALLA INGRESOS
        # ==========================================
        Screen:
            name: 'ingresos'
            BoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(10)
                Label:
                    text: 'Registrar Ingreso o Ahorro'
                    color: app.theme_text
                    bold: True
                    font_size: sp(20)
                    size_hint_y: None
                    height: dp(40)
                    text_size: self.size
                    halign: 'left'
                Label:
                    text: 'Tus ahorros reales regístralos como "Único".'
                    color: app.theme_text_muted
                    font_size: sp(12)
                    size_hint_y: None
                    height: dp(20)
                    text_size: self.size
                    halign: 'left'
                ModernSpinner:
                    id: ing_tipo
                    text: 'Salario'
                    values: ('Salario', 'Vales', 'Ingreso Extra', 'Inversión', 'Ahorro')
                ModernInput:
                    id: ing_monto
                    hint_text: 'Monto ($)'
                    input_filter: 'float'
                ModernSpinner:
                    id: ing_frecuencia
                    text: 'Mensual'
                    values: ('Único', 'Semanal', 'Quincenal', 'Mensual')
                Widget:
                    size_hint_y: None
                    height: dp(10)
                ActionBtn:
                    text: 'GUARDAR DINERO'
                    size_hint_y: None
                    height: dp(55)
                    on_release: app.guardar_ingreso()
                Widget:

        # ==========================================
        #           PANTALLA TARJETAS
        # ==========================================
        Screen:
            name: 'tarjetas'
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(20)
                    spacing: dp(10)
                    size_hint_y: None
                    height: self.minimum_height
                    Label:
                        text: 'Añadir Tarjeta de Crédito'
                        color: app.theme_text
                        bold: True
                        font_size: sp(20)
                        size_hint_y: None
                        height: dp(40)
                        text_size: self.size
                        halign: 'left'
                    
                    Label:
                        text: 'Nombre del Banco (Ej. Nu, BBVA):'
                        color: app.theme_text
                        font_size: sp(13)
                        size_hint_y: None
                        height: dp(20)
                        text_size: self.size
                        halign: 'left'
                    ModernInput:
                        id: t_banco
                        hint_text: 'Ej. Nu'
                    
                    Label:
                        text: 'Últimos 4 Dígitos:'
                        color: app.theme_text
                        font_size: sp(13)
                        size_hint_y: None
                        height: dp(20)
                        text_size: self.size
                        halign: 'left'
                    ModernInput:
                        id: t_digitos
                        hint_text: 'Ej. 1234'
                        input_filter: 'int'

                    Label:
                        text: 'Límite Original de Crédito ($):'
                        color: app.theme_text
                        font_size: sp(13)
                        size_hint_y: None
                        height: dp(20)
                        text_size: self.size
                        halign: 'left'
                    ModernInput:
                        id: t_limite
                        hint_text: 'Ej. 15000'
                        input_filter: 'float'
                    
                    GridLayout:
                        cols: 2
                        spacing: dp(10)
                        size_hint_y: None
                        height: dp(85)
                        BoxLayout:
                            orientation: 'vertical'
                            Label:
                                text: 'Día de Corte (Número):'
                                color: app.theme_text
                                font_size: sp(13)
                            ModernInput:
                                id: t_corte
                                hint_text: 'Ej. 15'
                        BoxLayout:
                            orientation: 'vertical'
                            Label:
                                text: 'Día de Pago (Número):'
                                color: app.theme_text
                                font_size: sp(13)
                            ModernInput:
                                id: t_pago
                                hint_text: 'Ej. 05'
                    
                    Widget:
                        size_hint_y: None
                        height: dp(10)
                    
                    Label:
                        id: lbl_exito_tarjeta
                        text: ''
                        color: get_color_from_hex('#10B981')
                        font_size: sp(13)
                        bold: True
                        size_hint_y: None
                        height: dp(30)
                    
                    ActionBtn:
                        text: 'GUARDAR TARJETA'
                        size_hint_y: None
                        height: dp(55)
                        on_release: app.guardar_tarjeta_basica()

        # ==========================================
        #           PANTALLA FIJOS
        # ==========================================
        Screen:
            name: 'fijos'
            BoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(10)
                Label:
                    text: 'Gastos Fijos'
                    color: app.theme_text
                    bold: True
                    font_size: sp(20)
                    size_hint_y: None
                    height: dp(40)
                    text_size: self.size
                    halign: 'left'
                ModernInput:
                    id: fijo_concepto
                    hint_text: 'Concepto (Ej. Internet)'
                ModernInput:
                    id: fijo_monto
                    hint_text: 'Monto ($)'
                    input_filter: 'float'
                GridLayout:
                    cols: 2
                    spacing: dp(10)
                    size_hint_y: None
                    height: dp(85)
                    ModernSpinner:
                        id: fijo_frecuencia
                        text: 'Mensual'
                        values: ('Semanal', 'Quincenal', 'Mensual')
                    ModernInput:
                        id: fijo_fecha
                        hint_text: 'Día de Pago'
                ActionBtn:
                    text: 'AGREGAR FIJO'
                    size_hint_y: None
                    height: dp(55)
                    on_release: app.guardar_fijo()
                ScrollView:
                    BoxLayout:
                        id: lista_fijos
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(10)

        Screen:
            name: 'canasta'
            BoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(10)
                Label:
                    text: 'Canasta Inteligente'
                    color: app.theme_text
                    bold: True
                    font_size: sp(20)
                    size_hint_y: None
                    height: dp(40)
                    text_size: self.size
                    halign: 'left'
                ModernInput:
                    id: can_prod
                    hint_text: 'Producto'
                ModernInput:
                    id: can_precio
                    hint_text: 'Precio ($)'
                    input_filter: 'float'
                ActionBtn:
                    text: 'AL CARRITO'
                    size_hint_y: None
                    height: dp(55)
                    on_release: app.guardar_canasta()
                ScrollView:
                    BoxLayout:
                        id: lista_canasta
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(10)

        # ==========================================
        #           PANTALLA ANÁLISIS
        # ==========================================
        Screen:
            name: 'analisis'
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(15)
                    spacing: dp(15)
                    size_hint_y: None
                    height: self.minimum_height
                    Label:
                        text: 'Reporte de IA (Vida y Finanzas)'
                        color: get_color_from_hex('#8B5CF6')
                        bold: True
                        font_size: sp(20)
                        size_hint_y: None
                        height: dp(40)
                        text_size: self.size
                        halign: 'left'
                    BoxLayout:
                        id: ia_contenedor
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(15)

    # NAVEGACIÓN INFERIOR
    BoxLayout:
        id: nav_bottom
        opacity: 0 # Oculto en splash
        disabled: True
        size_hint_y: None
        height: dp(65)
        canvas.before:
            Color:
                rgba: app.theme_card
            Rectangle:
                pos: self.pos
                size: self.size
        
        NavBtn:
            text: 'INICIO'
            icon_type: 'home'
            active: sm.current == 'home'
            on_release: app.go_home()
        NavBtn:
            text: 'INGRESOS'
            icon_type: 'wallet'
            active: sm.current == 'ingresos'
            on_release: sm.current = 'ingresos'
        NavBtn:
            text: 'DEUDAS'
            icon_type: 'card'
            active: sm.current == 'deudas'
            on_release: sm.current = 'deudas'; app.al_abrir_deudas()
        NavBtn:
            text: 'REPORTE'
            icon_type: 'chart'
            active: sm.current == 'analisis'
            on_release: app.analizar_datos_ia()
        NavBtn:
            text: 'MÁS'
            icon_type: 'menu'
            active: sm.current == 'menu'
            on_release: sm.current = 'menu'
'''

class DinerekApp(App):
    is_dark = BooleanProperty(True)
    
    theme_bg = ListProperty(get_color_from_hex('#0F172A'))
    theme_card = ListProperty(get_color_from_hex('#1E293B'))
    theme_text = ListProperty(get_color_from_hex('#F8FAFC'))
    theme_text_muted = ListProperty(get_color_from_hex('#94A3B8'))
    theme_accent = ListProperty(get_color_from_hex('#0EA5E9'))
    theme_accent_gradient = ListProperty(get_color_from_hex('#0284C7'))
    theme_input_bg = ListProperty(get_color_from_hex('#334155')) 
    theme_input_text = ListProperty(get_color_from_hex('#FFFFFF'))

    def build(self):
        init_db()
        self.root = Builder.load_string(KV)
        self.root.ids.sm.current = 'splash'
        self.loading_event = Clock.schedule_interval(self.update_splash, 0.05)
        self.ticks = 0
        return self.root

    def update_splash(self, dt):
        self.ticks += 1
        pct = self.ticks / 100.0
        self.root.ids.splash_progress.porcentaje = pct
        
        if pct < 0.3: self.root.ids.lbl_loading_text.text = 'Iniciando módulos de inteligencia...'
        elif pct < 0.7: self.root.ids.lbl_loading_text.text = 'Calculando tus finanzas y tarjetas...'
        else: self.root.ids.lbl_loading_text.text = 'Preparando Dashboard Max...'

        if self.ticks >= 100:
            self.loading_event.cancel()
            self.root.ids.header_top.opacity = 1
            self.root.ids.header_top.disabled = False
            self.root.ids.nav_bottom.opacity = 1
            self.root.ids.nav_bottom.disabled = False
            self.go_home()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        if self.is_dark:
            self.theme_bg = get_color_from_hex('#0F172A')
            self.theme_card = get_color_from_hex('#1E293B')
            self.theme_text = get_color_from_hex('#F8FAFC')
            self.theme_text_muted = get_color_from_hex('#94A3B8')
            self.theme_accent = get_color_from_hex('#0EA5E9')
            self.theme_accent_gradient = get_color_from_hex('#0284C7')
            self.theme_input_bg = get_color_from_hex('#334155')
            self.theme_input_text = get_color_from_hex('#FFFFFF')
        else:
            self.theme_bg = get_color_from_hex('#F1F5F9')
            self.theme_card = get_color_from_hex('#FFFFFF')
            self.theme_text = get_color_from_hex('#0F172A')
            self.theme_text_muted = get_color_from_hex('#64748B')
            self.theme_accent = get_color_from_hex('#2563EB')
            self.theme_accent_gradient = get_color_from_hex('#1D4ED8')
            self.theme_input_bg = get_color_from_hex('#E2E8F0') 
            self.theme_input_text = get_color_from_hex('#000000')

    def db_query(self, query, params=(), fetch=False):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(query, params)
            if fetch:
                data = c.fetchall()
                conn.close()
                return data
            conn.commit()
            conn.close()
        except Exception as e:
            print("Error SQL protegido:", e)
            return []

    def go_home(self):
        self.root.ids.sm.current = 'home'
        self.actualizar_home()

    def guardar_tarjeta_basica(self):
        ids = self.root.ids
        banco = ids.t_banco.text.strip()
        if not banco:
            ids.lbl_exito_tarjeta.text = "Error: El Banco es obligatorio."
            ids.lbl_exito_tarjeta.color = get_color_from_hex('#EF4444')
            return
            
        q = "INSERT INTO tarjetas (banco, digitos, limite, corte, pago) VALUES (?,?,?,?,?)"
        lim = parse_float(ids.t_limite.text)
        self.db_query(q, (banco, ids.t_digitos.text.strip(), lim, ids.t_corte.text.strip(), ids.t_pago.text.strip()))
        
        ids.t_banco.text = ""; ids.t_digitos.text = ""; ids.t_limite.text = ""; ids.t_corte.text = ""; ids.t_pago.text = ""
        ids.lbl_exito_tarjeta.text = "¡Tarjeta Guardada Correctamente!"
        ids.lbl_exito_tarjeta.color = get_color_from_hex('#10B981')
        self.actualizar_home()

    def al_abrir_deudas(self):
        self.root.ids.sm.current = 'deudas'
        self.check_deuda_tipo()
        self.actualizar_abonos()

    def check_deuda_tipo(self):
        ids = self.root.ids
        tipo = ids.deu_acreedor_tipo.text
        
        if tipo == 'Tarjeta':
            ids.deu_acreedor_spin.opacity = 1; ids.deu_acreedor_spin.disabled = False
            ids.deu_acreedor_txt.opacity = 0; ids.deu_acreedor_txt.disabled = True
            tarjetas_db = self.db_query("SELECT banco, digitos FROM tarjetas", fetch=True)
            nombres = [f"{t[0].strip()} (*{t[1].strip()})" for t in tarjetas_db]
            if nombres: ids.deu_acreedor_spin.values = nombres; ids.deu_acreedor_spin.text = nombres[0]
            else: ids.deu_acreedor_spin.values = ['Sin Tarjetas Reg.']; ids.deu_acreedor_spin.text = 'Sin Tarjetas Reg.'
        else:
            ids.deu_acreedor_spin.opacity = 0; ids.deu_acreedor_spin.disabled = True
            ids.deu_acreedor_txt.opacity = 1; ids.deu_acreedor_txt.disabled = False
            
            if tipo == 'Persona':
                ids.deu_modo_registro.text = 'Deuda Total Directa (Un solo pago)'

    def toggle_modo_deuda(self):
        ids = self.root.ids
        modo = ids.deu_modo_registro.text
        if modo == 'Deuda Total Directa (Un solo pago)':
            ids.caja_modo_cuotas.opacity = 0; ids.caja_modo_cuotas.height = 0; ids.caja_modo_cuotas.disabled = True
            ids.caja_modo_total.opacity = 1; ids.caja_modo_total.height = dp(65); ids.caja_modo_total.disabled = False
        else:
            ids.caja_modo_total.opacity = 0; ids.caja_modo_total.height = 0; ids.caja_modo_total.disabled = True
            ids.caja_modo_cuotas.opacity = 1; ids.caja_modo_cuotas.height = dp(115); ids.caja_modo_cuotas.disabled = False
        self.calcular_deuda_inversa()

    def calcular_deuda_inversa(self, *args):
        ids = self.root.ids
        modo = ids.deu_modo_registro.text
        
        try:
            if modo == 'Deuda Total Directa (Un solo pago)':
                total = parse_float(ids.deu_monto_total.text)
                if total > 0: ids.deu_calculo_vivo.text = f"[color=#0EA5E9][size=18sp]Deuda Total a Guardar: ${total:,.2f}[/size][/color]"
                else: ids.deu_calculo_vivo.text = "Escribe el monto total..."
            else:
                cuota = parse_float(ids.deu_cuota.text)
                plazo = int(ids.deu_plazo.text.replace(',', '')) if ids.deu_plazo.text else 0
                frecuencia = ids.deu_frecuencia.text
                if cuota > 0 and plazo > 0:
                    total_pagar = cuota * plazo
                    ids.deu_calculo_vivo.text = f"Abono: ${cuota:,.2f} x {plazo} pagos ({frecuencia})\n[color=#0EA5E9][size=18sp]Deuda Total: ${total_pagar:,.2f}[/size][/color]"
                else: ids.deu_calculo_vivo.text = "Completa Cuota y Plazo..."
        except Exception:
            ids.deu_calculo_vivo.text = "Escribe números válidos..."

    def guardar_deuda(self):
        ids = self.root.ids
        try:
            modo = ids.deu_modo_registro.text
            tipo_acreedor = ids.deu_acreedor_tipo.text
            acreedor_nombre = ids.deu_acreedor_spin.text.strip() if tipo_acreedor == 'Tarjeta' else ids.deu_acreedor_txt.text.strip()
            concepto = ids.deu_concepto.text

            if modo == 'Deuda Total Directa (Un solo pago)':
                total = parse_float(ids.deu_monto_total.text)
                cuota = total
                plazo = 1
                frecuencia = 'Mensual' 
            else:
                cuota = parse_float(ids.deu_cuota.text)
                plazo = int(ids.deu_plazo.text.replace(',', '')) if ids.deu_plazo.text else 0
                frecuencia = ids.deu_frecuencia.text
                total = cuota * plazo

            if total > 0:
                self.db_query("INSERT INTO deudas (concepto, tipo_acreedor, acreedor, monto_original, cuota, plazo, total, frecuencia) VALUES (?,?,?,?,?,?,?,?)",
                              (concepto, tipo_acreedor, acreedor_nombre, total, cuota, plazo, total, frecuencia))
                
                ids.deu_cuota.text = ""; ids.deu_plazo.text = ""; ids.deu_concepto.text = ""; ids.deu_acreedor_txt.text = ""; ids.deu_monto_total.text = ""
                ids.deu_calculo_vivo.text = "¡Deuda Registrada con éxito!"
                self.actualizar_abonos()
                self.actualizar_home()
        except Exception: pass

    def guardar_ingreso(self):
        ids = self.root.ids
        monto_limpio = parse_float(ids.ing_monto.text)
        if monto_limpio > 0:
            self.db_query("INSERT INTO ingresos (tipo, monto, frecuencia) VALUES (?,?,?)", (ids.ing_tipo.text, monto_limpio, ids.ing_frecuencia.text))
            ids.ing_monto.text = ''
            self.go_home()

    def guardar_fijo(self):
        ids = self.root.ids
        monto_limpio = parse_float(ids.fijo_monto.text)
        if monto_limpio > 0 and ids.fijo_concepto.text:
            self.db_query("INSERT INTO fijos (concepto, monto, frecuencia, fecha_pago) VALUES (?,?,?,?)", 
                          (ids.fijo_concepto.text, monto_limpio, ids.fijo_frecuencia.text, ids.fijo_fecha.text))
            ids.fijo_monto.text = ''; ids.fijo_concepto.text = ''; ids.fijo_fecha.text = ''
            self.actualizar_fijos()
            self.actualizar_home()

    def eliminar_fijo(self, id_fijo):
        self.db_query("DELETE FROM fijos WHERE id=?", (id_fijo,))
        self.actualizar_fijos()
        self.actualizar_home()

    def guardar_canasta(self):
        ids = self.root.ids
        precio = parse_float(ids.can_precio.text)
        if precio > 0:
            self.db_query("INSERT INTO canasta (producto, precio) VALUES (?,?)", (ids.can_prod.text, precio))
            ids.can_prod.text = ''; ids.can_precio.text = ''
            self.actualizar_canasta()

    def hacer_abono_custom(self, deuda_id, monto_txt):
        monto = parse_float(monto_txt)
        if monto > 0:
            self.db_query("INSERT INTO abonos (deuda_id, monto, fecha) VALUES (?,?,?)", (deuda_id, monto, datetime.datetime.now().strftime("%Y-%m-%d")))
            self.actualizar_abonos()
            self.actualizar_home()

    def actualizar_abonos(self):
        deudas = self.db_query("SELECT id, concepto, total, cuota, frecuencia, tipo_acreedor, acreedor, plazo FROM deudas", fetch=True)
        box = self.root.ids.lista_abonos
        box.clear_widgets()
        for d in deudas:
            abonos_raw = self.db_query("SELECT monto FROM abonos WHERE deuda_id=?", (d[0],), fetch=True)
            total_abonado = sum((a[0] or 0.0) for a in abonos_raw) if abonos_raw else 0.0
            restante = d[2] - total_abonado
            
            # --- MAGIA DEL ABONO EXACTO ---
            num_abonos_realizados = len(abonos_raw) if abonos_raw else 0
            siguiente_abono = num_abonos_realizados + 1
            plazo_total = d[7] if d[7] else 1
            
            if restante > 0:
                card = AbonoCard()
                card.deuda_id = d[0]
                card.cuota_sugerida = d[3]
                acreedor_txt = d[6] if d[6] else "Desconocido"
                total_original = d[2] if d[2] > 0 else 1 
                
                pct = total_abonado / total_original
                card.progreso_pct = pct
                
                texto_info = f"[b][size=15sp]{d[1]}[/size][/b] ({d[5]}: {acreedor_txt})\n"
                texto_info += f"Total: ${d[2]:,.2f} | Abonado: [color=#10B981]${total_abonado:,.2f}[/color]\n"
                texto_info += f"Por pagar: [color=#EF4444][b]${restante:,.2f}[/b][/color]\n"
                texto_info += f"Cuota {d[4]}: ${d[3]:,.2f}"
                
                card.info_text = texto_info
                
                # --- ASIGNACIÓN DEL TEXTO GRANDE Y CLARO ---
                if plazo_total == 1:
                    card.texto_progreso = "Pago Único / Total Directo"
                else:
                    abono_mostrar = min(siguiente_abono, plazo_total)
                    card.texto_progreso = f"Vas a pagar el abono {abono_mostrar} de {plazo_total}"
                
                box.add_widget(card)

    def actualizar_home(self):
        ids = self.root.ids
        
        hoy = datetime.date.today()
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        ids.lbl_fecha.text = f"{dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month - 1]}"

        # 2. CÁLCULO DE INGRESOS Y AHORROS LIBRES (CORREGIDO PARA ÚNICO/MENSUAL)
        ingresos = self.db_query("SELECT monto, frecuencia, tipo FROM ingresos", fetch=True)
        ing_mes = 0; ahorro_total_historico = 0; ahorro_mensual_esperado = 0
        
        for m, f, t in ingresos:
            val = m or 0.0
            if t == 'Ahorro': 
                if f == 'Único': ahorro_total_historico += val
                elif f == 'Semanal': ahorro_mensual_esperado += val*4; ahorro_total_historico += val*4
                elif f == 'Quincenal': ahorro_mensual_esperado += val*2; ahorro_total_historico += val*2
                elif f == 'Mensual': ahorro_mensual_esperado += val; ahorro_total_historico += val
            else: 
                if f == 'Semanal': ing_mes += val*4 
                elif f == 'Quincenal': ing_mes += val*2 
                elif f == 'Mensual': ing_mes += val
                elif f == 'Único': ing_mes += val
                
        ing_sem = ing_mes / 4
        ids.h_ing_mes.text = f"Mes: ${ing_mes:,.2f}"
        ids.h_ing_sem.text = f"Semana: ${ing_sem:,.2f}"
        
        ids.h_ahorro_total.text = f"${ahorro_total_historico:,.2f}"
        if ahorro_mensual_esperado > 0:
            ids.h_ahorro_mes.text = f"Ahorro mensual programado: ${ahorro_mensual_esperado:,.2f}"
        else:
            ids.h_ahorro_mes.text = "Sin ahorro mensual programado"

        # 3. CÁLCULO FIJOS
        fijos = self.db_query("SELECT monto, frecuencia FROM fijos", fetch=True)
        fij_mes = sum((m*4 if f=='Semanal' else m*2 if f=='Quincenal' else m) for m, f in fijos if m)
        fij_sem = fij_mes / 4
        ids.h_fij_mes.text = f"Mes: ${fij_mes:,.2f}"
        ids.h_fij_sem.text = f"Semana: ${fij_sem:,.2f}"

        # 4. CÁLCULO DEUDAS (LÓGICA PARA RESTAR LÍMITE)
        deudas = self.db_query("SELECT id, total, cuota, frecuencia, tipo_acreedor, acreedor FROM deudas", fetch=True)
        deu_mes = 0; deuda_global = 0
        deuda_por_tarjeta = {} 
        
        for d_id, total, cuota, frec, tipo, acreedor in deudas:
            abonos_raw = self.db_query("SELECT monto FROM abonos WHERE deuda_id=?", (d_id,), fetch=True)
            abonos = sum((a[0] or 0.0) for a in abonos_raw) if abonos_raw else 0.0
            restante = total - abonos
            
            if restante > 0:
                deuda_global += restante
                cuota_mes = cuota*4 if frec == 'Semanal' else cuota*2 if frec == 'Quincenal' else cuota
                deu_mes += cuota_mes
                
                # ¡AQUÍ ESTÁ LA MAGIA! Si abonas, "restante" baja, entonces la deuda asignada a la tarjeta baja
                if tipo == 'Tarjeta' and acreedor:
                    clean_name = str(acreedor).strip()
                    deuda_por_tarjeta[clean_name] = deuda_por_tarjeta.get(clean_name, 0.0) + restante

        deu_sem = deu_mes / 4
        ids.h_deuda_global.text = f"${deuda_global:,.2f}"
        ids.h_deu_mes.text = f"Mes: ${deu_mes:,.2f}"
        ids.h_deu_sem.text = f"Semana: ${deu_sem:,.2f}"

        # BALANCE Y PROYECCIÓN ANUAL
        gastos_totales_mes = fij_mes + deu_mes
        balance_libre = ing_mes - gastos_totales_mes
        ids.home_balance.text = f"${balance_libre:,.2f}"
        
        proyeccion_12_meses = balance_libre * 12
        if proyeccion_12_meses > 0:
            ids.h_proyeccion_anual.text = f"+${proyeccion_12_meses:,.2f} en 1 año"
            ids.h_proyeccion_anual.color = get_color_from_hex('#8B5CF6')
        else:
            ids.h_proyeccion_anual.text = f"-${abs(proyeccion_12_meses):,.2f} en 1 año (Alerta)"
            ids.h_proyeccion_anual.color = get_color_from_hex('#EF4444')
        
        if balance_libre < 0: 
            ids.home_balance.color = get_color_from_hex('#EF4444')
        else: 
            ids.home_balance.color = get_color_from_hex('#F8FAFC')

        # DONUT
        if ing_mes > 0:
            ids.donut_grafica.pct_fijos = fij_mes / ing_mes
            ids.donut_grafica.pct_deudas = deu_mes / ing_mes
        else:
            ids.donut_grafica.pct_fijos = 0; ids.donut_grafica.pct_deudas = 0

        # 5. TARJETAS CON DESCUENTO DE LÍMITE Y CALENDARIO (HORIZONTAL)
        tarjetas_db = self.db_query("SELECT banco, digitos, limite, corte, pago FROM tarjetas", fetch=True)
        box = ids.home_tarjetas_lista
        box.clear_widgets()

        # Enriquecer tarjetas con fechas calculadas para ordenar
        tarjetas_ordenadas = []
        for t in tarjetas_db:
            pago_str = str(t[4]).strip() if t[4] else "0"
            prox_pago = get_next_date(pago_str, hoy)
            tarjetas_ordenadas.append({'data': t, 'prox_pago': prox_pago})
        
        # Ordenar por fecha de pago más próxima
        tarjetas_ordenadas.sort(key=lambda x: x['prox_pago'])

        for item in tarjetas_ordenadas:
            t = item['data']
            prox_pago = item['prox_pago']
            dias_faltantes = (prox_pago - hoy).days

            banco = str(t[0]).strip() if t[0] else "Banco"
            dig = str(t[1]).strip() if t[1] else "****"
            nombre_tarjeta_exacto = f"{banco} (*{dig})"
            limite_original = t[2] if t[2] else 0.0
            corte_str = str(t[3]).strip() if t[3] else "N/A"
            
            # MATEMÁTICA EXACTA: Límite Original - Deuda Pendiente Actual
            deuda_de_esta_tarjeta = deuda_por_tarjeta.get(nombre_tarjeta_exacto, 0.0)
            limite_disponible = limite_original - deuda_de_esta_tarjeta
            
            porcentaje_usado = 0.0
            if limite_original > 0:
                porcentaje_usado = deuda_de_esta_tarjeta / limite_original
            
            # HORIZONTAL CARD SETUP
            card = PremiumCard(); card.orientation = 'vertical'; card.size_hint_x = None; card.width = dp(260); card.padding = dp(15)
            
            box_header = BoxLayout(size_hint_y=0.3)
            box_header.add_widget(Label(text=f"[b]{nombre_tarjeta_exacto}[/b]", markup=True, color=get_color_from_hex('#8B5CF6'), font_size=sp(15), halign='left', text_size=(dp(130), None)))
            box_header.add_widget(Label(text=f"Disp: [color=#10B981][b]${limite_disponible:,.0f}[/b][/color]", markup=True, font_size=sp(13), halign='right', text_size=(dp(100), None)))
            card.add_widget(box_header)
            
            box_text = BoxLayout(size_hint_y=0.3)
            box_text.add_widget(Label(text=f"A pagar: [color=#EF4444]${deuda_de_esta_tarjeta:,.0f}[/color]", markup=True, font_size=sp(12), halign='left', text_size=(dp(130), None)))
            
            # Etiqueta de días faltantes
            color_dias = '#EF4444' if dias_faltantes <= 5 else ('#F59E0B' if dias_faltantes <= 10 else '#10B981')
            alerta_dias = f"Faltan {dias_faltantes} días" if dias_faltantes > 0 else "¡PAGA HOY!"
            box_text.add_widget(Label(text=f"[color={color_dias}][b]{alerta_dias}[/b][/color]", markup=True, font_size=sp(11), halign='right', text_size=(dp(100), None)))
            card.add_widget(box_text)
            
            barra = ProgressBarWidget(size_hint_y=None, height=dp(10))
            barra.porcentaje = porcentaje_usado
            if porcentaje_usado > 0.8: barra.color_barra = get_color_from_hex('#EF4444')
            elif porcentaje_usado > 0.4: barra.color_barra = get_color_from_hex('#F59E0B')
            else: barra.color_barra = get_color_from_hex('#10B981')
            
            box_barra = BoxLayout(size_hint_y=0.2, padding=[0, dp(5)]); box_barra.add_widget(barra)
            card.add_widget(box_barra)
            
            box_fechas = BoxLayout(size_hint_y=0.2)
            prox_corte = get_next_date(corte_str, hoy)
            box_fechas.add_widget(Label(text=f"Corte: {prox_corte.strftime('%d/%b')} | Pago: {prox_pago.strftime('%d/%b')}", color=self.theme_text_muted, font_size=sp(11), halign='center'))
            card.add_widget(box_fechas)

            box.add_widget(card)

    def actualizar_fijos(self):
        fijos = self.db_query("SELECT id, concepto, monto, frecuencia, fecha_pago FROM fijos", fetch=True)
        box = self.root.ids.lista_fijos
        box.clear_widgets()
        for f in fijos:
            card = FijoCard()
            card.fijo_id = f[0]; card.concepto = str(f[1]); card.monto_text = f"${f[2]:,.2f}"; card.detalle_text = f"{f[3]} | Pago: {f[4]}"
            box.add_widget(card)
            
    def actualizar_canasta(self):
        prods = self.db_query("SELECT id, producto, precio FROM canasta", fetch=True)
        box = self.root.ids.lista_canasta
        box.clear_widgets()
        for p in prods:
            box.add_widget(Label(text=f"{p[1]} - ${p[2]:,.2f}", color=self.theme_text, size_hint_y=None, height=dp(30)))

    def analizar_datos_ia(self):
        self.root.ids.sm.current = 'analisis'
        box = self.root.ids.ia_contenedor
        box.clear_widgets()
        
        ingresos = self.db_query("SELECT monto, frecuencia, tipo FROM ingresos", fetch=True)
        ing = 0; ahorros = 0
        for m, f, t in ingresos:
            val = m or 0.0
            if t == 'Ahorro': 
                if f == 'Único': ahorros += val
                elif f == 'Mensual': ahorros += val
                elif f == 'Semanal': ahorros += val * 4
                elif f == 'Quincenal': ahorros += val * 2
            else: 
                if f == 'Semanal': ing += val*4 
                elif f == 'Quincenal': ing += val*2 
                elif f == 'Mensual': ing += val
                elif f == 'Único': ing += val

        fij = sum((m*4 if f=='Semanal' else m*2 if f=='Quincenal' else m) for m, f in self.db_query("SELECT monto, frecuencia FROM fijos", fetch=True) if m)
        
        deu_mes = 0; deuda_global = 0
        for d_id, tot, cuota, frec in self.db_query("SELECT id, total, cuota, frecuencia FROM deudas", fetch=True):
            restante = tot - sum((a[0] or 0.0) for a in self.db_query("SELECT monto FROM abonos WHERE deuda_id=?", (d_id,), fetch=True))
            if restante > 0:
                deuda_global += restante
                if frec == 'Semanal': deu_mes += (cuota * 4)
                elif frec == 'Quincenal': deu_mes += (cuota * 2)
                else: deu_mes += cuota

        def card_ia(titulo, desc, color):
            c = PremiumCard(); c.size_hint_y = None; c.height = dp(230); c.orientation = 'vertical'
            l1 = Label(text=titulo, bold=True, color=get_color_from_hex(color), font_size=sp(15), size_hint_y=None, height=dp(30), halign='left')
            l2 = Label(text=desc, color=self.theme_text, font_size=sp(13), halign='left', valign='top', markup=True)
            l1.bind(size=l1.setter('text_size')); l2.bind(size=l2.setter('text_size'))
            c.add_widget(l1); c.add_widget(l2)
            return c

        if ing == 0:
            box.add_widget(card_ia('Faltan Datos', 'Agrega Ingresos para que la IA pueda calcular tu salud.', '#94A3B8')); return

        # ---------------------------------------------------------
        # ANÁLISIS FINANCIERO AVANZADO (ESTADÍSTICAS Y RECOMENDACIONES)
        # ---------------------------------------------------------
        
        # 1. Diagnóstico de Salud Financiera
        ratio_deuda = (deu_mes / ing) * 100 if ing > 0 else 0
        ratio_fijos = (fij / ing) * 100 if ing > 0 else 0
        libre_pct = 100 - ratio_deuda - ratio_fijos

        salud_txt = f"Ingresos: [color=#10B981]${ing:,.2f}[/color]\n"
        salud_txt += f"Comprometido en Deudas: [color={'#EF4444' if ratio_deuda > 30 else '#F59E0B'}]{ratio_deuda:.1f}%[/color] (Ideal < 30%)\n"
        salud_txt += f"Gastos Fijos: [color=#0EA5E9]{ratio_fijos:.1f}%[/color] (Ideal < 50%)\n"
        salud_txt += f"Liquidez Libre: [color={'#10B981' if libre_pct >= 20 else '#EF4444'}]{libre_pct:.1f}%[/color]\n\n"
        
        if ratio_deuda > 40: salud_txt += "[b]⚠️ Alerta:[/b] Tu nivel de deuda es peligroso. Detén compras a crédito e intenta reestructurar deudas."
        elif libre_pct < 10: salud_txt += "[b]⚠️ Precaución:[/b] Tienes muy poca liquidez. Intenta recortar gastos fijos o no podrás afrontar imprevistos."
        else: salud_txt += "[b]✅ Excelente:[/b] Tus finanzas están estables. ¡Es momento de invertir el dinero libre!"
        
        box.add_widget(card_ia('📊 Diagnóstico de Salud Financiera', salud_txt, '#8B5CF6'))

        # 2. Recomendación: Fondo de Emergencia
        fondo_min = fij * 3
        fondo_ideal = fij * 6
        fondo_txt = f"El Fondo de Emergencia es tu escudo contra imprevistos, despidos o urgencias médicas. Se calcula con base en tus [b]gastos fijos mensuales (${fij:,.2f})[/b].\n\n"
        fondo_txt += f"🛡️ [b]Mínimo (3 meses):[/b] ${fondo_min:,.2f}\n"
        fondo_txt += f"🏆 [b]Ideal (6 meses):[/b] ${fondo_ideal:,.2f}\n\n"
        fondo_txt += f"Progreso actual: [color=#10B981]${ahorros:,.2f}[/color] ahorrados."
        
        box.add_widget(card_ia('🛡️ Fondo de Emergencia Meta', fondo_txt, '#0EA5E9'))

        # 3. Estimación y Proyección a Futuro (5 Años)
        ahorro_mensual = (ing - fij - deu_mes) if (ing - fij - deu_mes) > 0 else 0
        if ahorro_mensual > 0:
            # Fórmula de interés compuesto básico aportando mensualmente (aprox 8% anual)
            tasa_mensual = 0.08 / 12
            meses_5_anos = 60
            capital_futuro = ahorro_mensual * (((1 + tasa_mensual)**meses_5_anos - 1) / tasa_mensual)
            
            proy_txt = f"Si logras ahorrar tu dinero libre actual ([color=#10B981]${ahorro_mensual:,.2f}/mes[/color]) y lo inviertes en instrumentos seguros (como Cetes a 8% anual):\n\n"
            proy_txt += f"En 1 Año: [b]${(ahorro_mensual * 12 * 1.04):,.2f}[/b]\n"
            proy_txt += f"En 5 Años: [color=#10B981][b][size=16sp]${capital_futuro:,.2f}[/size][/b][/color]\n\n"
            proy_txt += "[i]El interés compuesto hará que tu dinero trabaje para ti automáticamente.[/i]"
        else:
            proy_txt = "Actualmente no tienes flujo de caja positivo al mes para proyectar inversiones. Tu prioridad número uno debe ser liquidar deudas (efecto bola de nieve) para liberar ingresos."

        box.add_widget(card_ia('🚀 Proyección de Riqueza (5 Años)', proy_txt, '#10B981'))

        # ---------------------------------------------------------
        # REPORTES IA MASIVOS Y TRUCOS DE AHORRO
        # ---------------------------------------------------------
        
        # 1. Carnes y Proteínas
        texto_carnes = "🥩 [b]Hack en Carnes:[/b]\n1. Compra pollo entero y pide al carnicero que lo despiece (es 30% más barato que en bandejas).\n2. El cerdo suele ser la proteína animal más económica.\n3. Rinde tu carne: Integra lentejas o frijoles molidos a tu carne para hamburguesas o albóndigas, rinden el triple por un cuarto del precio."
        box.add_widget(card_ia('Alimentación: Proteínas', texto_carnes, '#EF4444'))

        # 2. Verduras y Despensa
        texto_sada = "🍅 [b]Hack en el Súper:[/b]\n1. NUNCA compres frutas/verduras en el supermercado, ve al tianguis local o mercado, ahorrarás hasta 50%.\n2. Compra a granel: Arroz, frijol, semillas y especias son mucho más baratos sin la caja del supermercado.\n3. No vayas al súper con hambre, terminarás comprando comida chatarra innecesaria."
        box.add_widget(card_ia('Alimentación: Frescos y Granel', texto_sada, '#10B981'))

        # 3. La Regla de las Marcas Blancas
        texto_marcas = "🛒 [b]Marcas del Súper:[/b]\nCambia tus marcas favoritas por las 'Marcas Blancas' (Great Value, Aurrera, Soriana, etc.) en estos productos: Papel higiénico, cloro, jabón de trastes, azúcar y sal. Ahorrarás miles de pesos al año sin notar la diferencia en calidad."
        box.add_widget(card_ia('El Truco de las Marcas', texto_marcas, '#F59E0B'))

        # 4. Servicios y Electrónicos
        texto_casa = "⚡ [b]Ahorro en Casa:[/b]\n1. Consumo Vampiro: Desconecta microondas, consolas y cargadores. Consumen el 10% de tu recibo de luz estando apagados.\n2. Lava tu ropa con agua fría. El 85% de la energía de la lavadora se gasta solo en calentar el agua.\n3. Revisa los inodoros: Una fuga silenciosa es la principal causa de recibos de agua altísimos."
        box.add_widget(card_ia('Reducción de Servicios', texto_casa, '#0EA5E9'))

        # 5. Gastos Hormiga y Psicología
        texto_hormiga = "🧠 [b]Psicología de Compra:[/b]\n1. Regla de los 3 días: Si ves algo en internet que quieres comprar, espera 3 días. El 80% de las veces se te pasarán las ganas.\n2. Desinstala Amazon, MercadoLibre o Shein de tu pantalla principal.\n3. Suscripciones: No pagues 4 plataformas a la vez. Paga Netflix un mes, luego cancélala y pasa a Disney, así sucesivamente."
        box.add_widget(card_ia('Psicología y Fugas', texto_hormiga, '#8B5CF6'))

if __name__ == '__main__':
    DinerekApp().run()