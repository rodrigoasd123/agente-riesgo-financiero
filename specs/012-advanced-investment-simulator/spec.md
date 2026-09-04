# Simulador avanzado de inversión

- **ID:** SPEC-012
- **Estado:** VERIFIED
- **Fecha:** 2026-09-04
- **Owner:** Producto e ingeniería

## Problema

El simulador actual recibe una “tasa anual” y una frecuencia de capitalización, pero no aclara si la tasa es TEA o TNA. Tampoco permite ingresar una tasa efectiva mensual/bimestral, considerar inflación o costos mensuales, ni comparar el resultado nominal con su poder adquisitivo. Esto puede producir interpretaciones financieras incorrectas aun cuando la aritmética sea válida.

## Usuarios y resultado

- Analistas y administradores autenticados que ya analizaron un estado financiero.
- El usuario declara el tipo y periodicidad de la tasa, comprende sus equivalencias y obtiene un resultado nominal, neto y real trazable.
- La simulación sigue siendo educativa: no recomienda instrumentos, no usa cotizaciones y no ejecuta operaciones.

## Alcance

### Incluido

- Tasas TEA, TNA y efectiva por período.
- Periodicidades mensual, bimestral, trimestral, cuatrimestral, semestral y anual.
- Capitalización diaria, mensual, bimestral, trimestral, cuatrimestral, semestral y anual para TNA.
- Aportes al inicio o al final del mes.
- Comisión de entrada/salida, costo mensual, impuesto sobre ganancias e inflación anual.
- Equivalencias TEA y TEM, saldo real, ganancia real y ROI real.
- Compatibilidad del contrato anterior que enviaba `tasa_anual_percent`.

### Excluido

- Precios de mercado, volatilidad, Monte Carlo, riesgo crediticio del emisor y recomendaciones de compra.
- Reglas tributarias por país o instrumento.
- Persistencia de escenarios y ejecución de órdenes.

## Requisitos

### Funcionales

- **FR-001:** El sistema debe aceptar `tea`, `tna` o `efectiva_periodo` e indicar qué conversión aplicó.
- **FR-002:** Para una TNA debe usar la frecuencia de capitalización; para una tasa efectiva debe usar la periodicidad declarada.
- **FR-003:** Debe calcular TEA y TEM equivalentes con precisión Decimal.
- **FR-004:** Debe admitir aportes al inicio o al final del período y reflejar ese momento en la serie.
- **FR-005:** Debe descontar comisiones, costo mensual e impuesto solo sobre ganancia gravable positiva.
- **FR-006:** Debe mostrar saldo final nominal neto, saldo real, ganancia/ROI nominales y reales, costos e impuestos.
- **FR-007:** Debe conservar la forma anterior del API usando TNA cuando solo se envía `tasa_anual_percent`.
- **FR-008:** La interfaz debe explicar dinámicamente qué campos aplican al tipo de tasa elegido.

### No funcionales

- **NFR-001:** Dinero y tasas deben calcularse con `Decimal`; no se permiten `float` en la lógica financiera.
- **NFR-002:** No se añadirán dependencias y el proyecto debe seguir funcionando en el laboratorio.
- **NFR-003:** Los gráficos no deben generar `params` de Vega-Lite.
- **NFR-004:** Los límites de entrada deben impedir tasas, plazos, importes o porcentajes no razonables.

### Seguridad y privacidad

- **SEC-001:** El endpoint exige JWT y obtiene el análisis por propietario autenticado.
- **SEC-002:** Los supuestos del usuario no se envían a Gemini ni a servicios externos.
- **SEC-003:** La respuesta y el gráfico solo contienen campos financieros definidos en el contrato.

## Restricciones e invariantes

- Aportes mensuales posteriores al mes cero se consideran flujos del usuario, no rentabilidad.
- El saldo real se expresa en poder adquisitivo del inicio usando la inflación indicada.
- La simulación puede usar un capital manual mayor al excedente, pero debe advertirlo en la interfaz; no es una orden ni una recomendación.
- SPEC-012 amplía SPEC-010 sin cambiar sus reglas de tesorería ni autorización.

## Riesgos y mitigaciones

- Confundir TNA con TEA: etiquetas, ayuda contextual y equivalencias visibles.
- Interpretar una tasa fija como garantizada: advertencia permanente.
- Inflación de -100 % o base matemática no positiva: validación 422.
- Diferencias por redondeo: cálculo interno de alta precisión y redondeo monetario solo en salidas.

## Preguntas abiertas

Ninguna bloqueante. La periodicidad bimestral significa un período de dos meses; los aportes conservan frecuencia mensual.

## Referencias

- `specs/010-investment-treasury-integration/`
