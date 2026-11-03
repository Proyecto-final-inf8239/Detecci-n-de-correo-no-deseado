# Model Card · Clasificador de spam SMS v1.0.0 (`naive_bayes`)

Formato basado en Mitchell et al. (2019), *Model Cards for Model Reporting*. Datos descritos en
`docs/gobernanza/ficha_dataset.md`.

## Detalles del modelo

- **Tipo:** Multinomial Naive Bayes (α = 0.1) sobre TF-IDF de palabras 1-2 gramas con normalización de URL,
  correos, teléfonos, montos y números.
- **Versión:** 1.0.0, con semilla 42 y scikit-learn 1.7.
- **Desarrollado por:** equipo del trabajo final de INF-8239 Ciencia de Datos II, UASD, 2026.
- **Acompañantes:** regresión logística, SVM de caracteres y una red neuronal MLP (para detectar desacuerdo)
  y una capa de reglas, umbrales y abstención.

## Uso previsto

Proyecto aplicado (Modalidad A): clasificar SMS en inglés como spam, legítimo o incierto, con explicación, y
estudiar cuánto cuesta bloquear mensajes legítimos según el umbral. Es un producto académico de análisis; no
está pensado para filtrar mensajes reales sin una evaluación nueva.

## Usos no permitidos

Los de `docs/gobernanza/riesgos_y_usos.md` §3: eliminar mensajes automáticamente, perfilar o sancionar
personas, aplicarlo a SMS en español o al contexto dominicano sin datos nuevos, a correo electrónico, WhatsApp
o redes sociales, vigilar comunicaciones o presentarlo como detector de fraude.

## Datos

SMS Spam Collection v.1 (UCI, CC BY 4.0, SHA-256 verificado): 5 574 SMS, 13.4 % spam; tras deduplicar, 5 137.
Partición estratificada 70/15/15 sin textos compartidos.

## Métricas en prueba (771 SMS, umbral 0.5)

| Métrica | Valor |
|---|---|
| Precisión de spam | 1.000 (0 legítimos bloqueados) |
| Recall de spam | 0.914 (8 spam no detectados de 93) |
| F1 | 0.955 (IC 95 % 0.919 – 0.984) |
| PR-AUC / ROC-AUC | 0.968 / 0.984 |
| Brier | 0.011 |

Con los umbrales elegidos en validación (0.73) y las reglas de abstención: 0 legítimos marcados como spam, 7
spam no detectados, 0.9 % de abstención y precisión de spam de 100 %. Entre los umbrales 0.45 y 0.55 el modelo
no marca ningún legítimo de prueba como spam.

## Subgrupos

| Subgrupo | Recall | Observación |
|---|---|---|
| Spam con teléfono | 98.5 % | Señal dominante |
| Spam sin teléfono | 73.1 % | **Debilidad principal** |
| Mayúsculas > 50 % | 75 % | Muestra muy pequeña (4 spam) |
| Ham con marcador `<#>` | FPR 0 % | El artefacto se neutralizó sin efectos adversos |

## Consideraciones éticas

- **Costo asimétrico:** bloquear un SMS legítimo se considera 10 veces peor que dejar pasar spam; por eso se
  prioriza la precisión de spam y, ante la duda, el clasificador se abstiene.
- **Privacidad:** los SMS contienen nombres y teléfonos. No se muestran mensajes reales en informes ni app,
  los reportes de errores solo guardan `id_mensaje`, y el registro de monitoreo no guarda texto.
- **Cobertura lingüística:** inglés de Reino Unido y Singapur, 2003-2011. Con mensajes en español el clasificador
  se abstiene (regla R02).

## Limitaciones

- Corpus antiguo y pequeño (747 spam): el spam actual (enlaces acortados, smishing bancario) puede degradar el
  desempeño.
- La detección de español es heurística (palabras vacías).
- Los supuestos Green AI son estimaciones.

## Monitoreo

PSI de puntajes y longitudes (alerta ≥ 0.25), tasa de abstención (alerta > 25 %) y precisión de spam medida con
etiquetas verificadas (alerta < 95 %: se deja de marcar spam automáticamente y se revisa el umbral).
