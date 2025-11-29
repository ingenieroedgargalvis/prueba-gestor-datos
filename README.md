# prueba-gestor-datos
Soy Edgar Galvis, ingeniero de sistemas, y este repositorio contiene la solución que desarrollé para la prueba técnica del cargo de Gestor Especializado de Datos en la coordinación de Datos y Control.


# Prueba Técnica: Gestor Especializado de Datos

**Candidato:** Edgar Galvis (Ingeniero de Sistemas)  
**Fecha:** 29 de noviembre de 2025

## 1. Lo que hice en esta prueba
En este repositorio dejé la solución a la prueba que realicé para el rol de gestor de datos. Me tocó trabajar sobre dos frentes grandes:

1. **Análisis de datos de facturación médica:** aquí hice limpieza, transformación, enriquecimiento y la gráfica de barras que me solicitaron.
2. **Automatización tipo RPA para consultar el portal del RUAF:** acá realicé el bot con Selenium sobre Edge, manejando términos, formulario y captcha manual porque la API no la configuré para esta ejecución.

## 2. Lo que me tocó resolver
- El dataset venía con separadores no estándar (símbolo `°`), por lo que tuve que ajustar `encoding` y usar el motor correcto para leerlo sin que se rompiera.
- Cuando hice el cruce con el archivo parquet noté que la llave `POLIZA` venía como flotante con `.0`, entonces me tocó normalizar ambos lados antes del `merge` para garantizar que el cruce que realicé funcionara.
- Con la clasificación de personas apliqué la lógica que me dieron y la adapté a una función que hice desde cero.
- Para la gráfica agrupé por año y tipo de cuenta porque fue la forma que me dio mejores resultados en las pruebas que hice localmente.

## 3. Entregables que yo mismo generé
- `PRUEBA_ANALISIS.xlsx` → este lo exporté luego de procesar y cruzar la información.
- `GRAFICA_BARRAS_ANUAL.png` → esta la creé como parte de la visualización final que realicé.
- `ID_PROCESADOS_RUAF.xlsx` → el reporte del bot que hice y dejé al final del scraping RUAF.

## 4. Para ejecutarlo como yo lo hice
1. Dejé los archivos fuente en la raíz: `BASE.csv`, `PROD.parquet`, `ID.csv` y el driver `msedgedriver.exe`.
2. Para correr el análisis use uso:
   ```bash
   python analisis_datos2.py
