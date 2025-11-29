import pandas as pd
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print(">>> iniciando el bot de consulta RUAF...")

INPUT_FILE = "ID.csv"
OUTPUT_FILE = "ID_PROCESADOS_RUAF.xlsx"
URL_RUAF = "https://ruaf.sispro.gov.co/TerminosCondiciones.aspx"
API_KEY_2CAPTCHA = "TU_API_KEY_AQUI"
RUTA_DRIVER = r"C:\Users\hp\Documents\prueba_seg_mundial\edge\msedgedriver.exe"

# --- FUNCIÓN CAPTCHA ---
def resolver_captcha_servicio(driver):
    # Me tocó dejarlo en manual porque no tenía API Key configurada en esta fase.
    if API_KEY_2CAPTCHA == "TU_API_KEY_AQUI":
        print("\n   [!] Lo dejé en modo manual porque el portal tiene protección.")
        return input("   >>> Escribo el captcha que veo en pantalla: ")
    return None

# --- CARGA ---
try:
    # Intente leerlo con ; porque cuando lo hice por primera vez vinieron así los campos.
    df_ids = pd.read_csv(INPUT_FILE, sep=';', dtype=str)
    # Me tocó poner fallback a , porque algunos archivos que probé venían con coma.
    if df_ids.shape[1] < 2:
        df_ids = pd.read_csv(INPUT_FILE, sep=',', dtype=str)
    print(f">>> Leí yo mismo el archivo y encontré {len(df_ids)} documentos para consultar.")
except Exception as e:
    print(f"   Se dañó la lectura que hice por: {e}")
    exit()

# --- INICIO NAVEGADOR ---
if not os.path.exists(RUTA_DRIVER):
    print(f"   No encontré el driver en {RUTA_DRIVER}, entonces no pude iniciar Edge.")
    exit()

try:
    # Esto lo hice así manual porque el instalador automático me fallaba en RDS offline.
    service = Service(executable_path=RUTA_DRIVER)
    driver = webdriver.Edge(service=service)
    wait = WebDriverWait(driver, 10)
    print("   Edge lo levanté correctamente ✅")
except Exception as e:
    print(f"   No logré iniciar Edge por: {e}")
    exit()

# --- EJECUCIÓN ---
resultados = []
try:
    driver.get(URL_RUAF)
    # Me tocó validar aceptar términos porque era obligatorio para seguir.
    try:
        btn_terminos = wait.until(EC.element_to_be_clickable((By.ID, "MainContent_btnAcepto")))
        btn_terminos.click()
        print("   Aceptar términos.")
    except:
        print(" ya estan aceptados, seguir.")

    for idx, row in df_ids.iterrows():
        col_doc = df_ids.columns[0]
        col_fecha = df_ids.columns[-1]

        doc = row[col_doc].strip()
        fecha = row[col_fecha].strip()
        print(f"\n---  consulto: {doc} con fecha {fecha} ---")

        estado = {"DOCUMENTO": doc, "FECHA": fecha, "ESTADO": "Fallido"}
        try:
            # Esto lo hice para esperar que cargara el input porque sin eso se escribía en el DOM antes.
            wait.until(EC.presence_of_element_located((By.ID, "MainContent_txtNumeroIdentificacion")))

            # Seleccioné CC porque fue el tipo de documento que definí para la ejecución del bot.
            caja_tipo = Select(driver.find_element(By.ID, "MainContent_ddlTipoDocumento"))
            caja_tipo.select_by_value("CC")

            driver.find_element(By.ID, "MainContent_txtNumeroIdentificacion").clear()
            driver.find_element(By.ID, "MainContent_txtNumeroIdentificacion").send_keys(doc)

            driver.find_element(By.ID, "MainContent_txtFechaExpedicion").clear()
            driver.find_element(By.ID, "MainContent_txtFechaExpedicion").send_keys(fecha)

            driver.find_element(By.TAG_NAME, "body").click()

            captcha = resolver_captcha_servicio(driver)
            if captcha:
                driver.find_element(By.ID, "MainContent_txtCaptcha").clear()
                driver.find_element(By.ID, "MainContent_txtCaptcha").send_keys(captcha)
                driver.find_element(By.ID, "MainContent_btnConsultar").click()
                # Le puse pausa porque cuando lo hice sin esperar, no alcanzaba a leer el resultado.
                time.sleep(3)
                estado["ESTADO"] = "Exitoso"
        except Exception as e:
            print(f"   Falló la consulta que hice por: {e}")
        resultados.append(estado)
finally:
    # No cerré el driver al final para analizar yo mismo la ejecución en pruebas locales.
    print("\n>>> Bot terminó la ejecución que lancé.")

df_out = pd.DataFrame(resultados)
df_out.to_excel(OUTPUT_FILE, index=False)
print(">>> Guardé el Excel con el estado de cada consulta.")
