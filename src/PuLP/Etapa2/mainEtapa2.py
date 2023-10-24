def optimizacionJornadas():
    return None

def crearDataframesOptimos():
    return None

def guardarDatosOptimos():
    return None






#Inicio del Main

import pulp
import pandas as pd

# Inicializa la variable que tendrá el modelo de optimización
problem = pulp.LpProblem("OptimizacionJornadasLaborales", pulp.LpMinimize)

# Crea los dataFrame vacios donde irá la respuesta optima guardad
crearDataframesOptimos()

# Extración de datos del excel
dataton2023 = './src/PuLP/Etapa2/Dataton 2023 Etapa 2.xlsx'

# DataFrames generales
demanda_df = pd.read_excel(dataton2023, sheet_name='demand')
trabajadores_df = pd.read_excel(dataton2023, sheet_name='workers')

# Realizar el mismo proceso por cada sucursal (5 sucursales)
for suc_cod in demanda_df.suc_cod.unique():

    # DataFrames por sucursal
    demanda_df_sucursal = demanda_df[(demanda_df["suc_cod"] == suc_cod)]
    trabajadores_df_sucursal = trabajadores_df[(trabajadores_df["suc_cod"] == suc_cod)]

    # Variables completas 
    trabajadores = list(trabajadores_df_sucursal.documento)
    tipo_contrato = list(trabajadores_df_sucursal.contrato)

    # Encontrar inicios optimos de almuerzo y jornadas

    ## Semilla de los inicios de almuerzos y jornadas (No sigue una razón en particular)
    franjaInicialJornadaTC = 0 # 7:30 am
    franjaInicialJornadaMT = 36 # 4:30 pm
    franjaInicialAlmuerzoTC = 16 # 11:30 am
    iniciosJornadas = []
    iniciosAlmuerzos = []

    for indexTrabajador in range(len(trabajadores)):

        if (tipo_contrato[indexTrabajador] == "TC"):
            iniciosJornadas += [franjaInicialJornadaTC]
            franjaInicialJornadaTC += 2

            iniciosAlmuerzos += [franjaInicialAlmuerzoTC]
            franjaInicialAlmuerzoTC += 2
        else:
            iniciosJornadas += [franjaInicialJornadaMT]
            franjaInicialJornadaTC -= 5

            iniciosAlmuerzos += [-1] # Los MT no almuerzan

    ##################
    # AQUI DEBERIA HABER UN CÓDIGO QUE ENCUENTRE LOS INICIOS OPTIMOS
    ##################

    # Fechas unicas
    fechas_unicas = demanda_df_sucursal.fecha_hora.dt.date.unique()

    # De lunes a viernes
    for indexFecha in range(len(fechas_unicas)-1):
        fecha_actual = fechas_unicas[indexFecha]

        # DataFrame por dia (No es necesario hacerlo por trabajador)
        demanda_df_dia = demanda_df_sucursal[(demanda_df_sucursal["fecha_hora"].dt.date == fecha_actual)]

        # Variables completas por dia 
        fecha_hora = list(demanda_df_dia.fecha_hora)
        demanda_clientes = list(demanda_df_dia.demanda)
        
        # Franjas de cada dia
        franjas = list(range(0, len(demanda_clientes)))  # De 0 (7:30am) hasta la ultima demanda registrada
 
        # Modelo final por dia (Guardar progresivamente los resultados en un dataframe)
        optimizacionJornadas()
        guardarDatosOptimos()


    ##################
    # AQUI DEBERIA HACER EL CÓDIGO DE OPTIMIZACIÓN PARA EL SABADO
    ##################


##################
# Luego de correr los modelos por sucursal Y por dia, guardar los resultados acumulados en un .csv
##################


##################
# AQUI DEBERIA IMPRIMIR LAS GRÁFICAS CORRESPONDIENTES A LA SOLUCIÓN Y EL RESULTADO FINAL DE LA FUNCIÓN OBJETIVO
##################
