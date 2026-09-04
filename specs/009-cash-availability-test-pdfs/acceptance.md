# Aceptación — PDFs con disponibilidad de efectivo

## AC-001 — Estructura común

**Cubre:** FR-001, FR-005, NFR-002

```gherkin
Dado cualquiera de los tres estados financieros sintéticos
Cuando se regenera el documento
Entonces conserva su nombre e incluye parámetros, presupuesto de 90 días, fórmula y resultado
```

**Evidencia:** `tests/test_documentos_prueba.py`; los tres PDF conservan sus nombres y tienen dos páginas.

## AC-002 — Riesgo alto sin excedente

**Cubre:** FR-002

```gherkin
Dado el escenario Andes Comercial
Cuando se examina su disponibilidad
Entonces el excedente potencialmente invertible es S/ 0 y se muestra el déficit respecto de la reserva
```

**Evidencia:** prueba automatizada y revisión visual de `01_estado_financiero_riesgo_alto.pdf` (`S/ 0`, brecha `S/ 180,000`).

## AC-003 — Escenario saludable calculable

**Cubre:** FR-003

```gherkin
Dado el escenario Pacífico Servicios
Cuando se aplica la fórmula documentada
Entonces el excedente potencialmente invertible es S/ 210,000
```

**Evidencia:** prueba automatizada y revisión visual de `02_estado_financiero_saludable.pdf` (`S/ 210,000`).

## AC-004 — Datos insuficientes

**Cubre:** FR-004

```gherkin
Dado el escenario Costa Norte
Cuando faltan efectivo restringido, pagos y reserva mínima
Entonces el documento indica No informado y el resultado es No calculable
```

**Evidencia:** prueba automatizada y revisión visual de `03_estado_financiero_incompleto.pdf` (`No informado`, `No calculable`).

## AC-005 — Calidad visual y privacidad

**Cubre:** NFR-001, SEC-001

```gherkin
Dadas las seis páginas generadas
Cuando se renderizan e inspeccionan
Entonces no hay recortes ni solapamientos y todos los datos permanecen rotulados como sintéticos
```

**Evidencia:** seis páginas renderizadas con Poppler e inspeccionadas sin recortes ni superposiciones; textos rotulados como sintéticos.

## Registro de verificación

| Criterio | Evidencia | Resultado |
|---|---|---|
| AC-001 | `pytest tests/test_documentos_prueba.py -q`: 3 passed | PASS |
| AC-002 | PDF de riesgo: resultado `S/ 0` y brecha `S/ 180,000` | PASS |
| AC-003 | PDF saludable: resultado `S/ 210,000` | PASS |
| AC-004 | PDF incompleto: faltantes explícitos y resultado indeterminado | PASS |
| AC-005 | Render e inspección manual de seis páginas | PASS |

## Evidencia de regresión

- Suite completa: `99 passed`, 2 advertencias de dependencias.
- `git diff --check`: sin errores; solo avisos CRLF de Windows.
