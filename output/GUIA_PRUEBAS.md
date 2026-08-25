# Guia de prueba de la aplicacion

## Acceso

- Interfaz: http://localhost:8501
- Usuario: `admin`
- Contrasenia: `admin123`

## Documentos para cargar

1. `pdf/01_estado_financiero_riesgo_alto.pdf`
   - Debe producir varias alertas: liquidez, prueba acida, endeudamiento, cobertura de intereses y caida de ventas.
   - Preguntas sugeridas: "¿Cuales fueron las ventas de 2025?" y "¿Por que cayeron los ingresos?".
2. `pdf/02_estado_financiero_saludable.pdf`
   - No deberia producir alertas automaticas con los umbrales actuales.
   - Pregunta sugerida: "¿Cual es la utilidad neta?".
3. `pdf/03_estado_financiero_incompleto.pdf`
   - Debe dejar varios indicadores sin valor.
   - Pregunta sugerida: "¿Cual es el pasivo total?"; debe indicar que no encontro el dato.

## Secuencia recomendada

1. Inicia sesion.
2. Carga cada PDF por separado y pulsa **Analizar documento**.
3. Compara indicadores, alertas y resumen con el resultado esperado impreso al final del PDF.
4. Realiza las preguntas sugeridas y abre **Ver fuente citada**.
5. Cierra sesion para comprobar que el token deja de estar disponible en la interfaz.

La aplicacion esta ejecutandose sin una clave de Gemini, por lo que mostrara el modo offline. Para probar Gemini, pega la clave en `GEMINI_API_KEY` dentro de `.env` y reinicia backend y frontend.
