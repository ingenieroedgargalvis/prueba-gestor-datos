import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from selenium import webdriver

print(">>> Iniciando análisis de datos...")

# --- 1. CARGA DE DATOS ---
try:
    print("   Cargando 'BASE.csv'...")
    # Aquí tuve que usar encoding='latin1' porque me encontré con el símbolo ° y con UTF-8 se dañaba la lectura.
    df = pd.read_csv('BASE.csv', sep='°', encoding='latin1', engine='python')
    
    # También me tocó limpiar nombres de columnas porque le venían espacios raros al inicio y al final.
    df.columns = df.columns.str.strip()

    print(f"   La base se cargo sin errores: {df.shape[0]} registros.")
except Exception as e:
    print(f"   ERROR FATAL cargando la base: {e}")
    # Si llega a fallar, decidí cerrar todo porque sin base no podía seguir con el resto del análisis que realicé.
    exit()

# --- 2. CLASIFICACIÓN TIPO PERSONA ---
if 'ID RECLAMANTE' in df.columns:
    # Aquí hice la función para clasificar si era persona jurídica o natural según la regla del negocio que me dieron.
    def clasificar_persona(id_val):
        # Realicé la conversión a string y eliminé decimales tipo "12345678.0" porque el merge más adelante se dañaba.
        id_str = str(id_val).strip().split('.')[0]
        # La condición la escribí así porque me tocó interpretar que 8 dígitos + iniciar con 8 o 9 = jurídica.
        if len(id_str) == 8 and id_str.startswith(('8', '9')):
            return "P_JURÍDICA"
        return "P_NATURAL"

    df['TIPO_PERSONA'] = df['ID RECLAMANTE'].apply(clasificar_persona)
    print("   campo generado -> TIPO_PERSONA")
else:
    # Me pasó que algunos datasets que probé no traían la columna, por eso dejé esta advertencia informativa.
    print("   ADVERTENCIA: No esta la columna 'ID RECLAMANTE', entonces se puede clasificar ese punto.")

# --- 3. CLASIFICAR CUENTA (DESCUENTO) ---
if 'CLASE VEHICULO' in df.columns:
    # Convertí a mayúsculas porque cuando lo hice sin normalizar, me di cuenta que no detectaba "motocicleta" vs "MOTOCICLETA".
    df['CLASE VEHICULO'] = df['CLASE VEHICULO'].astype(str).str.upper().str.strip()
    condiciones = df['CLASE VEHICULO'].isin(["MOTOCICLETA", "CICLOMOTOR", "MOTO CARRO"])
    # Este np.where lo usé porque me tocó aplicar una regla rápida para marcar si aplica o no descuento.
    df['CLASIFICAR_CUENTA'] = np.where(condiciones, "APLICA_DESCUENTO", "NO_APLICA_DESCUENTO")
    print("   Ya con eso dejé la cuenta marcada según el descuento que me tocó evaluar.")

# --- 4. GRÁFICA DE BARRAS ---
campo_tipo = 'CLASIFICAR_CUENTA'  # Lo deje así porque fue el campo que enriquecí antes.

if 'F.AVISO' in df.columns and campo_tipo in df.columns:
    try:
        # Convertí las fechas porque en la primera ejecución que hice, venian como texto y tocaba parsearlas.
        df['F.AVISO'] = pd.to_datetime(df['F.AVISO'], errors='coerce')
        # Luego extraje el año porque era necesario para la grafi que hice como parte del análisis.
        df['ANO_AVISO'] = df['F.AVISO'].dt.year
        
        # agrup por año y tipo de cta para poder contar facturas Sisinn el unstack no me generaba barras agrupadas bien.
        df_grafica = df.groupby(['ANO_AVISO', campo_tipo])['FACTURA IQ'].count().unstack()

        # la graficacion la hice usando kind='bar' para que las barras queden una al lado de la otra como me lo pidieron.
            
        colores_corp = ['#003366', '#00A4E4'] # use tonos corporativos de Seguros Mundial


        # Crear la gráfica
        ax = df_grafica.plot(kind='bar', figsize=(12, 7), color=colores_corp, edgecolor='white', width=0.8)
        

        plt.title(f'Cantidad de Facturas por Año y {campo_tipo}')
        plt.xlabel('Año de Aviso')
        plt.ylabel('Cantidad de Facturas')
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        plt.xticks(rotation=0)
        plt.tight_layout()

        plt.savefig('GRAFICA_BARRAS_ANUAL.png')
        print("   La gráfica la exporté yo mismo como GRAFICA_BARRAS_ANUAL.png")
    except Exception as e:
        print(f"   Se me cayó la gráfica por este error: {e}")
else:
    # Dejé esto porque en unas pruebas locales que hice, no venía F.AVISO o el tipo de cuenta y no podía graficar.
    print("   No pude graficar porque me faltaban columnas claves.")

# --- 5. ANÁLISIS FINANCIERO ---
cols_fin = ['VLR RADICACION', 'VLR APROBADO', 'VLR GLOSADO']
# Aquí me tocó limpiar campos numéricos porque me pasó que algunos traían coma como separador decimal.

for col in cols_fin:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

if 'ID RECLAMANTE' in df.columns:
    analisis = df.groupby('ID RECLAMANTE')[cols_fin].sum()
    print("\n>>> Estos fueron los 5 reclamantes mas altos:")
    print(analisis.sort_values('VLR RADICACION', ascending=False).head(5))

# --- 6. CRUCE CON PROD.PARQUET ---
try:
    df_prod = pd.read_parquet('PROD.parquet')
    # Aquí hice la detección dinámica de la columna porque no podía asumir si era "NRO. POLIZA" o "POLIZA".
    col_poliza_base = next((c for c in df.columns if "POLIZA" in c), None)
    col_poliza_prod = 'POLIZA'

    if col_poliza_base and col_poliza_prod in df_prod.columns:
        print(f"\n   Haciendo cruce: BASE['{col_poliza_base}'] <--> PROD['{col_poliza_prod}']")

        # Estos replace los implementé porque me encontré con ".0" en ambas fuentes y sin eso no cruzaba.
        df[col_poliza_base] = df[col_poliza_base].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df_prod[col_poliza_prod] = df_prod[col_poliza_prod].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        # El merge lo realicé así porque necesitaba traer ANO_MODELO y además validar que no rompa la base.
        df = pd.merge(df, df_prod[[col_poliza_prod, 'ANO_MODELO']],
                      left_on=col_poliza_base,
                      right_on=col_poliza_prod,
                      how='left')

        print("   ¡Lo logré! Ya quedó enriquecido ANO_MODELO")
    else:
        print("   falló el cruce porque no esta la columna POLIZA en ambos lados.")
except FileNotFoundError:
    # Esto lo dejé porque cuando lo probé sin el parquet en la raíz, se reventaba sin avisar.
    print("   No encontrése encontro PROD.parquet, entonces no cruzar año modelo.")
except Exception as e:
    print(f"   Se cayó merge por este error: {e}")

# --- 7. EXPORTACIÓN ---
try:
    # Lo exporté como Excel porque era parte de lo que me tocó entregar en la prueba técnica.
    df.to_excel("PRUEBA_ANÁLISIS.xlsx", index=False)
    print("\n>>> Quedó generado PRUEBA_ANÁLISIS.xlsx")
except Exception as e:
    print(f"   Falló la exportación por: {e}")
