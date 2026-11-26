#Librerias utilizadas en el proyecto
import sys      #Permite controlar la ejecucion y cierre del programa.
import time     #Permite medir y controlar los tiempos de la simulacion.
import ctypes   #Permite acceder a funciones de Windows, como modificar la barra de titulo.
import copy     #Permite realizar copias de objetos sin modificar los originales.
import numpy as np  #Permite realizar operaciones matematicas con arreglos y vectores.
import pyvista as pv  #Permite crear y visualizar los elementos graficos en 3D.

#Importacion de funciones y componentes especificos
from scipy.integrate import tplquad #Permite calcular integrales triples
from pyvistaqt import QtInteractor #Permite integrar la visualizacion 3D de PyVista en la interfaz grafica.
from PySide6.QtCore import QTimer, Qt, QEvent #Componentes para controlar el tiempo, los eventos y la interfaz.
from PySide6.QtWidgets import ( #Componentes utilizados para construir la interfaz grafica.
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel
)

# PARAMETROS DEL PROYECTO
R = 4.0
H = 10.0
TF = 5.0
R0 = 2.5
OMEGA = 2 * np.pi
VZ = 2.0
I0 = 50.0
A = 5.0

# Grados por segundo de la camara
VELOCIDAD_ROTACION = 18.0

# Colores
FONDO_OSCURO = "#141A27"
PANEL_OSCURO = "#202938"
LEYENDA_OSCURA = "#263245"
FONDO_CLARO = "#FFFFFF"
PANEL_CLARO = "#F0F0F0"
LEYENDA_CLARA = "#FFFFFF"
AZUL_HELICE = "#18276B"
AZUL_RECORRIDO = "#1E90FF"


# FUNCIONES MATEMATICAS

#Permite calcular la posicion de la particula en los ejes X, Y y Z
#en cualquier instante de tiempo, siguiendo una trayectoria
#helicoidal dentro del cilindro.
def trayectoria(t):
    x = R0 * np.cos(OMEGA * t)
    y = R0 * np.sin(OMEGA * t)
    z = VZ * t
    return x, y, z


#Permite calcular la intensidad luminosa en cualquier punto
#del cilindro dependiendo de su distancia al eje central
#y de la altura en la que se encuentra.
#Representa una densidad volumetrica de potencia en W/m^3.
def intensidad(r, z):
    return I0 + A * (R**2 - r**2) * np.cos(
        np.pi * z / (2 * H)
    )


#Permite calcular el gradiente de la intensidad luminosa
#en coordenadas cilindricas mediante las derivadas parciales
#respecto al radio, el angulo y la altura.
#Determina la direccion de maximo aumento de la intensidad.
def gradiente_cilindrico(r, z):
    gr = -2 * A * r * np.cos(
        np.pi * z / (2 * H)
    )
    gtheta = np.zeros_like(np.asarray(gr))
    gz = (
        -A * (R**2 - r**2)
        * np.pi / (2 * H)
        * np.sin(np.pi * z / (2 * H))
    )
    return gr, gtheta, gz


#Permite convertir las componentes del gradiente de coordenadas
#cilindricas a coordenadas cartesianas para representar
#los vectores en los ejes X, Y y Z de la simulacion.
def gradiente_cartesiano(x, y, z):
    r = np.hypot(x, y)
    gr, _, gz = gradiente_cilindrico(r, z)
    theta = np.arctan2(y, x)
    gx = gr * np.cos(theta)
    gy = gr * np.sin(theta)
    return gx, gy, gz


#Permite calcular la potencia luminosa total mediante una integral
#triple del campo de intensidad en todo el volumen del cilindro.
#El resultado se expresa en watts y tambien se obtiene
#el error estimado de la integracion numerica.
def calcular_potencia():
    potencia, error = tplquad(
        lambda z, r, theta: intensidad(r, z) * r,
        0,
        2 * np.pi,
        lambda theta: 0,
        lambda theta: R,
        lambda theta, r: 0,
        lambda theta, r: H
    )
    return potencia, error


#Permite calcular la rapidez, la longitud de arco y la curvatura
#de la trayectoria helicoidal, asi como obtener la potencia
#luminosa total y el error estimado de la integral triple.
#Almacena los resultados para mostrarlos en la simulacion.
def calcular_resultados():
    rapidez = np.sqrt(
        (R0 * OMEGA)**2 + VZ**2
    )
    longitud = rapidez * TF
    curvatura = (
        R0 * OMEGA**2
        / ((R0 * OMEGA)**2 + VZ**2)
    )
    potencia, error = calcular_potencia()
    return {
        "rapidez": rapidez,
        "longitud": longitud,
        "curvatura": curvatura,
        "potencia": potencia,
        "error": error
    }


#Convierte el tiempo de la simulacion de segundos a minutos,
#segundos y milisegundos para mostrarlo en el cronometro
#de la interfaz con el formato MM:SS:mmm.
def formato_tiempo(segundos):
    total_ms = round(segundos * 1000)
    minutos = total_ms // 60000
    segundos = (total_ms // 1000) % 60
    milisegundos = total_ms % 1000
    return (
        f"{minutos:02d}:"
        f"{segundos:02d}:"
        f"{milisegundos:03d}"
    )


#BARRA SUPERIOR DE WINDOWS
#Permite cambiar el color de fondo y del texto de la barra superior
#de la ventana dependiendo del modo claro u oscuro seleccionado.
def cambiar_color_barra(ventana, oscuro):
    if sys.platform != "win32":
        return
    try:
        hwnd = int(ventana.winId())
        if oscuro:
            color_fondo = PANEL_OSCURO
            color_texto = "#FFFFFF"
        else:
            color_fondo = PANEL_CLARO
            color_texto = "#202936"
        def color_windows(hexadecimal):
            hexadecimal = hexadecimal.lstrip("#")
            rojo = int(hexadecimal[0:2], 16)
            verde = int(hexadecimal[2:4], 16)
            azul = int(hexadecimal[4:6], 16)
            return (
                rojo
                | (verde << 8)
                | (azul << 16)
            )
        dwm = ctypes.windll.dwmapi
        valor = ctypes.c_int(
            1 if oscuro else 0
        )
        resultado = dwm.DwmSetWindowAttribute(
            hwnd,
            20,
            ctypes.byref(valor),
            ctypes.sizeof(valor)
        )
        if resultado != 0:
            dwm.DwmSetWindowAttribute(
                hwnd,
                19,
                ctypes.byref(valor),
                ctypes.sizeof(valor)
            )
        fondo = ctypes.c_uint32(
            color_windows(color_fondo)
        )
        dwm.DwmSetWindowAttribute(
            hwnd,
            35,
            ctypes.byref(fondo),
            ctypes.sizeof(fondo)
        )
        texto = ctypes.c_uint32(
            color_windows(color_texto)
        )
        dwm.DwmSetWindowAttribute(
            hwnd,
            36,
            ctypes.byref(texto),
            ctypes.sizeof(texto)
        )
    except (OSError, AttributeError):
        pass


#EJES ESTILO GEOGEBRA
#Permite dibujar los tres ejes del sistema de coordenadas
#cartesianas, utilizando el color rojo para X, verde para Y
#y azul para Z, con flechas que indican su direccion positiva.
def dibujar_ejes(plotter):
    longitud = 5.5
    ejes = [
        (
            (-longitud, 0, 0),
            (longitud, 0, 0),
            "red"
        ),
        (
            (0, -longitud, 0),
            (0, longitud, 0),
            "green"
        ),
        (
            (0, 0, 0),
            (0, 0, H + 1),
            "blue"
        )
    ]
    for inicio, fin, color in ejes:
        plotter.add_mesh(
            pv.Line(inicio, fin),
            color=color,
            line_width=3
        )
    flechas = [
        ((5, 0, 0), (1, 0, 0), "red"),
        ((0, 5, 0), (0, 1, 0), "green"),
        ((0, 0, 10.5), (0, 0, 1), "blue")
    ]
    for origen, direccion, color in flechas:
        flecha = pv.Arrow(
            start=origen,
            direction=direccion,
            scale=0.5,
            tip_radius=0.10,
            shaft_radius=0.025
        )
        plotter.add_mesh(
            flecha,
            color=color
        )


#PLANO CON CUADRICULA
#Permite crear un plano horizontal con una cuadricula
#sobre los ejes X y Y para facilitar la ubicacion
#de los elementos dentro de la escena tridimensional.
def dibujar_plano(plotter):
    plano = pv.Plane(
        center=(0, 0, -0.05),
        direction=(0, 0, 1),
        i_size=12,
        j_size=12
    )
    actor_plano = plotter.add_mesh(
        plano,
        color="lightgray",
        opacity=0.18,
        lighting=False
    )
    actores_cuadricula = []
    for n in range(-6, 7):
        linea_horizontal = pv.Line(
            (-6, n, 0),
            (6, n, 0)
        )
        linea_vertical = pv.Line(
            (n, -6, 0),
            (n, 6, 0)
        )
        actor1 = plotter.add_mesh(
            linea_horizontal,
            color="gray",
            opacity=0.25,
            line_width=1
        )
        actor2 = plotter.add_mesh(
            linea_vertical,
            color="gray",
            opacity=0.25,
            line_width=1
        )
        actores_cuadricula.extend(
            [actor1, actor2]
        )
    return actor_plano, actores_cuadricula


#CILINDRO TRANSPARENTE
#Permite dibujar el cilindro transparente con el radio y la altura
#establecidos, representando el espacio donde se mueve la particula.
def dibujar_cilindro(plotter):
    cilindro = pv.Cylinder(
        center=(0, 0, H / 2),
        direction=(0, 0, 1),
        radius=R,
        height=H,
        resolution=100,
        capping=False
    )
    plotter.add_mesh(
        cilindro,
        color="steelblue",
        opacity=0.06,
        smooth_shading=True
    )


#CAPAS DE INTENSIDAD LUMINOSA
#Permite representar la intensidad luminosa mediante tres capas
#horizontales ubicadas a diferentes alturas dentro del cilindro.
#Los colores representan los diferentes valores de intensidad.
def dibujar_intensidad(plotter):
    rr = np.linspace(0, R, 35)
    theta = np.linspace(0, 2 * np.pi, 90)
    RR, TT = np.meshgrid(rr, theta)
    for altura in (2.0, 5.0, 8.0):
        XX = RR * np.cos(TT)
        YY = RR * np.sin(TT)
        ZZ = np.full_like(XX, altura)
        superficie = pv.StructuredGrid(
            XX, YY, ZZ
        )
        valores = intensidad(RR, altura)
        superficie.point_data["Intensidad"] = (
            valores.ravel(order="F")
        )
        plotter.add_mesh(
            superficie,
            scalars="Intensidad",
            cmap="inferno",
            clim=(I0, I0 + A * R**2),
            opacity=0.20,
            lighting=False,
            show_scalar_bar=False
        )


#VECTORES GRADIENTE
#Permite calcular y representar los vectores gradiente
#en diferentes puntos de la trayectoria helicoidal.
#Las flechas rojas se normalizan para representar la direccion
#de maximo aumento de la intensidad y no su magnitud real.
def dibujar_gradientes(plotter):
    tg = np.linspace(
        0.15,
        TF - 0.15,
        22
    )
    xg, yg, zg = trayectoria(tg)
    gx, gy, gz = gradiente_cartesiano(
        xg, yg, zg
    )
    for i in range(len(tg)):
        origen = np.array([
            xg[i],
            yg[i],
            zg[i]
        ])
        vector = np.array([
            gx[i],
            gy[i],
            gz[i]
        ])
        magnitud = np.linalg.norm(vector)
        if magnitud > 0:
            direccion = vector / magnitud
            flecha = pv.Arrow(
                start=origen,
                direction=direccion,
                scale=0.85,
                tip_radius=0.12,
                shaft_radius=0.025
            )
            plotter.add_mesh(
                flecha,
                color="red"
            )


#VENTANA PRINCIPAL
#Clase encargada de crear y configurar la ventana principal,
#los botones, los paneles y los temporizadores de la simulacion.
class VentanaSimulacion(QMainWindow):
    def __init__(self, resultados):
        super().__init__()
        self.resultados = resultados
        self.setWindowTitle(
            "Proyecto de Calculo Vectorial - Simulacion 3D"
        )
        self.resize(1300, 900)

        # ESTADO DE SIMULACION
        self.ejecutando = False
        self.tiempo_acumulado = 0.0
        self.inicio_intervalo = None
        self.tiempo_actual = 0.0

        # ESTADO VISUAL
        self.modo_oscuro = False
        self.vista_bloqueada = False
        self.rotacion_automatica = False
        self.ultimo_instante_rotacion = None

        # CONTENEDOR PRINCIPAL
        self.contenedor = QWidget()
        self.contenedor.setObjectName(
            "contenedorPrincipal"
        )
        self.setCentralWidget(
            self.contenedor
        )
        self.layout_principal = QVBoxLayout(
            self.contenedor
        )
        self.layout_principal.setContentsMargins(
            0, 0, 0, 0
        )
        self.layout_principal.setSpacing(0)

        # ESCENA 3D
        self.plotter = QtInteractor(
            self.contenedor,
            auto_update=False
        )
        self.layout_principal.addWidget(
            self.plotter,
            stretch=1
        )

        # PANEL INFERIOR
        self.panel = QWidget()
        self.panel.setObjectName(
            "panelControles"
        )
        self.layout_botones = QHBoxLayout(
            self.panel
        )
        self.layout_botones.setContentsMargins(
            8, 10, 8, 10
        )
        self.layout_botones.setSpacing(6)

        self.boton_inicio = QPushButton(
            "Iniciar simulación"
        )
        self.boton_reiniciar = QPushButton(
            "Reiniciar"
        )
        self.boton_vista = QPushButton(
            "⟲  Restaurar vista"
        )
        self.boton_rotacion = QPushButton(
            "⟳  Rotación automática"
        )
        self.boton_candado = QPushButton(
            "🔓  Bloquear vista"
        )
        self.boton_tema = QPushButton(
            "☾  Modo oscuro"
        )
        self.etiqueta_estado = QLabel(
            "Estado: Sin iniciar"
        )

        botones = [
            self.boton_inicio,
            self.boton_reiniciar,
            self.boton_vista,
            self.boton_rotacion,
            self.boton_candado,
            self.boton_tema
        ]

        for boton in botones:
            boton.setMinimumHeight(42)
            boton.setCursor(
                Qt.CursorShape.PointingHandCursor
            )
            self.layout_botones.addWidget(
                boton
            )

        self.layout_botones.addStretch()
        self.layout_botones.addWidget(
            self.etiqueta_estado
        )
        self.layout_principal.addWidget(
            self.panel
        )

        # CONEXIONES DE BOTONES
        self.boton_inicio.clicked.connect(
            self.iniciar_pausar
        )
        self.boton_reiniciar.clicked.connect(
            self.reiniciar
        )
        self.boton_vista.clicked.connect(
            self.restaurar_vista
        )
        self.boton_rotacion.clicked.connect(
            self.alternar_rotacion
        )
        self.boton_candado.clicked.connect(
            self.alternar_bloqueo
        )
        self.boton_tema.clicked.connect(
            self.cambiar_tema
        )

        # CREAR ESCENA
        self.crear_escena()
        self.camara_original = copy.deepcopy(
            self.plotter.camera_position
        )
        self.escala_original = (
            self.plotter.camera.parallel_scale
        )
        self.proyeccion_original = (
            self.plotter.camera.GetParallelProjection()
        )

        # PANELES INFORMATIVOS
        self.crear_leyenda()
        self.crear_panel_calculos()
        self.crear_panel_tiempo()
        self.plotter.installEventFilter(self)

        # TEMPORIZADOR DE PARTICULA
        self.timer = QTimer(self)
        self.timer.setTimerType(
            Qt.TimerType.PreciseTimer
        )
        self.timer.setInterval(20)
        self.timer.timeout.connect(
            self.actualizar_animacion
        )

        # TEMPORIZADOR DE ROTACION
        self.timer_rotacion = QTimer(self)
        self.timer_rotacion.setTimerType(
            Qt.TimerType.PreciseTimer
        )
        self.timer_rotacion.setInterval(20)
        self.timer_rotacion.timeout.connect(
            self.actualizar_rotacion
        )

        self.aplicar_tema()
        self.actualizar_posicion(0.0)


    #CREAR ESCENA 3D
    #Permite crear la escena tridimensional con el cilindro,
    #la trayectoria helicoidal, los gradientes, los ejes y la particula.
    #Tambien establece la posicion inicial de la camara.
    def crear_escena(self):
        plotter = self.plotter
        plotter.set_background(FONDO_CLARO)
        self.texto_titulo = plotter.add_text(
            "Trayectoria helicoidal y campo de iluminación",
            position="upper_edge",
            font_size=13,
            color="black"
        )

        (
            self.actor_plano,
            self.actores_cuadricula
        ) = dibujar_plano(plotter)

        dibujar_cilindro(plotter)
        dibujar_intensidad(plotter)

        # HELICE CON DOS COLORES
        # Azul claro: recorrido realizado.
        # Azul oscuro: recorrido pendiente.
        #
        # Son dos lineas independientes para
        # evitar que los colores se superpongan.
        self.cantidad_puntos = 1000
        self.tiempos_base = np.linspace(
            0,
            TF,
            self.cantidad_puntos
        )
        x, y, z = trayectoria(
            self.tiempos_base
        )
        puntos_helice = np.column_stack(
            (x, y, z)
        )
        self.helice_pendiente = (
            pv.lines_from_points(puntos_helice)
        )
        self.actor_helice_pendiente = (
            plotter.add_mesh(
                self.helice_pendiente,
                color=AZUL_HELICE,
                line_width=3,
                opacity=0.85
            )
        )

        # Recorrido inicialmente vacio
        x0, y0, z0 = trayectoria(0.0)
        punto_inicial = np.array([
            [x0, y0, z0]
        ])
        puntos_recorrido = np.repeat(
            punto_inicial,
            self.cantidad_puntos,
            axis=0
        )
        self.recorrido = pv.lines_from_points(
            puntos_recorrido
        )
        self.actor_recorrido = plotter.add_mesh(
            self.recorrido,
            color=AZUL_RECORRIDO,
            line_width=5,
            opacity=1.0
        )
        self.actor_recorrido.SetVisibility(False)

        # GRADIENTES Y EJES
        dibujar_gradientes(plotter)
        dibujar_ejes(plotter)
        self.actor_etiquetas = None
        self.crear_etiquetas_ejes()

        # PARTICULA NARANJA
        esfera = pv.Sphere(
            radius=0.20,
            center=(0, 0, 0),
            theta_resolution=32,
            phi_resolution=32
        )
        self.actor_particula = plotter.add_mesh(
            esfera,
            color="orange",
            smooth_shading=True
        )
        self.actor_particula.SetPosition(
            x0, y0, z0
        )

        # CAMARA INICIAL
        plotter.camera_position = [
            (17, -19, 14),
            (0, 0, 5),
            (0, 0, 1)
        ]
        plotter.camera.zoom(0.85)
        plotter.enable_trackball_style()
        plotter.render()


    #ETIQUETAS DE LOS EJES
    #Permite colocar las etiquetas X, Y y Z en los ejes
    #del sistema de coordenadas y cambiar su color
    #dependiendo del modo claro u oscuro seleccionado.
    def crear_etiquetas_ejes(self):
        if self.actor_etiquetas is not None:
            self.plotter.remove_actor(
                self.actor_etiquetas,
                render=False
            )

        color = (
            "white"
            if self.modo_oscuro
            else "black"
        )

        self.actor_etiquetas = (
            self.plotter.add_point_labels(
                np.array([
                    [6, 0, 0],
                    [0, 6, 0],
                    [0, 0, 11.5]
                ]),
                ["X", "Y", "Z"],
                font_size=15,
                text_color=color,
                show_points=False,
                always_visible=True,
                shape=None
            )
        )


    #PANEL DERECHO: SIMBOLOS
    #Permite crear el panel que muestra los nombres, colores
    #y simbolos de los elementos presentes en la simulacion.
    def crear_leyenda(self):
        self.leyenda = QFrame(
            self.plotter
        )
        self.leyenda.setObjectName(
            "leyendaSimulacion"
        )
        self.leyenda.setFixedWidth(225)

        layout = QVBoxLayout(
            self.leyenda
        )
        layout.setContentsMargins(
            14, 12, 14, 12
        )
        layout.setSpacing(9)

        titulo = QLabel(
            "Elementos de la simulación"
        )
        titulo.setObjectName(
            "tituloPanel"
        )
        layout.addWidget(titulo)

        elementos = [
            (
                "Hélice pendiente",
                "∿∿∿",
                AZUL_HELICE
            ),
            (
                "Gradiente",
                "⟶",
                "#E33434"
            ),
            (
                "Recorrido",
                "━━━━",
                AZUL_RECORRIDO
            ),
            (
                "Partícula",
                "●",
                "#FF9900"
            )
        ]

        for nombre, simbolo, color in elementos:
            fila = QWidget()
            fila.setObjectName(
                "filaLeyenda"
            )
            fila_layout = QHBoxLayout(
                fila
            )
            fila_layout.setContentsMargins(
                0, 0, 0, 0
            )

            etiqueta = QLabel(nombre)
            etiqueta.setObjectName(
                "textoPanel"
            )

            icono = QLabel(simbolo)
            icono.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            icono.setFixedWidth(55)
            icono.setStyleSheet(
                f"""
                color: {color};
                font-size: 24px;
                font-weight: bold;
                background: transparent;
                border: none;
                """
            )

            fila_layout.addWidget(
                etiqueta
            )
            fila_layout.addStretch()
            fila_layout.addWidget(
                icono
            )
            layout.addWidget(
                fila
            )

        self.leyenda.adjustSize()
        self.leyenda.show()
        self.leyenda.raise_()


    #PANEL IZQUIERDO DE CALCULOS
    #Permite crear el panel donde se muestran los resultados
    #de los calculos matematicos realizados en el proyecto.
    def crear_panel_calculos(self):
        self.panel_calculos = QFrame(
            self.plotter
        )
        self.panel_calculos.setObjectName(
            "panelCalculos"
        )
        self.panel_calculos.setFixedWidth(260)

        layout = QVBoxLayout(
            self.panel_calculos
        )
        layout.setContentsMargins(
            14, 12, 14, 12
        )
        layout.setSpacing(10)

        titulo = QLabel(
            "Resultados del cálculo vectorial"
        )
        titulo.setObjectName(
            "tituloPanel"
        )
        titulo.setWordWrap(True)
        layout.addWidget(titulo)

        datos = [
            (
                "Rapidez",
                f"{self.resultados['rapidez']:.4f} m/s"
            ),
            (
                "Longitud de arco",
                f"{self.resultados['longitud']:.4f} m"
            ),
            (
                "Curvatura",
                f"{self.resultados['curvatura']:.6f} 1/m"
            ),
            (
                "Potencia luminosa total",
                f"{self.resultados['potencia']:.4f} W"
            ),
            (
                "Error estimado",
                f"{self.resultados['error']:.2e}"
            )
        ]

        for nombre, valor in datos:
            bloque = QWidget()
            bloque.setObjectName(
                "bloqueCalculo"
            )
            bloque_layout = QVBoxLayout(
                bloque
            )
            bloque_layout.setContentsMargins(
                0, 2, 0, 2
            )
            bloque_layout.setSpacing(3)

            etiqueta_nombre = QLabel(
                nombre
            )
            etiqueta_nombre.setObjectName(
                "nombreCalculo"
            )

            etiqueta_valor = QLabel(
                valor
            )
            etiqueta_valor.setObjectName(
                "valorCalculo"
            )
            etiqueta_valor.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            bloque_layout.addWidget(
                etiqueta_nombre
            )
            bloque_layout.addWidget(
                etiqueta_valor
            )
            layout.addWidget(
                bloque
            )

        self.panel_calculos.adjustSize()
        self.panel_calculos.show()
        self.panel_calculos.raise_()


    #PANEL DEL TIEMPO SIMULADO CORREGIDO
    #Permite crear el panel donde se muestra el tiempo transcurrido
    #de la simulacion en minutos, segundos y milisegundos.
    def crear_panel_tiempo(self):
        self.panel_tiempo = QFrame(
            self.plotter
        )
        self.panel_tiempo.setObjectName(
            "panelTiempo"
        )
        self.panel_tiempo.setFixedSize(
            260, 115
        )

        layout = QVBoxLayout(
            self.panel_tiempo
        )
        layout.setContentsMargins(
            14, 12, 14, 12
        )
        layout.setSpacing(8)

        # Titulo del cronometro
        titulo = QLabel(
            "◷  Tiempo simulado"
        )
        titulo.setObjectName(
            "tituloPanel"
        )
        titulo.setFixedHeight(24)
        titulo.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        # Valor del cronometro
        self.etiqueta_tiempo = QLabel(
            "00:00:000"
        )
        self.etiqueta_tiempo.setObjectName(
            "valorTiempo"
        )
        self.etiqueta_tiempo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.etiqueta_tiempo.setMinimumHeight(
            45
        )
        self.etiqueta_tiempo.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(
            titulo
        )
        layout.addWidget(
            self.etiqueta_tiempo
        )

        self.panel_tiempo.show()
        self.panel_tiempo.raise_()


    #POSICIONAR PANELES
    #Permite establecer la posicion de los paneles informativos
    #de acuerdo con las dimensiones de la ventana.
    def posicionar_paneles(self):
        margen = 16
        altura = 55

        # Resultados arriba a la izquierda
        self.panel_calculos.move(
            margen,
            altura
        )

        # Leyenda arriba a la derecha
        x = (
            self.plotter.width()
            - self.leyenda.width()
            - margen
        )
        self.leyenda.move(
            max(margen, x),
            altura
        )

        # Cronometro abajo a la izquierda
        y_tiempo = (
            self.plotter.height()
            - self.panel_tiempo.height()
            - margen
        )
        self.panel_tiempo.move(
            margen,
            max(
                altura
                + self.panel_calculos.height()
                + 12,
                y_tiempo
            )
        )

        self.panel_calculos.raise_()
        self.leyenda.raise_()
        self.panel_tiempo.raise_()


    #ACTIVAR O DETENER ROTACION
    #Permite activar o detener la rotacion automatica de la camara
    #mediante el boton correspondiente.
    def alternar_rotacion(self):
        if not self.rotacion_automatica:
            self.rotacion_automatica = True
            self.ultimo_instante_rotacion = (
                time.perf_counter()
            )
            self.timer_rotacion.start()
            self.boton_rotacion.setText(
                "■  Detener rotación"
            )
        else:
            self.detener_rotacion()

        self.actualizar_estilo_rotacion()


    #DETENER ROTACION
    #Permite detener el movimiento automatico de la camara,
    #desactivar su temporizador y actualizar el texto
    #y la apariencia del boton de rotacion.
    def detener_rotacion(self):
        self.rotacion_automatica = False
        self.timer_rotacion.stop()
        self.ultimo_instante_rotacion = None
        self.boton_rotacion.setText(
            "⟳  Rotación automática"
        )
        self.actualizar_estilo_rotacion()


    #ACTUALIZAR ROTACION AUTOMATICA
    #Permite actualizar el angulo de rotacion de la camara
    #de acuerdo con el tiempo transcurrido y la velocidad establecida.
    def actualizar_rotacion(self):
        if not self.rotacion_automatica:
            return

        ahora = time.perf_counter()

        if self.ultimo_instante_rotacion is None:
            self.ultimo_instante_rotacion = ahora
            return

        delta_tiempo = (
            ahora - self.ultimo_instante_rotacion
        )
        self.ultimo_instante_rotacion = ahora
        delta_tiempo = min(
            delta_tiempo,
            0.1
        )
        angulo = (
            VELOCIDAD_ROTACION
            * delta_tiempo
        )

        camara = self.plotter.camera
        camara.Azimuth(angulo)
        camara.SetViewUp(0, 0, 1)
        camara.OrthogonalizeViewUp()
        self.plotter.render()


    #ESTILO DE BOTON DE ROTACION
    #Permite cambiar la apariencia del boton de rotacion
    #dependiendo de si se encuentra activado o desactivado.
    def actualizar_estilo_rotacion(self):
        if self.rotacion_automatica:
            self.boton_rotacion.setStyleSheet(
                """
                QPushButton {
                    background-color: #1677D2;
                    color: white;
                    border: 1px solid #1677D2;
                    font-size: 13px;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background-color: #105DA5;
                }
                """
            )
        else:
            if self.modo_oscuro:
                fondo = LEYENDA_OSCURA
                texto = "#F3F6FC"
                borde = "#46556D"
            else:
                fondo = LEYENDA_CLARA
                texto = "#202936"
                borde = "#D5DBE4"

            self.boton_rotacion.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {fondo};
                    color: {texto};
                    border: 1px solid {borde};
                    font-size: 13px;
                    border-radius: 6px;
                    padding: 8px 12px;
                }}
                QPushButton:hover {{
                    border: 1px solid #1677D2;
                }}
                """
            )


    #RESTAURAR VISTA ORIGINAL
    #Permite regresar la camara a su posicion y escala originales
    #sin reiniciar el movimiento de la particula ni el cronometro.
    def restaurar_vista(self):
        self.detener_rotacion()
        self.plotter.camera_position = (
            copy.deepcopy(
                self.camara_original
            )
        )
        self.plotter.camera.SetParallelProjection(
            self.proyeccion_original
        )
        self.plotter.camera.SetParallelScale(
            self.escala_original
        )
        self.plotter.render()

        # No se reinicia la particula
        # ni el cronometro.


    #BLOQUEAR O DESBLOQUEAR VISTA
    #Permite activar o desactivar el bloqueo de la vista
    #para controlar la interaccion del usuario con la camara.
    def alternar_bloqueo(self):
        self.vista_bloqueada = (
            not self.vista_bloqueada
        )

        if self.vista_bloqueada:
            self.boton_candado.setText(
                "🔒  Desbloquear vista"
            )
        else:
            self.boton_candado.setText(
                "🔓  Bloquear vista"
            )

        self.actualizar_estilo_candado()


    #EVENTOS DEL MOUSE
    #Permite controlar los eventos del mouse y los cambios
    #de tamaño de la escena, evitando modificar la vista
    #manualmente cuando se encuentra bloqueada.
    def eventFilter(self, objeto, evento):
        if objeto is self.plotter:
            tipo = evento.type()

            if tipo == QEvent.Type.Resize:
                QTimer.singleShot(
                    0,
                    self.posicionar_paneles
                )

            if self.vista_bloqueada:
                eventos_bloqueados = (
                    QEvent.Type.MouseButtonPress,
                    QEvent.Type.MouseButtonRelease,
                    QEvent.Type.MouseButtonDblClick,
                    QEvent.Type.MouseMove,
                    QEvent.Type.Wheel,
                    QEvent.Type.Gesture,
                    QEvent.Type.NativeGesture
                )

                if tipo in eventos_bloqueados:
                    return True

        return super().eventFilter(
            objeto,
            evento
        )


    #CAMBIAR TEMA
    #Permite alternar entre el modo claro y el modo oscuro
    #de la interfaz mediante el boton correspondiente.
    def cambiar_tema(self):
        self.modo_oscuro = (
            not self.modo_oscuro
        )
        self.aplicar_tema()


    #ESTILO DEL CANDADO
    #Permite cambiar la apariencia del boton del candado
    #dependiendo de si la vista esta bloqueada o desbloqueada.
    def actualizar_estilo_candado(self):

        if self.vista_bloqueada:
            self.boton_candado.setStyleSheet(
                """
                QPushButton {
                    background-color: #A33A45;
                    color: white;
                    border: 1px solid #C85560;
                    font-size: 13px;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background-color: #B84954;
                }
                """
            )
        else:
            if self.modo_oscuro:
                fondo = LEYENDA_OSCURA
                texto = "#F3F6FC"
                borde = "#46556D"
            else:
                fondo = LEYENDA_CLARA
                texto = "#202936"
                borde = "#D5DBE4"

            self.boton_candado.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {fondo};
                    color: {texto};
                    border: 1px solid {borde};
                    font-size: 13px;
                    border-radius: 6px;
                    padding: 8px 12px;
                }}
                QPushButton:hover {{
                    border: 1px solid #1677D2;
                }}
                """
            )


    #APLICAR MODO CLARO U OSCURO
    #Permite aplicar los colores correspondientes al tema
    #seleccionado, modificando el fondo de la escena,
    #los paneles, los botones, los textos y la cuadricula.
    def aplicar_tema(self):
        if self.modo_oscuro:
            fondo_3d = FONDO_OSCURO
            fondo_panel = PANEL_OSCURO
            fondo_leyenda = LEYENDA_OSCURA
            texto = "#F3F6FC"
            borde = "#46556D"

            color_cuadricula = (
                0.55, 0.60, 0.70
            )
            color_plano = (
                0.35, 0.40, 0.48
            )
            color_texto_vtk = (
                1.0, 1.0, 1.0
            )

            self.boton_tema.setText(
                "☀  Modo claro"
            )
        else:
            fondo_3d = FONDO_CLARO
            fondo_panel = PANEL_CLARO
            fondo_leyenda = LEYENDA_CLARA
            texto = "#202936"
            borde = "#D5DBE4"

            color_cuadricula = (
                0.50, 0.50, 0.50
            )
            color_plano = (
                0.83, 0.83, 0.83
            )
            color_texto_vtk = (
                0.0, 0.0, 0.0
            )

            self.boton_tema.setText(
                "☾  Modo oscuro"
            )

        # BARRA SUPERIOR
        cambiar_color_barra(
            self,
            self.modo_oscuro
        )

        # FONDO PRINCIPAL
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {fondo_3d};
            }}
            QWidget#contenedorPrincipal {{
                background-color: {fondo_3d};
            }}
            QWidget#panelControles {{
                background-color: {fondo_panel};
                border-top: 1px solid {borde};
            }}
            """
        )

        self.plotter.set_background(
            fondo_3d
        )

        # TITULO 3D
        self.texto_titulo.GetTextProperty().SetColor(
            *color_texto_vtk
        )

        # PLANO Y CUADRICULA
        self.actor_plano.GetProperty().SetColor(
            *color_plano
        )

        for actor in self.actores_cuadricula:
            actor.GetProperty().SetColor(
                *color_cuadricula
            )

        self.crear_etiquetas_ejes()

        # BOTON PRINCIPAL
        self.boton_inicio.setStyleSheet(
            """
            QPushButton {
                background-color: #1677D2;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #105DA5;
            }
            """
        )

        # BOTONES SECUNDARIOS
        estilo_botones = f"""
            QPushButton {{
                background-color: {fondo_leyenda};
                color: {texto};
                border: 1px solid {borde};
                font-size: 13px;
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                border: 1px solid #1677D2;
            }}
        """

        self.boton_reiniciar.setStyleSheet(
            estilo_botones
        )
        self.boton_vista.setStyleSheet(
            estilo_botones
        )
        self.boton_tema.setStyleSheet(
            estilo_botones
        )

        self.actualizar_estilo_rotacion()
        self.actualizar_estilo_candado()

        self.etiqueta_estado.setStyleSheet(
            f"""
            color: {texto};
            font-size: 12px;
            background: transparent;
            """
        )

        # ESTILO DE LOS TRES PANELES
        estilo_paneles = f"""
            QFrame#leyendaSimulacion,
            QFrame#panelCalculos,
            QFrame#panelTiempo {{
                background-color: {fondo_leyenda};
                border: 1px solid {borde};
                border-radius: 12px;
            }}

            QLabel#tituloPanel {{
                color: {texto};
                font-size: 13px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}

            QLabel#textoPanel {{
                color: {texto};
                font-size: 12px;
                background: transparent;
                border: none;
            }}

            QLabel#nombreCalculo {{
                color: {texto};
                font-size: 12px;
                background: transparent;
                border: none;
            }}

            QLabel#valorCalculo {{
                color: #45A8FF;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}

            QLabel#valorTiempo {{
                color: #45A8FF;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Consolas;
                padding: 0px;
                margin: 0px;
            }}

            QWidget#filaLeyenda,
            QWidget#bloqueCalculo {{
                background: transparent;
                border: none;
            }}
        """

        self.leyenda.setStyleSheet(
            estilo_paneles
        )
        self.panel_calculos.setStyleSheet(
            estilo_paneles
        )
        self.panel_tiempo.setStyleSheet(
            estilo_paneles
        )

        self.plotter.render()


    #INICIAR O PAUSAR SIMULACION
    #Permite iniciar, pausar y reanudar el movimiento de la particula,
    #conservando el tiempo acumulado durante la simulacion.
    def iniciar_pausar(self):
        if not self.ejecutando:
            self.inicio_intervalo = (
                time.perf_counter()
            )
            self.ejecutando = True
            self.timer.start()
            self.boton_inicio.setText(
                "Pausar simulación"
            )
            self.etiqueta_estado.setText(
                "Estado: En ejecución"
            )
        else:
            ahora = time.perf_counter()
            self.tiempo_acumulado += (
                ahora - self.inicio_intervalo
            )
            self.ejecutando = False
            self.timer.stop()
            self.boton_inicio.setText(
                "Reanudar simulación"
            )
            self.etiqueta_estado.setText(
                "Estado: En pausa"
            )
            self.actualizar_posicion(
                self.tiempo_acumulado % TF
            )


    #REINICIAR SIMULACION
    #Permite detener la simulacion, regresar la particula
    #a su posicion inicial y establecer el cronometro en cero.
    def reiniciar(self):
        self.timer.stop()
        self.ejecutando = False
        self.tiempo_acumulado = 0.0
        self.inicio_intervalo = None
        self.tiempo_actual = 0.0

        self.boton_inicio.setText(
            "Iniciar simulación"
        )
        self.etiqueta_estado.setText(
            "Estado: Sin iniciar"
        )

        # La rotacion sigue independiente
        self.actualizar_posicion(0.0)


    #ACTUALIZAR ANIMACION
    #Permite calcular el tiempo transcurrido y actualizar
    #la posicion de la particula durante la simulacion.
    #Repite el recorrido al completar el tiempo establecido.
    def actualizar_animacion(self):
        if not self.ejecutando:
            return

        ahora = time.perf_counter()
        transcurrido = (
            self.tiempo_acumulado
            + ahora
            - self.inicio_intervalo
        )
        tiempo_actual = transcurrido % TF

        self.actualizar_posicion(
            tiempo_actual
        )


    #ACTUALIZAR PARTICULA Y RECORRIDO
    #Permite actualizar la posicion de la particula en la trayectoria
    #helicoidal de acuerdo con el tiempo transcurrido.
    #Tambien actualiza el recorrido realizado, el recorrido pendiente
    #y el tiempo mostrado en el cronometro.
    def actualizar_posicion(self, tiempo):
        self.tiempo_actual = tiempo

        # POSICION DE LA PARTICULA
        xp, yp, zp = trayectoria(tiempo)
        self.actor_particula.SetPosition(
            float(xp),
            float(yp),
            float(zp)
        )

        # RECORRIDO AZUL CLARO
        # Solo aparece en la parte que
        # ya recorrio la particula.
        tiempos_recorridos = np.minimum(
            self.tiempos_base,
            tiempo
        )
        xr, yr, zr = trayectoria(
            tiempos_recorridos
        )
        puntos_recorridos = np.column_stack(
            (xr, yr, zr)
        )
        self.recorrido.points = (
            puntos_recorridos
        )

        # HELICE AZUL OSCURO
        # Solo aparece en la parte que
        # falta recorrer.
        tiempos_pendientes = np.maximum(
            self.tiempos_base,
            tiempo
        )
        xh, yh, zh = trayectoria(
            tiempos_pendientes
        )
        puntos_pendientes = np.column_stack(
            (xh, yh, zh)
        )
        self.helice_pendiente.points = (
            puntos_pendientes
        )

        self.actor_recorrido.SetVisibility(
            tiempo > 0.0001
        )
        self.actor_helice_pendiente.SetVisibility(
            tiempo < TF - 0.0001
        )

        # ACTUALIZAR CRONOMETRO
        self.etiqueta_tiempo.setText(
            formato_tiempo(tiempo)
        )
        self.plotter.render()


    #CERRAR VENTANA
    #Permite detener los temporizadores de la particula
    #y de la rotacion automatica, ademas de cerrar
    #correctamente la visualizacion tridimensional.
    def closeEvent(self, evento):
        self.timer.stop()
        self.timer_rotacion.stop()
        self.plotter.close()
        evento.accept()


#RESULTADOS EN TERMINAL
#Permite mostrar en la terminal los resultados obtenidos
#de los calculos matematicos junto con sus unidades
#y el error estimado de la integracion numerica.
def mostrar_resultados(resultados):
    print("===================================")
    print(" RESULTADOS DEL CALCULO VECTORIAL")
    print("===================================")

    print(
        f"Rapidez: "
        f"{resultados['rapidez']:.4f} m/s"
    )
    print(
        f"Longitud de arco: "
        f"{resultados['longitud']:.4f} m"
    )
    print(
        f"Curvatura: "
        f"{resultados['curvatura']:.6f} 1/m"
    )
    print(
        f"Potencia luminosa total: "
        f"{resultados['potencia']:.4f} W"
    )
    print(
        f"Error estimado: "
        f"{resultados['error']:.2e}"
    )


#PROGRAMA PRINCIPAL
#Permite realizar los calculos matematicos, mostrar los resultados
#en la terminal, crear la ventana principal e iniciar
#la ejecucion de la interfaz grafica de la simulacion.
def main():
    resultados = calcular_resultados()
    mostrar_resultados(resultados)

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    ventana = VentanaSimulacion(
        resultados
    )
    ventana.show()

    # Colocar paneles en sus posiciones
    QTimer.singleShot(
        0,
        ventana.posicionar_paneles
    )

    # Aplicar color a la barra de Windows
    QTimer.singleShot(
        100,
        lambda: cambiar_color_barra(
            ventana,
            ventana.modo_oscuro
        )
    )

    sys.exit(app.exec())


#Permite ejecutar la funcion main cuando el archivo
#se ejecuta directamente como programa principal.
if __name__ == "__main__":
    main()