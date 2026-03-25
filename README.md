# F1 Telemetry Dashboard

Un dashboard interactivo para visualizar datos de telemetría de Fórmula 1 en tiempo real y histórico, construido con Streamlit y FastF1.

## Características

- **Modo en Vivo**: Monitoreo automático de sesiones de F1 en curso
- **Datos Históricos**: Análisis de sesiones completadas
- **Driver Destacado**: Seguimiento detallado de Franco Colapinto (#43, Williams)
- **Torre de Tiempos**: Clasificaciones en tiempo real con indicadores de mejores tiempos
- **Mapa del Circuito**: Visualización GPS con animación de vueltas
- **Comparación de Telemetría**: Análisis detallado de velocidad, acelerador, frenos, RPM y cambios
- **Mensajes FIA**: Control de carrera y comunicaciones oficiales
- **Campeonato**: Posiciones actuales de pilotos y constructores

## Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/f1-dashboard.git
   cd f1-dashboard
   ```

2. Crea un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Ejecuta la aplicación:
   ```bash
   streamlit run app.py
   ```

## Uso

- Selecciona un Gran Premio y sesión desde la barra lateral
- Haz clic en "Load Session Data" para cargar los datos
- Explora las diferentes pestañas para ver análisis detallados
- Durante sesiones en vivo, el dashboard se actualiza automáticamente

## Selección Dinámica de Drivers

La aplicación ahora carga automáticamente todos los drivers participantes en la sesión seleccionada, eliminando la necesidad de configuración manual. El driver destacado (Franco Colapinto) se selecciona automáticamente cuando está presente en la sesión.

## Datos

- **Fuente**: FastF1 API para datos de telemetría
- **Cache**: Datos almacenados localmente en `./cache/`
- **Actualización**: Datos en vivo cada 3 segundos durante sesiones activas

## Requisitos

- Python 3.8+
- Streamlit
- FastF1
- Plotly
- Pandas
- Requests

## Contribución

Si encuentras errores o tienes sugerencias, por favor abre un issue o envía un pull request.

## Licencia

Este proyecto es de código abierto. Consulta el archivo LICENSE para más detalles.