# Tasks — Configuración Gemini, herramientas financieras, reportes y guardrails

## Preparation

- [x] **T-001** Confirmar alcance, invariantes y ausencia de preguntas bloqueantes. `[FR-001..FR-007]`

## Implementation

- [x] **T-010** Implementar estado/prueba/guardado seguro de Gemini. `[FR-001, SEC-002]`
- [x] **T-011** Incorporar contexto financiero estructurado y moderación al chat. `[FR-002, FR-006]`
- [x] **T-012** Implementar VAN, TIR y recuperación con validaciones. `[FR-003, NFR-001]`
- [x] **T-013** Implementar CSV/PDF y correo SMTP autorizados. `[FR-004, FR-005, SEC-001..SEC-005]`
- [x] **T-014** Actualizar Streamlit con configuración, escenarios y distribución. `[FR-007]`

## Verification

- [x] **T-020** Añadir pruebas unitarias e integración para todos los criterios. `[AC-001..AC-008]`
- [x] **T-021** Ejecutar regresión, renderizar PDF y probar UI en navegador. `[NFR-003, NFR-004]`

## Release

- [x] **T-030** Actualizar `.env.example`, README y guía de pruebas/subida.
- [x] **T-031** Confirmar preparación de despliegue y limitaciones externas.
