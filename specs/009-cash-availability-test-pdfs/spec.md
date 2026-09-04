# PDFs de prueba con disponibilidad de efectivo

- **ID:** SPEC-009
- **Estado:** VERIFIED
- **Creado:** 2026-08-27
- **Responsable:** Producto e ingeniería

## Problema

Los estados financieros sintéticos solo muestran el saldo contable de efectivo. No contienen los datos de corto plazo necesarios para estimar un excedente potencialmente invertible ni para demostrar que el resultado es indeterminado cuando faltan datos críticos.

## Usuarios y resultados

- **Usuario principal:** analista financiero que prueba la aplicación.
- **Resultado deseado:** cargar ejemplos que permitan consultar efectivo restringido, presupuesto de caja a 90 días, reserva mínima y excedente estimado.
- **Señal de éxito:** los tres PDF conservan su escenario original y cubren un resultado de cero, uno positivo y uno no calculable.

## Alcance

### Incluido

- Reemplazar los tres PDF sintéticos manteniendo sus nombres.
- Añadir efectivo restringido, efectivo no restringido, reserva mínima y compromisos.
- Añadir cobros, pagos y saldo proyectado para tres meses.
- Mostrar la fórmula, el resultado esperado y sus supuestos.
- Mantener un caso incompleto con valores explícitos `No informado`/`No calculable`.
- Actualizar el generador, la guía y pruebas automatizadas de los documentos.

### Excluido

- Calcular automáticamente la disponibilidad en el backend.
- Recomendar inversiones o ejecutar operaciones financieras.
- Usar datos financieros reales.

## Requisitos

### Funcionales

- **FR-001:** Cada PDF debe incluir una sección de disponibilidad de efectivo con horizonte de 90 días.
- **FR-002:** El caso de riesgo alto debe mostrar `S/ 0` de excedente potencialmente invertible.
- **FR-003:** El caso saludable debe mostrar `S/ 210,000` de excedente potencialmente invertible.
- **FR-004:** El caso incompleto debe mostrar `No calculable` y los datos críticos ausentes como `No informado`.
- **FR-005:** El generador debe seguir siendo la fuente reproducible de los tres PDF.

### No funcionales

- **NFR-001:** Los PDF deben ser legibles, sin texto cortado ni tablas superpuestas.
- **NFR-002:** Los nombres de archivo existentes deben conservarse para compatibilidad con la guía y la demo.

### Seguridad y privacidad

- **SEC-001:** Todos los nombres, cifras y notas deben seguir siendo sintéticos y no identificar clientes reales.

## Restricciones e invariantes

- El resultado es una estimación académica basada en supuestos, no asesoría financiera.
- La fórmula usa el menor saldo proyectado, incluyendo el saldo inicial, menos la reserva mínima.
- Los flujos de caja no deben presentarse como extraídos de una empresa real.

## Riesgos y fallos

- **Falsa precisión:** mitigada con horizonte, fórmula y aviso de supuestos visibles.
- **Regresión visual:** mitigada renderizando y revisando todas las páginas.
- **Caso incompleto convertido accidentalmente en completo:** mitigado con aceptación automatizada.

## Preguntas abiertas

Ninguna pregunta bloqueante.

## Referencias

- PDF inicial de la rúbrica: agente de análisis de riesgo financiero.
- SPEC-001: herramientas financieras, proyecciones y reportes.
