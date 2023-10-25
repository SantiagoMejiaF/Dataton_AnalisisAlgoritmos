def definirVariablesDecision(trabajadores, franjas):
    x = pulp.LpVariable.dicts('Duplas binarias', [(i, t) for i in trabajadores for t in franjas], 0, 1, pulp.LpBinary)
    return x


# Variable intermedia para almacenar las diferencias
def definirVariableDiferencia(franjas):
    diferencias = pulp.LpVariable.dicts('diferencia', franjas)
    return diferencias


def agregarAsignacionDiferenciaModelo(trabajadores, franjas, demanda_clientes, diferencias, x):
    global problem

    for t in franjas:
        problem += diferencias[t] == demanda_clientes[t] - pulp.lpSum(x[(i, t)] for i in trabajadores)


def agregarFuncionObjetivoModelo(diferencias,franjas):
    global problem

    problem += pulp.lpSum(diferencias[t] if (diferencias[t]>=0) else -diferencias[t] for t in franjas), "Sumatoria de diferencias absolutas"


def agregarRestriccionFranjasTrabajadasModelo(trabajadores, tipoContrato, franjas, x):
    global problem
    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]

        if (contrato == "TC"):
            problem += pulp.lpSum(x[(i, t)] for t in franjas) <= 28
        else:
            problem += pulp.lpSum(x[(i, t)] for t in franjas) <= 16


def agregarRestriccionFranjaAtendidaTrabajadorModelo(trabajadores, franjas, demanda_clientes, x):
    global problem
    for t in franjas:
        if (demanda_clientes[t] >= 1):
            problem += pulp.lpSum(x[(i, t)] for i in trabajadores) >= 1


def agregarRestriccionAlmuerzoContinuoModelo(trabajadores, tipoContrato, franjas, x, iniciosAlmuerzo):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]
        franjaInicial = iniciosAlmuerzo[indexTrabajador]

        if (contrato == "TC"):
            # El trabajador TC no puede trabajar durante las 6 franjas del almuerzo
            problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial:franjaInicial+6]) == 0


def agregarRestriccionTrabajaContinuoAntesDespuesAlmuerzoModelo(trabajadores, tipoContrato, franjas, x, iniciosAlmuerzos):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]
        franjaInicial = iniciosAlmuerzos[indexTrabajador]

        if (contrato == "TC"):
            # Cada trabajador TC tiene que trabajar 1 hora continua antes y despues de almorzar
            problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial-4:franjaInicial]) == 4
            problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial+6:franjaInicial+10]) == 4


def agregarRestriccionNoTrabajaAntesInicioJornadaModelo(trabajadores, franjas, x, iniciosJornadas):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        franjaInicial = iniciosJornadas[indexTrabajador]

        # El trabajador no puede trabajar antes de iniciar de jornada
        problem += pulp.lpSum(x[(i, t)] for t in franjas[0:franjaInicial]) == 0


def agregarRestriccionNoTrabajaDespuesFinalJornadaModelo(trabajadores, tipoContrato, franjas, x, iniciosJornadas):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]
        franjaInicial = iniciosJornadas[indexTrabajador]
        
        # El trabajador no puede trabajar despues de finalizar su jornada
        if (contrato == "TC"):
            # El trabajador TC finaliza su jornada 34 franjas despues de iniciar la jornada (Se suma almuerzo)
            problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial+34:len(franjas)]) == 0
        else:
            # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
            problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial+16:len(franjas)]) == 0


def agregarRestriccionTrabajaContinuoExtremosJornadaModelo(trabajadores, tipoContrato, franjas, x, iniciosJornadas):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]
        franjaInicial = iniciosJornadas[indexTrabajador]

        # Cada trabajador tiene que trabajar 1 hora continua despues de su jornada inicio
        problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial:franjaInicial+4]) == 4

        # Cada trabajador tiene que trabajar 1 hora continua antes de finalizar su jornada
        if (contrato == "TC"):
            # El trabajador TC finaliza su jornada 34 franjas despues de iniciar la jornada (Se suma almuerzo)
            problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial+30:franjaInicial+34]) == 4
        else:
            # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
            problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial+12:franjaInicial+16]) == 4


def agregarRestriccionPausasActivasModelo(trabajadores, tipoContrato, franjas, x, iniciosAlmuerzos, iniciosJornadas):
    # Se debe sacar 1 pausa activa despues de trabajar minimo 1 hora o maximo 2 horas
    # Eso se traduce a que en cada intervalo de 5 franjas la suma debe dar mayor o igual a 4 (Maximo una pausa activa)
    # Y además, traduce que en cada intervalo de 9 franjas no puede sumar 9 franjas trabajadas 
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]
        franjaInicialJornada = iniciosJornadas[indexTrabajador]
        franjaInicialAlmuerzo = iniciosAlmuerzos[indexTrabajador]
        
        if (contrato == "TC"):
            ## Antes de almorzar
            for franjaEspecifica in range(franjaInicialJornada,franjaInicialAlmuerzo-4):
                
                # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8
            
            ## Despues de almorzar
            # El trabajador TC finaliza su jornada 34 franjas despues de iniciar la jornada
            for franjaEspecifica in range(franjaInicialAlmuerzo+6,franjaInicialJornada+30):

                # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                if (franjaEspecifica <= len(franjas)-9):
                    problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8

        else:
            # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
            for franjaEspecifica in range(franjaInicialJornada,franjaInicialJornada+12):

                # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                if (franjaEspecifica <= len(franjas)-9):
                    problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8


def optimizacionJornadas(trabajadores, tipoContrato, franjas, demanda_clientes, iniciosAlmuerzos, iniciosJornadas):
    global problem
    global x

    # Crea un problema (Modelo) de minimización lineal
    problem = pulp.LpProblem("OptimizacionJornadas", pulp.LpMinimize)

    # Define la variable binaria de decisión x (0: no trabajda 1: trabaja)
    x = definirVariablesDecision(trabajadores, franjas)
    
    # Define una variable intermedia para almacenar las diferencias de cada franja
    diferencias = definirVariableDiferencia(franjas)

    # Agrega a que hace referencia la diferencia
    agregarAsignacionDiferenciaModelo(trabajadores, franjas, demanda_clientes, diferencias, x)
    
    # Agrega la función objetivo para minimizar las diferencias
    agregarFuncionObjetivoModelo(diferencias,franjas)

    # Agrega las restricciones de las variables de decisión

    ## Cada trabajador tiene que trabajar unas horas al dia determinadas por el tipo de contrato
    ## Tiempo completo: 7 horas (28 franjas)
    ## Medio tiempo: 4 horas (16 franjas)
    ## Pero hay que tener en cuenta que hay pausas activas. Entonces esas franjas son la referencias maximas.
    agregarRestriccionFranjasTrabajadasModelo(trabajadores, tipoContrato, franjas, x)

    ## Cada franja debe ser atendida por al menos un trabajador (Solo si la demanda es mayor o igual a 1)
    agregarRestriccionFranjaAtendidaTrabajadorModelo(trabajadores, franjas, demanda_clientes, x)

    ## Cada trabajador TC debe sacar 1h 30 min continua de almuerzo (6 franjas)
    ## El bloque del almuerzo corresponde entre las franjas 16 y 29 (Inclusives)
    ## Cada trabajador debe iniciar a almorzar entre la franja 16 y 24 (Inclusives)
    agregarRestriccionAlmuerzoContinuoModelo(trabajadores, tipoContrato, franjas, x, iniciosAlmuerzos)

    ## Cada trabajador TC tiene que trabajar 1 hora continua antes y despues del almuerzo
    agregarRestriccionTrabajaContinuoAntesDespuesAlmuerzoModelo(trabajadores, tipoContrato, franjas, x, iniciosAlmuerzos)

    ## Cada trabajador no puede trabajar antes de su jornada inicio
    agregarRestriccionNoTrabajaAntesInicioJornadaModelo(trabajadores, franjas, x, iniciosJornadas)

    ## Cada trabajador no puede trabajar despues de su jornada final
    agregarRestriccionNoTrabajaDespuesFinalJornadaModelo(trabajadores, tipoContrato, franjas, x, iniciosJornadas)

    ## Cada trabajador tiene que trabajar 1 hora continua despues de su jornada inicio y antes de su jornada final (Es decir, trabajar 1 hora continua en los extremos)
    agregarRestriccionTrabajaContinuoExtremosJornadaModelo(trabajadores, tipoContrato, franjas, x, iniciosJornadas)

    ## Se debe sacar 1 pausa activa despues de trabajar minimo 1 hora o maximo 2 horas
    agregarRestriccionPausasActivasModelo(trabajadores, tipoContrato, franjas, x, iniciosAlmuerzos, iniciosJornadas)

    # Resuelve el problema
    problem.solve()

    # Imprime el estado del problema (óptimo, subóptimo, etc.)
    print("Estado:", pulp.LpStatus[problem.status])

    # Imprime el valor optimo de la diferencia
    print("Valor optimo de la Diferencia:", pulp.value(problem.objective))


def crearSemillaIniciosJornadasAlmuerzos(trabajadores, tipoContrato):
    global iniciosJornadas
    global iniciosAlmuerzos

    franjaInicialJornadaTC = 0 # 7:30 am
    franjaInicialJornadaMT = 36 # 4:30 pm
    franjaInicialAlmuerzoTC = 16 # 11:30 am

    for indexTrabajador in range(len(trabajadores)):

        if (tipoContrato[indexTrabajador] == "TC"):
            iniciosJornadas += [franjaInicialJornadaTC]
            franjaInicialJornadaTC += 2

            iniciosAlmuerzos += [franjaInicialAlmuerzoTC]
            franjaInicialAlmuerzoTC += 2
        else:
            iniciosJornadas += [franjaInicialJornadaMT]
            franjaInicialJornadaTC -= 5

            iniciosAlmuerzos += [-1] # Los MT no almuerzan


def crearDataframeOptimoVacio():
    global solucionOptima_df

    # Definir la estructura del DataFrame
    columnas = ["suc_cod", "documento", "fecha", "hora", "estado", "hora_franja"]

    # Crear un DataFrame vacío
    solucionOptima_df = pd.DataFrame(columns=columnas, dtype="object")


def guardarResultadoOptimoDia(trabajadores, tipoContrato, franjas, iniciosAlmuerzos, fecha_hora, suc_cod, fecha_actual):
    global solucionOptima_df
    global x

    # Vamos a rellenar toda la data optima de este dia para guardarlo en el dataframe acumulador 
    horas = [fechaHora.time().strftime("%H:%M") for fechaHora in fecha_hora]

    suc_codOptimo = [suc_cod]*(len(franjas)*len(trabajadores))
    documentoOptimo = []
    fechaOptimo = [fecha_actual.strftime("%d/%m/%Y")]*(len(franjas)*len(trabajadores))
    horaOptimo = []
    estadoOptimo = []
    franjaOptimo = []

    for t in franjas:
        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]
            contrato = tipoContrato[indexTrabajador]
            documentoOptimo += [i]
            
            if pulp.value(x[(i, t)]) == 1:
                estadoOptimo += ["Trabaja"]
            else:
                if (t != 0 and t != len(franjas)-1):
                    if(contrato == "TC" and t in range(iniciosAlmuerzos[indexTrabajador],iniciosAlmuerzos[indexTrabajador]+6)):
                        estadoOptimo += ["Almuerza"]
                    elif (pulp.value(x[(i, t-1)]) == 1 and pulp.value(x[(i, t+1)]) == 1):
                        estadoOptimo += ["Pausa Activa"]
                    else:
                        estadoOptimo += ["Nada"]
                else:
                    estadoOptimo += ["Nada"]
            
            horaOptimo += [horas[t]]
            franjaOptimo += [t+30]

    # Crear el dataframe del dia en el que estamos
    data = {'suc_cod': suc_codOptimo, 'documento': documentoOptimo, 'fecha': fechaOptimo, 'hora': horaOptimo, 'estado': estadoOptimo, 'hora_franja': franjaOptimo}

    solucionOptimaDia_df = pd.DataFrame(data)
    solucionOptimaDia_df = solucionOptimaDia_df.sort_values(by=['documento','hora_franja'])

    # Concatenar los datos optimos de ese dia con los otros datos que hemos recolectado hasta ahora
    solucionOptima_df = pd.concat([solucionOptima_df, solucionOptimaDia_df], ignore_index=True)


def crearCSVResultadoOptimo():
    global solucionOptima_df

    ## Archivo CSV
    solucionOptima_df.to_csv("./src/PuLP/Etapa2/solucionOptimaEtapa2.csv", index=False) 

    print("Asignación Óptima de Horarios realizada")

    


#Inicio del Main

import pulp
import pandas as pd

# Inicializa la variable que tendrá el modelo de optimización
problem = pulp.LpProblem("OptimizacionJornadasLaborales", pulp.LpMinimize)

# Crea los dataFrame vacios donde irá la respuesta optima guardada
solucionOptima_df = pd.DataFrame()
crearDataframeOptimoVacio()

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
    tipoContrato = list(trabajadores_df_sucursal.contrato)

    # Encontrar inicios optimos de almuerzo y jornadas

    ## Semilla de los inicios de almuerzos y jornadas (No sigue una razón en particular)
    iniciosJornadas = []
    iniciosAlmuerzos = []
    crearSemillaIniciosJornadasAlmuerzos(trabajadores, tipoContrato)
    
    ##################
    # AQUI DEBERIA HABER UN CÓDIGO QUE ENCUENTRE LOS INICIOS OPTIMOS
    ##################

    # Fechas unicas
    fechasUnicas = demanda_df_sucursal.fecha_hora.dt.date.unique()

    # De lunes a viernes
    for indexFecha in range(len(fechasUnicas)-1):
        fecha_actual = fechasUnicas[indexFecha]

        # DataFrame por dia (No es necesario hacerlo por trabajador)
        demanda_df_dia = demanda_df_sucursal[(demanda_df_sucursal["fecha_hora"].dt.date == fecha_actual)]

        # Variables completas por dia 
        fecha_hora = list(demanda_df_dia.fecha_hora)
        demanda_clientes = list(demanda_df_dia.demanda)
        
        # Franjas de cada dia
        franjas = list(range(0, len(demanda_clientes)))  # De 0 (7:30am) hasta la ultima demanda registrada
 
        # Modelo final por dia
        optimizacionJornadas(trabajadores, tipoContrato, franjas, demanda_clientes, iniciosAlmuerzos, iniciosJornadas)

        # Guardar progresivamente los resultados en un dataframe acumulador
        guardarResultadoOptimoDia(trabajadores, tipoContrato, franjas, iniciosAlmuerzos, fecha_hora, suc_cod, fecha_actual)


    ##################
    # AQUI DEBERIA HACER EL CÓDIGO DE OPTIMIZACIÓN PARA EL SABADO
    ##################


# Luego de correr los modelos por sucursal y por dia, guardar los resultados acumulados en un .csv
crearCSVResultadoOptimo()


##################
# AQUI DEBERIA IMPRIMIR LAS GRÁFICAS CORRESPONDIENTES A LA SOLUCIÓN Y EL RESULTADO FINAL DE LA FUNCIÓN OBJETIVO
##################
