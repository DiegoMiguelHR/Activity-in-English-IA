# -*- coding: utf-8 -*-
"""================================================================================
    GENERAR INFORME: construye el documento Word final del proyecto
    "Activity in English" - Comparativa de Modelos de Clasificacion.

    Contenido:
      - Portada (facultad, tema, curso, docente, integrantes, ciudad-anio)
      - Fase 1: Matriz Teorica
      - Fase 2: El Reto de Clasificacion (dataset, pipeline, optimizacion,
        validacion cruzada, resultados y figuras)
      - Fase 3: El Veredicto (analisis comparativo final)
      - Anexo: reproducibilidad

    USO:
        python generar_informe.py
================================================================================
"""

import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BASE = os.path.dirname(os.path.abspath(__file__))
GRAF = os.path.join(BASE, "ActividadIngles", "graficos")
OUT_PATH = os.path.join(BASE, "Activity in English - INFORME FINAL.docx")

AZUL = RGBColor(0x1F, 0x4E, 0x79)

# ----------------------------------------------------------------------------
# Utilidades de formato
# ----------------------------------------------------------------------------
def configurar_documento(doc):
    """Estilo base: fuente Calibri 11, titulos en azul oscuro."""
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")

    for level, size in [("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 12)]:
        st = doc.styles[level]
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.color.rgb = AZUL
        st.font.bold = True
        # quitar el azul de hipervinculo de los titulos
        st.element.get_or_add_rPr()


def parrafo_justificado(doc, texto, negritas_inicial=False):
    p = doc.add_paragraph(texto)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def add_tabla(doc, encabezados, filas, anchos=None):
    """Tabla con bordes, primera fila en negrita y fondo suave."""
    tabla = doc.add_table(rows=1 + len(filas), cols=len(encabezados))
    tabla.style = "Table Grid"
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER

    for j, h in enumerate(encabezados):
        celda = tabla.cell(0, j)
        celda.text = ""
        run = celda.paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        shd = celda._tc.get_or_add_tcPr()
        from docx.oxml import OxmlElement
        el = OxmlElement("w:shd")
        el.set(qn("w:val"), "clear")
        el.set(qn("w:color"), "auto")
        el.set(qn("w:fill"), "DCE6F1")
        shd.append(el)

    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            celda = tabla.cell(i + 1, j)
            celda.text = ""
            run = celda.paragraphs[0].add_run(str(valor))
            run.font.size = Pt(10)

    if anchos:
        for j, ancho in enumerate(anchos):
            for i in range(len(filas) + 1):
                tabla.cell(i, j).width = Inches(ancho)
    return tabla


def add_figura(doc, ruta, titulo, ancho=6.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(ruta, width=Inches(ancho))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(titulo)
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def add_figura_en_celda(celda, ruta, titulo, ancho=2.9):
    p = celda.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(ruta, width=Inches(ancho))
    cap = celda.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(titulo)
    r.italic = True
    r.font.size = Pt(8)
    r.font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def add_codigo(doc, codigo):
    for linea in codigo.strip("\n").splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.35)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(linea if linea else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(9)
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")


# ----------------------------------------------------------------------------
# Documento
# ----------------------------------------------------------------------------
doc = Document()
configurar_documento(doc)

# ============================ PORTADA ========================================
for _ in range(4):
    doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("UNIVERSIDAD ANDINA DEL CUSCO")
r.bold = True
r.font.size = Pt(22)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("FACULTAD DE INGENIERÍA Y ARQUITECTURA")
r.bold = True
r.font.size = Pt(15)

for _ in range(5):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('"Activity in English"')
r.bold = True
r.font.size = Pt(26)
r.font.color.rgb = AZUL

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Comparativa de Modelos de Clasificación con Aprendizaje Supervisado")
r.font.size = Pt(13)

for _ in range(4):
    doc.add_paragraph()

datos = [
    ("CURSO:", "Inteligencia Artificial"),
    ("DOCENTE:", "Espetia Huamanga, Hugo"),
]
for etiqueta, valor in datos:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(etiqueta + " ")
    r.bold = True
    r.font.size = Pt(12)
    r = p.add_run(valor)
    r.font.size = Pt(12)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("INTEGRANTES:")
r.bold = True
r.font.size = Pt(12)

integrantes = [
    "Huamantalla Ríos, Diego Miguel   -   022100354D",
    "Latorre Campos, Andre Ismael     -   022101034C",
    "Ordóñez Paniura, Marcela Leonor  -   022100735H",
    "Suel Monrroy, David Joshua       -   022101091G",
]
for nombre in integrantes:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(nombre)
    r.font.size = Pt(12)

for _ in range(4):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("CUSCO – PERÚ")
r.bold = True
r.font.size = Pt(13)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("2026")
r.bold = True
r.font.size = Pt(13)

doc.add_page_break()

# ===================== PRESENTACION DEL PROYECTO =============================
doc.add_heading("Presentación del Proyecto", level=1)

parrafo_justificado(
    doc,
    "El presente trabajo aborda la aplicación práctica de cuatro modelos de clasificación "
    "supervisada sobre un problema de datos de sensores ambientales. La actividad se organiza "
    "en tres fases: (1) selección estratégica y análisis teórico de los modelos, (2) reto de "
    "clasificación con experimentación y validación rigurosa, y (3) veredicto final comparativo "
    "sobre el mejor modelo en términos de rendimiento y costo computacional.",
)
parrafo_justificado(
    doc,
    "Los cuatro modelos seleccionados pertenecen a familias matemáticas distintas, tal como "
    "exige la actividad: Support Vector Machines (SVM) y K-Nearest Neighbors (KNN) de la familia "
    "geométrica y basada en distancias; Gaussian Naive Bayes de la familia probabilística; y "
    "Gradient Boosting de la familia de ensembles. El conjunto de datos elegido fue el "
    "\u201cOccupancy Detection Dataset\u201d, sobre el cual los cuatro algoritmos compitieron en "
    "igualdad de condiciones mediante un pipeline unificado de preprocesamiento.",
)

# ============================ FASE 1 =========================================
doc.add_heading("Fase 1: Matriz Teórica", level=1)

parrafo_justificado(
    doc,
    "De acuerdo con las reglas de la actividad, cada equipo debía seleccionar cuatro modelos "
    "asegurando al menos uno por familia matemática. La selección realizada fue:",
)
parrafo_justificado(
    doc,
    "\u2022  Familia 1 (Geométrica y basada en distancias): Support Vector Machines (SVM) y "
    "K-Nearest Neighbors (KNN), evaluando distintos kernels y métricas de distancia.\n"
    "\u2022  Familia 2 (Probabilística y generativa): Naive Bayes Gaussiano (GaussianNB).\n"
    "\u2022  Familia 3 (Ensembles y estocásticos): Gradient Boosting.",
)
parrafo_justificado(
    doc,
    "La Tabla 1 contrasta los cuatro modelos según los cuatro criterios solicitados: principio "
    "matemático central, sensibilidad a valores atípicos, costo computacional y supuestos sobre "
    "la distribución de los datos.",
)

add_tabla(
    doc,
    ["Modelo", "Principio Matemático", "Sensibilidad a Outliers",
     "Costo Computacional", "Supuestos sobre la Distribución de Datos"],
    [
        ["Support Vector Machines (SVM)",
         "Maximización del margen (distancia) entre clases usando hiperplanos. Aplica el \u201ckernel trick\u201d para proyectar los datos a dimensiones superiores.",
         "Baja a Media. Depende fuertemente de los vectores de soporte: si un outlier está cerca del margen, puede desviar el hiperplano.",
         "Alto. El entrenamiento escala de forma cuadrática con el número de instancias (O(n²)), y requiere ajustar C, gamma y el kernel.",
         "No asume ninguna distribución subyacente específica (modelo no paramétrico); solo depende de la geometría de los datos."],
        ["Gaussian Naive Bayes (GNB)",
         "Teorema de Bayes junto con la presunción de independencia condicional entre las variables predictoras.",
         "Moderada a Alta. Al estimar medias y varianzas, los valores extremos pueden sesgar los parámetros de las distribuciones.",
         "Muy Bajo. Altamente eficiente en entrenamiento y predicción; requiere pocos recursos.",
         "Asume que las variables numéricas siguen una distribución Normal (Gaussiana) y que todas las variables son independientes entre sí."],
        ["Gradient Boosting",
         "Ensemble estocástico y secuencial: combina iterativamente árboles de decisión débiles, donde cada nuevo árbol minimiza los errores residuales del anterior mediante descenso de gradiente.",
         "Baja. Es robusto frente a outliers gracias a los árboles base y a funciones de pérdida robustas.",
         "Muy Alto. Entrena múltiples árboles de forma secuencial (no nativamente paralelizable como Random Forest), con gran demanda de tiempo y memoria.",
         "No hace supuestos matemáticos sobre la distribución de los datos ni sobre la relación espacial entre variables."],
        ["K-Nearest Neighbors (KNN)",
         "Clasificación basada en la distancia espacial (euclidiana, Manhattan, etc.) respecto a los k vecinos más cercanos en el espacio de características.",
         "Alta. Al depender de métricas de distancia, un outlier aislado puede convertirse erróneamente en el \u201cvecino más cercano\u201d de un dato nuevo.",
         "Bajo en entrenamiento, alto en predicción (lazy learning). Calcular distancias contra todas las instancias es costoso en datasets grandes.",
         "No asume distribución previa, pero sí asume que datos con características similares pertenecen a la misma clase (localidad espacial)."],
    ],
    anchos=[1.05, 1.75, 1.45, 1.50, 1.75],
)

cap = doc.add_paragraph("Tabla 1. Matriz comparativa teórica de los cuatro modelos de clasificación.")
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.runs[0].italic = True
cap.runs[0].font.size = Pt(9)

doc.add_page_break()

# ============================ FASE 2 =========================================
doc.add_heading("Fase 2: El Reto de Clasificación", level=1)

# ---- 2.1 Dataset ----
doc.add_heading("2.1. Conjunto de datos: Occupancy Detection", level=2)

parrafo_justificado(
    doc,
    "Se seleccionó el \u201cOccupancy Detection Dataset\u201d, un problema de clasificación de "
    "datos de sensores ambientales (la categoría sugerida de \u201cenvironmental sensor "
    "data\u201d). El objetivo es predecir si una sala está ocupada (1) o vacía (0) a partir de "
    "lecturas de sensores que se registran aproximadamente cada minuto.",
)
parrafo_justificado(
    doc,
    "El conjunto original se distribuye en dos archivos (entrenamiento y prueba). Para este "
    "experimento se concatenaron ambos, obteniendo un total de 17,895 instancias, superando con "
    "holgura el mínimo exigido de 2,500. Se eliminaron dos columnas no predictivas: la de índice "
    "sin nombre (\u201cUnnamed: 0\u201d) y la de fecha/hora (\u201cdate\u201d), ya que su uso "
    "podría introducir artefactos temporales y contaminación de información.",
)

add_tabla(
    doc,
    ["Variable", "Descripción", "Tipo"],
    [
        ["Temperature", "Temperatura del ambiente (°C)", "Predictora numérica"],
        ["Humidity", "Humedad relativa (%)", "Predictora numérica"],
        ["Light", "Intensidad de la luz (lux)", "Predictora numérica"],
        ["CO2", "Dióxido de carbono en el aire (ppm)", "Predictora numérica"],
        ["HumidityRatio", "Razón de humedad (kg agua / kg aire seco)", "Predictora numérica"],
        ["Occupancy", "Estado de la sala: 0 = vacía, 1 = ocupada", "Objetivo binario"],
    ],
    anchos=[1.6, 3.4, 1.7],
)
cap = doc.add_paragraph("Tabla 2. Variables del dataset. Cinco predictores numéricos y una variable objetivo binaria.")
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.runs[0].italic = True
cap.runs[0].font.size = Pt(9)

doc.add_paragraph()
p = doc.add_paragraph()
r = p.add_run("Distribución de clases: ")
r.bold = True
parrafo_justificado(
    doc,
    "14,117 instancias de sala vacía (78.9%) frente a 3,778 de sala ocupada (21.1%). El conjunto "
    "está desbalanceado, por lo que la precisión (accuracy) no sería una métrica fiable: un "
    "clasificador que siempre predijera \u201cvacía\u201d alcanzaría un 78.9% de acierto sin "
    "aprender nada. Por ello, la métrica de evaluación principal es el F1-Score promedio (macro).",
)

# ---- 2.2 Pipeline ----
doc.add_heading("2.2. Pipeline unificado de preprocesamiento", level=2)
parrafo_justificado(
    doc,
    "Para que los cuatro modelos compitan en igualdad de condiciones, se construyó un pipeline "
    "único compuesto por un StandardScaler (normalización z-score) seguido del clasificador. El "
    "escalado es imprescindible para los modelos basados en distancias (KNN) y en márgenes (SVM), "
    "ya que variables como la luz (cientos de lux) y la razón de humedad (unidades de 10⁻³) "
    "tienen escalas muy dispares.",
)
parrafo_justificado(
    doc,
    "Es importante destacar que el StandardScaler se encuentra dentro del Pipeline que se pasa "
    "al GridSearchCV: de esta forma, las estadísticas del escalado se aprenden únicamente con los "
    "pliegues de entrenamiento de cada validación, evitando la fuga de datos (data leakage).",
)
add_codigo(doc, """
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", clasificador),
    ])
""")

# ---- 2.3 Optimizacion ----
doc.add_heading("2.3. Entrenamiento y optimización de hiperparámetros", level=2)
parrafo_justificado(
    doc,
    "Cada modelo se optimizó mediante GridSearchCV, búsqueda exhaustiva sobre las cuadrículas de "
    "hiperparámetros mostradas en la Tabla 3, utilizando como métrica de búsqueda el F1-Score "
    "promedio (macro). Para SVM se evaluaron tres kernels distintos (análisis de kernels) y para "
    "KNN dos métricas de distancia (evaluación de métricas de distancia), conforme a lo pedido "
    "por la familia geométrica.",
)

add_tabla(
    doc,
    ["Modelo", "Cuadrícula de hiperparámetros (GridSearch)", "N.º de combinaciones"],
    [
        ["SVC", "kernel: [rbf, linear, poly] · C: [0.1, 1, 10] · gamma: [0.01, 0.1, 1]", "27"],
        ["GaussianNB", "var_smoothing: [1e-9, 1e-8, 1e-7]", "3"],
        ["GradientBoosting", "n_estimators: [50, 100] · max_depth: [2, 4] · learning_rate: [0.05, 0.1]", "8"],
        ["KNN", "n_neighbors: [3, 5, 7] · weights: [uniform, distance] · metric: [euclidean, manhattan]", "12"],
    ],
    anchos=[1.5, 3.6, 1.6],
)
cap = doc.add_paragraph("Tabla 3. Cuadrículas de hiperparámetros evaluadas por GridSearchCV para cada modelo.")
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.runs[0].italic = True
cap.runs[0].font.size = Pt(9)

# ---- 2.4 Validacion ----
doc.add_heading("2.4. Validación cruzada", level=2)
parrafo_justificado(
    doc,
    "Para garantizar que los resultados no dependan de una partición afortunada, se utilizó "
    "validación cruzada estratificada con 5 pliegues (StratifiedKFold, 5 splits, shuffle=True, "
    "random_state=42). La versión estratificada mantiene la proporción original de clases "
    "(78.9% / 21.1%) en cada pliegue, lo cual es lo más riguroso dado el desbalanceo del conjunto. "
    "El F1-Score reportado es el promedio de los cinco pliegues.",
)

# ---- 2.5 Resultados ----
doc.add_heading("2.5. Resultados del experimento", level=2)
parrafo_justificado(
    doc,
    "La Tabla 4 resume el rendimiento final de cada modelo tras la optimización. KNN obtuvo el "
    "mejor F1-Score macro (0.9923) con la menor carga computacional entre los tres primeros. "
    "Los mejores hiperparámetros encontrados fueron:",
)

add_tabla(
    doc,
    ["Modelo", "F1-Score (macro)", "Accuracy", "Precision (macro)", "Recall (macro)",
     "Tiempo total (s)", "Mejores hiperparámetros"],
    [
        ["KNN", "0.9923", "0.9949", "0.9912", "0.9934", "1.21",
         "n_neighbors=5, weights='distance', metric='euclidean'"],
        ["SVC", "0.9900", "0.9933", "0.9869", "0.9931", "34.51",
         "C=10, gamma=1, kernel='rbf'"],
        ["GradientBoosting", "0.9886", "0.9923", "0.9866", "0.9906", "8.75",
         "n_estimators=100, max_depth=4, learning_rate=0.1"],
        ["GaussianNB", "0.9530", "0.9670", "0.9327", "0.9784", "0.17",
         "var_smoothing=1e-9"],
    ],
    anchos=[1.4, 0.85, 0.7, 0.95, 0.9, 0.85, 1.9],
)
cap = doc.add_paragraph("Tabla 4. Resultados finales: F1-Score macro promedio de validación cruzada (StratifiedKFold, 5 pliegues). Las métricas de precisión/recall/accuracy se estimaron con predicciones out-of-fold.")
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.runs[0].italic = True
cap.runs[0].font.size = Pt(9)

doc.add_paragraph()
add_figura(doc, os.path.join(GRAF, "resultados_f1.png"),
           "Figura 1. F1-Score macro promedio de validación cruzada por modelo.", 5.6)
add_figura(doc, os.path.join(GRAF, "resultados_tiempo.png"),
           "Figura 2. Tiempo computacional total (búsqueda + entrenamiento) por modelo.", 5.6)

doc.add_page_break()

doc.add_heading("2.6. Análisis de kernels en SVM y métricas de distancia en KNN", level=2)

parrafo_justificado(
    doc,
    "Tal como exige la familia geométrica, se analizaron distintos kernels para SVM. El kernel "
    "RBF fue claramente superior, seguido del lineal y del polinomial. En cuanto a KNN, la "
    "métrica euclidiana superó apenas a la de Manhattan, lo que indica que la estructura "
    "geométrica del problema favorece la distancia en línea recta.",
)
add_figura(doc, os.path.join(GRAF, "comparacion_kernels.png"),
           "Figura 3. Mejor F1-Score alcanzado por cada kernel de SVM.", 5.4)
add_figura(doc, os.path.join(GRAF, "comparacion_metricas.png"),
           "Figura 4. Mejor F1-Score alcanzado por cada métrica de distancia en KNN.", 5.4)

doc.add_heading("2.7. Matrices de confusión", level=2)
parrafo_justificado(
    doc,
    "Las matrices de confusión se construyeron con predicciones out-of-fold (cada instancia fue "
    "predicha por un modelo entrenado sin ella). Permiten cuantificar los errores de cada modelo:",
)

tabla_cm = doc.add_table(rows=2, cols=2)
tabla_cm.style = "Table Grid"
tabla_cm.alignment = WD_TABLE_ALIGNMENT.CENTER
add_figura_en_celda(tabla_cm.cell(0, 0), os.path.join(GRAF, "confusion_KNN.png"),
                    "KNN — errores: 58 FP, 34 FN")
add_figura_en_celda(tabla_cm.cell(0, 1), os.path.join(GRAF, "confusion_SVC.png"),
                    "SVC — errores: 93 FP, 27 FN")
add_figura_en_celda(tabla_cm.cell(1, 0), os.path.join(GRAF, "confusion_GradientBoosting.png"),
                    "GradientBoosting — errores: 90 FP, 47 FN")
add_figura_en_celda(tabla_cm.cell(1, 1), os.path.join(GRAF, "confusion_GaussianNB.png"),
                    "GaussianNB — errores: 584 FP, 7 FN")
doc.add_paragraph()
cap = doc.add_paragraph("Figuras 5–8. Matrices de confusión de los cuatro modelos (predicciones out-of-fold). FP = falsos positivos, FN = falsos negativos.")
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.runs[0].italic = True
cap.runs[0].font.size = Pt(9)

doc.add_heading("2.8. Aplicación interactiva (Streamlit)", level=2)
parrafo_justificado(
    doc,
    "Adicionalmente se desarrolló una interfaz web con Streamlit (app_occupancy.py) que replica "
    "el experimento y permite ejecutarlo con un botón, mostrando la tabla de resultados, los "
    "mejores hiperparámetros por modelo y un gráfico de barras interactivo del F1-Score. Su uso "
    "favoreció la obtención ordenada de capturas para el informe.",
)
add_figura(doc, os.path.join(GRAF, "captura_streamlit.png"),
           "Figura 9. Captura de la aplicación Streamlit con la comparativa de modelos.", 5.0)

doc.add_page_break()

# ============================ FASE 3 =========================================
doc.add_heading("Fase 3: El Veredicto", level=1)
parrafo_justificado(
    doc,
    "Con los resultados de la experimentación se responde a continuación a las tres preguntas "
    "del análisis final.",
)

doc.add_heading("3.1. Balance entre exactitud y capacidad de generalización (F1-Score)", level=2)
parrafo_justificado(
    doc,
    "Tras la validación cruzada estratificada, el modelo que demostró el mejor equilibrio entre "
    "exactitud y generalización fue KNN, con un sobresaliente F1-Score macro de 0.9923 y una "
    "exactitud de 0.9949. Esta métrica balancea de forma casi perfecta los falsos positivos y "
    "falsos negativos al predecir la ocupación de la sala (58 FP y 34 FN sobre 17,895 instancias), "
    "superando por un margen notable al modelo de menor rendimiento, Gaussian Naive Bayes, que "
    "alcanzó 0.9530 (con 584 falsos positivos: predijo \u201cocupada\u201d en 584 lecturas de "
    "sala vacía). El uso de F1-macro garantiza que el resultado no esté distorsionado por el "
    "desbalanceo de clases (78.9% de salas vacías).",
)

doc.add_heading("3.2. ¿El modelo más complejo justificó su costo computacional?", level=2)
parrafo_justificado(
    doc,
    "No. En este experimento, los modelos matemáticamente más complejos NO justificaron su alto "
    "costo computacional. Mientras que SVC (34.51 s) y Gradient Boosting (8.75 s) alcanzaron "
    "F1-Scores ligeramente inferiores (0.9900 y 0.9886), KNN obtuvo el puntaje ganador "
    "(0.9923) ejecutando todo el proceso en apenas 1.21 segundos, y GaussianNB lo hizo en 0.17 s. "
    "La simplicidad de calcular distancias euclidianas venció ampliamente al esfuerzo de construir "
    "árboles secuenciales o de proyectar hiperplanos multidimensionales. El sobrecosto de SVC y "
    "Boosting no se tradujo en una mejora de rendimiento, por lo que, para este problema, la "
    "complejidad adicional no es rentable.",
)
add_figura(doc, os.path.join(GRAF, "resultados_f1_tiempo.png"),
           "Figura 10. Balance rendimiento (F1-Score) frente a costo computacional: el cuadrante óptimo es arriba-izquierda.", 5.6)

doc.add_heading("3.3. Límites de decisión y dimensionalidad del problema", level=2)
parrafo_justificado(
    doc,
    "El dataset cuenta con cinco variables ambientales (Temperature, Humidity, Light, CO2, "
    "HumidityRatio). Proyectando los datos sobre sus dos primeras componentes PCA se retiene "
    "aproximadamente el 82% de la varianza (46.4% + 35.8%), lo que indica una estructura "
    "intrínsecamente de baja dimensión. En esa proyección (Figura 11) se observa que las clases "
    "(sala vacía vs. sala ocupada) forman clústeres densos y espacialmente separados: cuando hay "
    "personas, la luz y el CO2 se elevan de forma simultánea, agrupando los puntos de la clase "
    "ocupada.",
)
parrafo_justificado(
    doc,
    "Esta estructura explica el triunfo de KNN: trazó límites de decisión basados puramente en la "
    "proximidad de los datos, sin supuestos rígidos, y su frontera prácticamente coincide con la "
    "separación natural de los clústeres. SVC (kernel RBF) y Gradient Boosting lograron fronteras "
    "casi equivalentes, pero a un costo computacional mucho mayor. En el extremo opuesto, "
    "GaussianNB trazó una frontera probabilística demasiado rígida: al asumir independencia y "
    "normalidad entre variables que en realidad están correlacionadas (Luz y CO2, por su vínculo "
    "con la presencia de personas; Temperatura y HumidityRatio), su límite quedó desplazado y "
    "produjo la mayor cantidad de falsos positivos de los cuatro modelos. La baja dimensionalidad "
    "efectiva impidió la maldición de la dimensionalidad, beneficiando a las técnicas basadas en "
    "distancias por encima de las fronteras paramétricas de Naive Bayes.",
)
add_figura(doc, os.path.join(GRAF, "fronteras_decision_PCA.png"),
           "Figura 11. Fronteras de decisión de los cuatro modelos proyectadas sobre las dos primeras componentes PCA.", 6.2)
add_figura(doc, os.path.join(GRAF, "correlacion_features.png"),
           "Figura 12. Correlación entre las variables predictoras (sustenta el análisis sobre Gaussian Naive Bayes).", 4.8)

doc.add_heading("3.4. Conclusión final", level=2)
parrafo_justificado(
    doc,
    "KNN con k=5, ponderación por distancia y métrica euclidiana fue el modelo ganador, logrando "
    "el mejor F1-Score con el menor costo computacional de los tres modelos de alto rendimiento. "
    "Los modelos complejos (SVC y Gradient Boosting) no justificaron su sobrecosto en este "
    "problema, y el modelo probabilístico (GaussianNB) quedó rezagado por la violación de sus "
    "supuestos de independencia. La lección práctica: para problemas de baja dimensionalidad con "
    "clases bien separadas, un método simple y geométrico como KNN puede ser la opción más "
    "eficiente y precisa.",
)

doc.add_page_break()

# ============================ ANEXO ==========================================
doc.add_heading("Anexo: Reproducibilidad", level=1)

parrafo_justificado(
    doc,
    "Todos los archivos del experimento se encuentran en la carpeta ActividadIngles. Los "
    "resultados presentados en este informe fueron generados con el siguiente procedimiento:",
)

doc.add_heading("A.1. Código y ejecución", level=2)
add_tabla(
    doc,
    ["Archivo", "Descripción", "Comando"],
    [
        ["occupancy_classification.py", "Experimento completo en consola (datos, pipeline, GridSearchCV, resultados)", "python occupancy_classification.py"],
        ["app_occupancy.py", "Aplicación interactiva Streamlit del experimento", "streamlit run app_occupancy.py"],
        ["generar_graficos.py", "Genera todas las figuras de este informe en ./graficos", "python generar_graficos.py"],
        ["generar_informe.py", "Genera este documento Word final", "python generar_informe.py"],
    ],
    anchos=[2.1, 3.4, 1.9],
)
cap = doc.add_paragraph("Tabla 5. Archivos del proyecto y comandos para reproducir cada parte.")
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.runs[0].italic = True
cap.runs[0].font.size = Pt(9)

doc.add_heading("A.2. Dependencias", level=2)
add_codigo(doc, """
    numpy, pandas, scikit-learn, matplotlib, streamlit, python-docx
""")

doc.add_heading("A.3. Resumen del flujo de experimentación", level=2)
add_codigo(doc, """
    1. Cargar y concatenar DataTraining.csv + DataTest.csv  -> 17,895 filas
    2. Limpiar: eliminar 'Unnamed: 0' y 'date'
    3. Pipeline unificado: StandardScaler + clasificador
    4. GridSearchCV (scoring = F1-macro, cv = StratifiedKFold(5))
    5. Ordenar resultados por F1-Score y tiempo computacional
""")

doc.save(OUT_PATH)
print("Informe generado:", OUT_PATH)