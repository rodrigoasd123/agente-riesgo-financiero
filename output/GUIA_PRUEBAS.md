# Guia de prueba de la aplicacion

## Acceso

- Interfaz: http://localhost:8501
- Usuario: `admin`
- Contrasenia: `admin123`

## Documentos para cargar

1. `pdf/01_estado_financiero_riesgo_alto.pdf`
   - Debe producir varias alertas: liquidez, prueba acida, endeudamiento, cobertura de intereses y caida de ventas.
   - Disponibilidad a 90 dias: excedente potencialmente invertible `S/ 0` y brecha de caja de `S/ 180,000` respecto de la reserva.
   - Preguntas sugeridas: "¿Cuales fueron las ventas de 2025?", "¿Por que cayeron los ingresos?" y "¿Hay efectivo disponible para invertir?".
   - Evolucion mensual: caida desde S/ 95,000 en enero hasta S/ 73,000 en diciembre, con recuperaciones puntuales.
2. `pdf/02_estado_financiero_saludable.pdf`
   - No deberia producir alertas automaticas con los umbrales actuales.
   - Disponibilidad a 90 dias: excedente potencialmente invertible estimado de `S/ 210,000`.
   - Preguntas sugeridas: "¿Cual es la utilidad neta?" y "¿Como se calcula el excedente de S/ 210,000?".
   - Evolucion mensual: crecimiento desde S/ 110,000 en enero hasta S/ 162,000 en diciembre.
3. `pdf/03_estado_financiero_incompleto.pdf`
   - Debe dejar varios indicadores sin valor.
   - Disponibilidad a 90 dias: `No calculable` porque faltan efectivo restringido, pagos y reserva minima.
   - Preguntas sugeridas: "¿Cual es el pasivo total?" y "¿Cuanto efectivo se puede invertir?"; debe indicar que faltan datos.
   - Evolucion mensual: serie estable de S/ 30,000 a S/ 36,000; el desglose de ventas no completa los datos faltantes del balance.

## Secuencia recomendada

1. Inicia sesion.
2. Carga cada PDF por separado y pulsa **Analizar documento**.
3. Compara indicadores, alertas y resumen con el resultado esperado impreso al final del PDF.
4. Revisa la segunda pagina y contrasta parametros, flujos mensuales y excedente esperado.
5. Revisa la tercera pagina y confirma que el dashboard muestre doce puntos mensuales y sus variaciones en el tooltip.
6. En **Proyecciones y reportes**, ejecuta el simulador con un capital que no exceda el excedente estimado y contrasta saldo, ganancia y ROI.
7. Realiza las preguntas sugeridas y abre **Ver fuente citada**.
8. Cierra sesion para comprobar que el token deja de estar disponible en la interfaz.

## Prueba recomendada del simulador avanzado

Con el documento saludable, selecciona el escenario de 60 % del excedente (`S/ 126,000`) y prueba:

- Tipo de tasa: `TNA`.
- Tasa: `12 %`.
- Capitalizacion: `mensual`.
- Plazo: `12 meses`.
- Inflacion: `3 % anual`.
- Comision de entrada y salida: `0.2 %` cada una.
- Impuesto sobre ganancia: `5 %`.

Comprueba que la aplicacion muestre TEM, TEA equivalente, saldo nominal, saldo real, ROI nominal, ROI real y costos. Luego cambia a tasa efectiva `2 % bimestral`: la TEA equivalente debe ser aproximadamente `12.616242 %`.

## Prueba recomendada del pronostico

En **Dashboard**, selecciona `6 meses`:

- El PDF saludable debe elegir regresion temporal y proyectar aproximadamente `S/ 1,023,174.83` en seis meses.
- El PDF de riesgo alto debe elegir persistencia porque su backtesting presenta menor error que prolongar linealmente la caida.
- Deben mostrarse MAE, variacion contra los ultimos seis meses, confianza cualitativa baja y un rango orientativo.
- El documento sin seis meses consecutivos debe mostrar `Pronostico no disponible`, sin completar datos inexistentes.

Si la aplicacion se ejecuta sin una clave de Gemini, mostrara el modo offline. Para probar Gemini, pega la clave en `GEMINI_API_KEY` dentro de `.env`, reinicia backend y frontend y valida la conexion desde Configuracion con el rol administrador.
