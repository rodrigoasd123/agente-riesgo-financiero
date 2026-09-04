# Pronóstico de ventas a seis meses

- **ID:** SPEC-013
- **Estado:** VERIFIED
- **Fecha:** 2026-09-04

## Problema y resultado

El dashboard muestra la evolución histórica mensual, pero no ofrece una referencia cuantitativa para los siguientes meses. Analistas y administradores necesitan una proyección explicable que distinga datos observados de estimaciones y exponga su error histórico.

## Alcance

- Entrenar sobre `ventas_mensuales` un modelo de regresión lineal temporal y compararlo mediante backtesting walk-forward con una línea base de persistencia.
- Seleccionar el menor MAE, proyectar 1 a 12 meses (6 por defecto) y producir un rango orientativo del 80 % basado en residuos.
- Mostrar serie observada/pronosticada, total proyectado, variación contra los últimos meses, MAE, modelo y advertencia.
- No usar Gemini, datos externos, cotizaciones ni nuevas dependencias.

## Requisitos

- **FR-001:** Debe requerir al menos seis observaciones mensuales válidas, ordenadas y no negativas.
- **FR-002:** Debe evaluar regresión lineal temporal y persistencia con backtesting walk-forward y seleccionar el menor MAE.
- **FR-003:** Debe devolver 1 a 12 meses futuros con estimación, límite inferior no negativo y límite superior.
- **FR-004:** Debe devolver MAE, modelo elegido, total futuro y variación frente al bloque histórico comparable.
- **FR-005:** El dashboard debe diferenciar observado, pronóstico y rango de incertidumbre, y explicar que no es garantía.
- **FR-006:** Sin historia suficiente debe mostrar un estado no calculable, no inventar meses.
- **NFR-001:** El cálculo monetario debe usar `Decimal`, ser determinista y no añadir dependencias.
- **NFR-002:** El gráfico debe ser compatible con el laboratorio y no contener `params` Vega-Lite.
- **SEC-001:** El endpoint debe exigir JWT y filtrar el análisis por propietario.
- **SEC-002:** Solo se procesan período e importe; el texto del PDF no sale del backend ni llega al gráfico.
- **SEC-003:** Horizonte y estructura se validan con un contrato explícito.

## Límites y riesgos

- Doce meses constituyen una muestra corta y no permiten inferir estacionalidad anual de forma robusta.
- El rango es orientativo, no un intervalo probabilístico garantizado.
- Eventos comerciales, inflación, capacidad, precios o shocks no incluidos no pueden ser anticipados.
- La salida es apoyo analítico y no una meta, presupuesto aprobado ni recomendación de inversión.

## Preguntas abiertas

Ninguna bloqueante. El horizonte inicial será de seis meses y quedará limitado a doce.
