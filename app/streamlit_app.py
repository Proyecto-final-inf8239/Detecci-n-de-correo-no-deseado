"""
app/streamlit_app.py — Aplicación del proyecto aplicado (Modalidad A)
=====================================================================

Clasifica SMS nuevos, compara los modelos con sus líneas base y muestra cuánto
cuesta bloquear mensajes legítimos según el umbral. No toma decisiones sobre
mensajes reales: presenta la evidencia y sus límites.

Ejecutar desde la raíz:   streamlit run app/streamlit_app.py

Responsable: Roque · Paquete 6
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.config import DIR_ARTEFACTOS, DIR_REPORTES  # noqa: E402
from src.decision.explicacion import TEXTO_ETIQUETA  # noqa: E402
from src.monitoreo.monitor import reporte_monitoreo  # noqa: E402
from src.servicio import ModelosNoEntrenados, ServicioClasificador  # noqa: E402

st.set_page_config(page_title="Detección de spam SMS", page_icon=":material/sms:", layout="wide")

ESTILO_ETIQUETA = {
    "LEGITIMO": ("green", ":material/check_circle:"),
    "INCIERTO": ("orange", ":material/help:"),
    "SPAM": ("red", ":material/report:"),
}

# Mensajes inventados: no están en el corpus y no contienen datos personales.
EJEMPLOS = {
    "Legítimo": "Hey, are we still meeting at the library at 5? I'll bring the notes for the exam.",
    "Promoción": "WINNER!! You have been selected to receive a £500 prize. Call 09061234567 now to claim. T&Cs apply",
    "Dudoso": "Your free ringtone is waiting. Reply YES to get it, cost 50p per week, stop anytime.",
    "Español": "Hola, mañana tenemos la reunión del proyecto a las 10, por favor confirma.",
}


@st.cache_resource(show_spinner="Cargando modelos...")
def cargar_servicio() -> ServicioClasificador:
    return ServicioClasificador()


@st.cache_data(ttl=300)
def cargar_reportes() -> dict:
    def leer_json(ruta: Path):
        return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else None

    def leer_csv(ruta: Path):
        return pd.read_csv(ruta) if ruta.exists() else None

    ev, dec = DIR_REPORTES / "evaluacion", DIR_REPORTES / "decision"
    return {
        "validacion": leer_csv(ev / "comparacion_validacion.csv"),
        "prueba": leer_csv(ev / "comparacion_prueba.csv"),
        "mcnemar": leer_json(ev / "mcnemar_prueba.json"),
        "subgrupos": leer_csv(ev / "subgrupos_prueba.csv"),
        "errores": leer_csv(ev / "errores_prueba.csv"),
        "green": leer_json(ev / "green_ai.json"),
        "barrido": leer_csv(dec / "barrido_umbral_prueba.csv"),
        "por_razon": leer_csv(dec / "umbral_por_razon.csv"),
        "umbral": leer_json(dec / "resumen_umbral.json"),
    }


def alcance(representa: str, no_permite: str) -> None:
    with st.expander("Qué representa y qué no permite concluir", icon=":material/info:"):
        st.markdown(f"**Representa:** {representa}")
        st.markdown(f"**No permite concluir:** {no_permite}")


def figura(col, nombre: str, pie: str) -> None:
    ruta = DIR_REPORTES / "figuras" / nombre
    if ruta.exists():
        col.image(str(ruta), caption=pie)


def mostrar_resultado(r: dict) -> None:
    c = r["clasificacion"]
    color, icono = ESTILO_ETIQUETA[c["etiqueta"]]
    with st.container(border=True):
        st.markdown(f"### :{color}[{icono} {TEXTO_ETIQUETA[c['etiqueta']].capitalize()}]")
        st.write(r["resumen"])
        with st.container(horizontal=True):
            st.metric("Probabilidad de spam", f"{c['p_spam']:.1%}" if r["probabilidades"] else "—")
            st.metric("Nivel de riesgo", f"{c['riesgo']:.0f}/100")
            st.metric("Desacuerdo entre modelos", f"{c['desacuerdo_modelos']:.2f}")
            st.metric("Abstención", "Sí" if c["abstencion"] else "No")

    izquierda, derecha = st.columns(2)
    with izquierda:
        st.subheader("Por qué")
        for motivo in c["motivos"]:
            st.markdown(f"- {motivo}")
        if c["reglas"]:
            st.dataframe(pd.DataFrame(c["reglas"])[["codigo", "descripcion", "efecto"]],
                         hide_index=True, width="stretch")
        if r["probabilidades"]:
            st.subheader("Probabilidad por modelo")
            st.bar_chart(pd.Series(r["probabilidades"], name="p(spam)"), horizontal=True,
                         alt="Probabilidad de spam según cada modelo")
    with derecha:
        exp = r["explicacion"]
        if exp.get("disponible"):
            terminos = [{"Término": t, "Aporte": a} for t, a in exp["hacia_spam"] + exp["hacia_ham"]]
            if terminos:
                st.subheader("Términos más influyentes")
                st.caption("Positivo empuja hacia spam; negativo, hacia mensaje legítimo.")
                st.bar_chart(pd.DataFrame(terminos), x="Término", y="Aporte", horizontal=True,
                             sort="-Aporte", alt="Aporte de cada término a la clasificación")
        st.subheader("Costo esperado de cada etiqueta")
        st.dataframe(pd.DataFrame([{"Etiqueta": e, "Costo esperado": v}
                                   for e, v in c["costos_esperados"].items()]),
                     hide_index=True, width="stretch")


def pestana_clasificar(s: ServicioClasificador) -> None:
    alcance("la probabilidad de que un SMS en inglés sea spam según el modelo seleccionado, la etiqueta que "
            "resulta de los umbrales elegidos en validación y los términos que más pesaron.",
            "que el mensaje sea fraude o phishing, ni que el remitente sea malicioso. Una probabilidad alta no "
            "es una certeza; los mensajes en español u otros canales quedan fuera de la cobertura y el "
            "clasificador se abstiene.")
    ejemplo = st.segmented_control("Cargar ejemplo", list(EJEMPLOS), key="ejemplo")
    with st.form("formulario"):
        texto = st.text_area("Texto del SMS (puede escribir uno nuevo)", value=EJEMPLOS.get(ejemplo, ""), height=120)
        enviado = st.form_submit_button("Clasificar", icon=":material/search:", type="primary")
    if enviado:
        mostrar_resultado(s.analizar(texto))


def pestana_comparacion(r: dict) -> None:
    alcance("el desempeño de las dos líneas base y los cuatro modelos con las mismas particiones. El modelo se "
            "eligió solo con validación; prueba se usó una vez al final. Las líneas base compiten en la "
            "selección y podían ganar.",
            "que un modelo sea mejor que otro cuando sus intervalos se solapan y McNemar no es significativo, ni "
            "que el desempeño se mantenga en SMS actuales o en otros países.")
    columnas = ["modelo", "precision", "recall", "f1", "pr_auc", "brier", "fp", "fn"]
    st.subheader("Prueba (771 SMS)")
    st.dataframe(r["prueba"][columnas].round(4), hide_index=True, width="stretch")
    st.subheader("Validación (usada para elegir)")
    st.dataframe(r["validacion"][columnas].round(4), hide_index=True, width="stretch")
    if r["mcnemar"]:
        st.subheader("McNemar: modelo seleccionado frente a cada uno")
        st.dataframe(pd.DataFrame(r["mcnemar"]).T, width="stretch")
    if r["green"]:
        st.subheader("Green AI")
        st.dataframe(pd.DataFrame(r["green"]).T.drop(columns="supuestos"), width="stretch")
    izquierda, derecha = st.columns(2)
    figura(izquierda, "curvas_pr.png", "Curvas precisión-recall (validación)")
    figura(derecha, "calibracion.png", "Curva de calibración (validación)")


def pestana_costo(r: dict, seleccionado: str) -> None:
    alcance("cuántos mensajes legítimos se marcarían como spam y cuánto spam se escaparía con cada umbral, en "
            "el conjunto de prueba, y qué umbral conviene según cuánto más grave sea bloquear un legítimo.",
            "el costo real para una empresa o un usuario: las razones de costo son supuestos. Con 678 legítimos "
            "en prueba, cero bloqueados no garantiza cero en producción.")
    barrido = r["barrido"]
    modelos = list(barrido["modelo"].unique())
    modelo = st.selectbox("Modelo", modelos, index=modelos.index(seleccionado) if seleccionado in modelos else 0)
    datos = barrido[barrido["modelo"] == modelo]
    umbral = st.select_slider("Umbral para marcar spam", options=list(datos["umbral"]), value=0.5)
    fila = datos[datos["umbral"] == umbral].iloc[0]
    with st.container(horizontal=True):
        st.metric("Legítimos marcados como spam", int(fila["legitimos_marcados_spam"]))
        st.metric("Spam no detectado", int(fila["spam_no_detectado"]))
        st.metric("Precisión de spam", f"{fila['precision']:.1%}")
        st.metric("Recall de spam", f"{fila['recall']:.1%}")
    st.line_chart(datos.set_index("umbral")[["legitimos_marcados_spam", "spam_no_detectado"]],
                  x_label="Umbral", y_label="Mensajes en prueba")
    st.subheader("Umbral recomendado según la razón de costos")
    st.caption("Razón = cuántas veces más grave es bloquear un legítimo que dejar pasar un spam. "
               "El umbral se elige en validación y se mide en prueba.")
    st.dataframe(r["por_razon"][r["por_razon"]["modelo"] == modelo].drop(columns=["modelo", "n_prueba"]),
                 hide_index=True, width="stretch")


def pestana_errores(r: dict) -> None:
    alcance("dónde se equivoca el modelo seleccionado: subgrupos de mensajes, errores sin texto (por privacidad) "
            "y los mensajes en los que se abstiene.",
            "las causas de cada error; los subgrupos se definen con rasgos simples del texto.")
    u = r["umbral"]
    if u:
        with st.container(horizontal=True):
            st.metric("Legítimos marcados como spam", u["legitimos_marcados_spam"])
            st.metric("Spam no detectado", u["spam_no_detectado"])
            st.metric("Abstenciones (incierto)", f"{u['tasa_abstencion']:.1%}")
            st.metric("Costo por 1 000 SMS", u["costo_por_1000"], delta=f"umbral 0.5: {u['costo_por_1000_umbral_fijo']}",
                      delta_color="off")
    st.subheader("Desempeño por subgrupo")
    st.dataframe(r["subgrupos"].round(3), hide_index=True, width="stretch")
    st.subheader("Errores del modelo seleccionado (sin texto)")
    st.dataframe(r["errores"], hide_index=True, width="stretch")
    izquierda, _ = st.columns(2)
    figura(izquierda, "matriz_confusion.png", "Matriz de confusión (prueba)")


def pestana_monitoreo(s: ServicioClasificador) -> None:
    alcance("si los mensajes clasificados en esta aplicación se parecen a los de validación (PSI) y cuántas "
            "abstenciones hay.", "que el modelo siga acertando: para eso hacen falta etiquetas verificadas.")
    ruta = DIR_ARTEFACTOS / "referencia_monitoreo.json"
    if not ruta.exists() or s.log is None:
        st.warning("No hay referencia de monitoreo o registro de predicciones.")
        return
    rep = reporte_monitoreo(s.log.leer(), json.loads(ruta.read_text(encoding="utf-8")))
    if rep["n"] == 0:
        st.info("Aún no hay predicciones registradas.")
        return
    with st.container(horizontal=True):
        st.metric("Predicciones registradas", rep["n"])
        st.metric("PSI de puntajes", f"{rep['psi_puntaje']:.3f}")
        st.metric("PSI de longitudes", f"{rep['psi_longitud']:.3f}")
        st.metric("Abstención", f"{rep['tasa_abstencion']:.1%}",
                  delta=f"{rep['tasa_abstencion'] - rep['tasa_abstencion_referencia']:+.1%} vs referencia",
                  delta_color="off")
    for alerta in rep["alertas"]:
        (st.error if alerta.startswith("ALERTA") else st.warning)(alerta)
    st.bar_chart(pd.Series(rep["etiquetas"], name="mensajes"), alt="Mensajes por etiqueta")
    st.caption("El registro no guarda el texto de los mensajes: solo hash, longitud, probabilidad, etiqueta y reglas.")


st.title(":material/sms: Detección de spam SMS")
st.caption("INF-8239 Ciencia de Datos II · Proyecto aplicado (Modalidad A) · SMS Spam Collection (UCI)")
st.warning("Cobertura: solo SMS en inglés (corpus UCI 2003-2011). Con mensajes en español u otros canales el "
           "clasificador se abstiene.", icon=":material/translate:")

try:
    servicio = cargar_servicio()
except ModelosNoEntrenados as e:
    st.error(str(e))
    st.stop()

with st.sidebar:
    st.header("Configuración")
    st.write(f"Modelo seleccionado: **{servicio.seleccionado}**")
    st.write(f"Costos: legítimo marcado como spam = {servicio.costos.fp}, spam no detectado = {servicio.costos.fn}, "
             f"abstención = {servicio.costos.abstencion}")
    st.write(f"Umbrales: legítimo bajo p = {servicio.umbrales[0]:.2f}, spam desde p = {servicio.umbrales[1]:.2f}")

reportes = cargar_reportes()
pestanas = st.tabs(["Clasificar SMS", "Comparación de modelos", "Costo de bloquear legítimos",
                    "Errores y abstenciones", "Monitoreo"])
with pestanas[0]:
    pestana_clasificar(servicio)
if reportes["prueba"] is None or reportes["barrido"] is None:
    for p in pestanas[1:4]:
        p.warning("No hay reportes. Ejecute python -m src.pipeline")
else:
    with pestanas[1]:
        pestana_comparacion(reportes)
    with pestanas[2]:
        pestana_costo(reportes, servicio.seleccionado)
    with pestanas[3]:
        pestana_errores(reportes)
with pestanas[4]:
    pestana_monitoreo(servicio)
