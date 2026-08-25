# Tasks — Finalizacion, seguridad y Gemini del agente de riesgo financiero

## Preparation

- [x] **T-001** Inspeccionar ZIP, PDF, codigo y documentos heredados. `[FR-001..007]`
- [x] **T-002** Confirmar que la especificacion no tiene preguntas bloqueantes. `[FR-001..007, SEC-001..007]`

## Implementation

- [x] **T-010** Endurecer configuracion, `.env` y dependencias vigentes. `[FR-005, FR-007, NFR-001, SEC-004]`
- [x] **T-011** Completar bcrypt/JWT y contratos de login. `[FR-001, SEC-001, SEC-002, SEC-006]`
- [x] **T-012** Aplicar ownership en SQLite, historial y chat. `[FR-003, FR-004, SEC-003]`
- [x] **T-013** Validar uploads y sanitizar fallos API. `[FR-002, SEC-005, SEC-006]`
- [x] **T-014** Actualizar Gemini a salida estructurada, modelos vigentes y timeouts. `[FR-005, FR-006, NFR-002, SEC-007]`
- [x] **T-015** Mejorar fuentes por pagina y comportamiento offline. `[FR-003, FR-006]`
- [x] **T-016** Ajustar frontend y health operacional. `[FR-007, NFR-005]`

## Verification

- [x] **T-020** Crear pruebas unitarias y de integracion para AC-001..AC-010. `[AC-001..010]`
- [x] **T-021** Ejecutar compilacion, pytest y E2E offline. `[NFR-001, NFR-003]`
- [x] **T-022** Revisar seguridad con evidencia y registrar riesgo residual. `[SEC-001..007]`
- [x] **T-023** No aplicable: `GEMINI_API_KEY` aun esta vacia; adaptador verificado con doble local y smoke real documentado para despues de pegar la clave. `[FR-005]`

## Release

- [x] **T-030** Actualizar README y documentos heredados con la configuracion real. `[NFR-005]`
- [x] **T-031** Registrar resultados, rollback y funcionalidades recomendadas. `[NFR-004, NFR-005]`
