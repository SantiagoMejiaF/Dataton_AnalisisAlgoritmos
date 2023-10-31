import time
from datetime import datetime
import pandas as pd
import os
import sys
import pulp


def definirVariablesDecision(trabajadores, franjas):
    x = pulp.LpVariable.dicts('Duplas binarias', [(
        i, t) for i in trabajadores for t in franjas], 0, 1, pulp.LpBinary)
    return x


# Variable intermedia para almacenar las diferencias
def definirVariableDiferencia(franjas):
    diferencias = pulp.LpVariable.dicts('diferencia', franjas)
    return diferencias


def agregarAsignacionDiferenciaModelo(trabajadores, franjas, demanda_clientes, diferencias, x):
    global problem

    for t in franjas:
        problem += diferencias[t] == demanda_clientes[t] - \
            pulp.lpSum(x[(i, t)] for i in trabajadores)


def agregarFuncionObjetivoModelo(diferencias, franjas):
    global problem

    problem += pulp.lpSum(diferencias[t] if (diferencias[t] >= 0) else -diferencias[t]
                          for t in franjas), "Sumatoria de diferencias absolutas"


def agregarRestriccionFranjasTrabajadasModelo(trabajadores, tipoContrato, franjas, x, tiempoMaxTC, tiempoMaxMT):
    global problem
    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]

        if (contrato == "TC"):
            problem += pulp.lpSum(x[(i, t)] for t in franjas) <= tiempoMaxTC
        else:
            problem += pulp.lpSum(x[(i, t)] for t in franjas) <= tiempoMaxMT


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
            problem += pulp.lpSum(x[(i, t)]
                                  for t in franjas[franjaInicial:franjaInicial+6]) == 0


def agregarRestriccionTrabajaContinuoAntesDespuesAlmuerzoModelo(trabajadores, tipoContrato, franjas, x, iniciosAlmuerzos):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]
        franjaInicial = iniciosAlmuerzos[indexTrabajador]

        if (contrato == "TC"):
            # Cada trabajador TC tiene que trabajar 1 hora continua antes y despues de almorzar
            problem += pulp.lpSum(x[(i, t)]
                                  for t in franjas[franjaInicial-4:franjaInicial]) == 4
            problem += pulp.lpSum(x[(i, t)]
                                  for t in franjas[franjaInicial+6:franjaInicial+10]) == 4


def agregarRestriccionNoTrabajaAntesInicioJornadaModelo(trabajadores, franjas, x, iniciosJornadas):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        franjaInicial = iniciosJornadas[indexTrabajador]

        # El trabajador no puede trabajar antes de iniciar de jornada
        problem += pulp.lpSum(x[(i, t)] for t in franjas[0:franjaInicial]) == 0


def agregarRestriccionNoTrabajaDespuesFinalJornadaModelo(trabajadores, tipoContrato, franjas, x, iniciosJornadas, tiempoMaxTC, tiempoMaxMT):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]
        franjaInicial = iniciosJornadas[indexTrabajador]

        # El trabajador no puede trabajar despues de finalizar su jornada
        if (contrato == "TC"):
            # El trabajador TC finaliza su jornada 34 franjas despues de iniciar la jornada (Se suma almuerzo)
            problem += pulp.lpSum(x[(i, t)]
                                  for t in franjas[franjaInicial+tiempoMaxTC:len(franjas)]) == 0
        else:
            # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
            problem += pulp.lpSum(x[(i, t)]
                                  for t in franjas[franjaInicial+tiempoMaxMT:len(franjas)]) == 0


def agregarRestriccionTrabajaContinuoExtremosJornadaModelo(trabajadores, tipoContrato, franjas, x, iniciosJornadas, tiempoMaxTC, tiempoMaxMT):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]
        franjaInicial = iniciosJornadas[indexTrabajador]

        # Cada trabajador tiene que trabajar 1 hora continua despues de su jornada inicio
        problem += pulp.lpSum(x[(i, t)]
                              for t in franjas[franjaInicial:franjaInicial+4]) == 4

        # Cada trabajador tiene que trabajar 1 hora continua antes de finalizar su jornada
        if (contrato == "TC"):
            # El trabajador TC finaliza su jornada 34 franjas despues de iniciar la jornada (Se suma almuerzo)
            problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial +
                                  tiempoMaxTC-4:franjaInicial+tiempoMaxTC]) == 4
        else:
            # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
            problem += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial +
                                  tiempoMaxMT-4:franjaInicial+tiempoMaxMT]) == 4


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
            # Antes de almorzar
            for franjaEspecifica in range(franjaInicialJornada, franjaInicialAlmuerzo-4):

                # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                problem += pulp.lpSum(x[(i, t)]
                                      for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                problem += pulp.lpSum(x[(i, t)]
                                      for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8

            # Despues de almorzar
            # El trabajador TC finaliza su jornada 34 franjas despues de iniciar la jornada
            for franjaEspecifica in range(franjaInicialAlmuerzo+6, franjaInicialJornada+30):

                # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                problem += pulp.lpSum(x[(i, t)]
                                      for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                if (franjaEspecifica <= len(franjas)-9):
                    problem += pulp.lpSum(x[(i, t)]
                                          for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8

        else:
            # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
            for franjaEspecifica in range(franjaInicialJornada, franjaInicialJornada+12):

                # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                problem += pulp.lpSum(x[(i, t)]
                                      for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                if (franjaEspecifica <= len(franjas)-9):
                    problem += pulp.lpSum(x[(i, t)]
                                          for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8


def agregarRestriccionPausasActivasSabadoModelo(trabajadores, tipoContrato, franjas, x, iniciosJornadas):
    # Se debe sacar 1 pausa activa despues de trabajar minimo 1 hora o maximo 2 horas
    # Eso se traduce a que en cada intervalo de 5 franjas la suma debe dar mayor o igual a 4 (Maximo una pausa activa)
    # Y además, traduce que en cada intervalo de 9 franjas no puede sumar 9 franjas trabajadas
    global problem

    for indexTrabajador in range(len(trabajadores)):
        i = trabajadores[indexTrabajador]
        contrato = tipoContrato[indexTrabajador]
        franjaInicialJornada = iniciosJornadas[indexTrabajador]

        if (contrato == "TC"):
            # El trabajador TC finaliza su jornada 20 franjas despues de iniciar la jornada
            for franjaEspecifica in range(franjaInicialJornada, franjaInicialJornada+16):

                # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                problem += pulp.lpSum(x[(i, t)]
                                      for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                if (franjaEspecifica <= len(franjas)-9):
                    problem += pulp.lpSum(x[(i, t)]
                                          for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8
        else:
            # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
            for franjaEspecifica in range(franjaInicialJornada, franjaInicialJornada+12):

                # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                problem += pulp.lpSum(x[(i, t)]
                                      for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                if (franjaEspecifica <= len(franjas)-9):
                    problem += pulp.lpSum(x[(i, t)]
                                          for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8


def optimizacionJornadas(trabajadores, tipoContrato, franjas, demanda_clientes, iniciosAlmuerzos, iniciosJornadas, diaSemana):
    global problem
    global x

    # Definir el tiempo maximo que trabaja un trabajador TC y MT
    if (diaSemana != 5):
        # Dia entre semana
        # Tiempo completo: 7 horas (28 franjas)
        # Medio tiempo: 4 horas (16 franjas)
        tiempoMaxTC = 28
        tiempoMaxMT = 16
    else:
        # Dia Sabado
        # Tiempo completo: 5 horas (20 franjas)
        # Medio tiempo: 4 horas (16 franjas)
        tiempoMaxTC = 20
        tiempoMaxMT = 16

    # Crea un problema (Modelo) de minimización lineal
    problem = pulp.LpProblem("OptimizacionJornadas", pulp.LpMinimize)

    # Define la variable binaria de decisión x (0: no trabajda 1: trabaja)
    x = definirVariablesDecision(trabajadores, franjas)

    # Define una variable intermedia para almacenar las diferencias de cada franja
    diferencias = definirVariableDiferencia(franjas)

    # Agrega a que hace referencia la diferencia
    agregarAsignacionDiferenciaModelo(
        trabajadores, franjas, demanda_clientes, diferencias, x)

    # Agrega la función objetivo para minimizar las diferencias
    agregarFuncionObjetivoModelo(diferencias, franjas)

    # Agrega las restricciones de las variables de decisión

    # Cada trabajador tiene que trabajar unas horas al dia determinadas por el tipo de contrato
    # Pero hay que tener en cuenta que hay pausas activas. Entonces esas franjas son la referencias maximas.
    agregarRestriccionFranjasTrabajadasModelo(
        trabajadores, tipoContrato, franjas, x, tiempoMaxTC, tiempoMaxMT)

    # Cada franja debe ser atendida por al menos un trabajador (Solo si la demanda es mayor o igual a 1)
    agregarRestriccionFranjaAtendidaTrabajadorModelo(
        trabajadores, franjas, demanda_clientes, x)

    # En dia de semana los trabajadores TC sacan almuerzo (No aplica para el sabado)
    if (diaSemana != 5):
        # Cada trabajador TC debe sacar 1h 30 min continua de almuerzo (6 franjas)
        # El bloque del almuerzo corresponde entre las franjas 16 y 29 (Inclusives)
        # Cada trabajador debe iniciar a almorzar entre la franja 16 y 24 (Inclusives)
        agregarRestriccionAlmuerzoContinuoModelo(
            trabajadores, tipoContrato, franjas, x, iniciosAlmuerzos)

        # Cada trabajador TC tiene que trabajar 1 hora continua antes y despues del almuerzo
        agregarRestriccionTrabajaContinuoAntesDespuesAlmuerzoModelo(
            trabajadores, tipoContrato, franjas, x, iniciosAlmuerzos)

    # Cada trabajador no puede trabajar antes de su jornada inicio
    agregarRestriccionNoTrabajaAntesInicioJornadaModelo(
        trabajadores, franjas, x, iniciosJornadas)

    # Cada trabajador no puede trabajar despues de su jornada final
    if (diaSemana != 5):
        # En semana hay que tener en cuenta el tiempo del almuerzo para saber la jornada final
        agregarRestriccionNoTrabajaDespuesFinalJornadaModelo(
            trabajadores, tipoContrato, franjas, x, iniciosJornadas, tiempoMaxTC + 6, tiempoMaxMT)
    else:
        # el sabado no hay almuerzo
        agregarRestriccionNoTrabajaDespuesFinalJornadaModelo(
            trabajadores, tipoContrato, franjas, x, iniciosJornadas, tiempoMaxTC, tiempoMaxMT)

    # Cada trabajador tiene que trabajar 1 hora continua despues de su jornada inicio y antes de su jornada final (Es decir, trabajar 1 hora continua en los extremos)
    if (diaSemana != 5):
        # En semana hay que tener en cuenta el tiempo del almuerzo para saber la jornada final
        agregarRestriccionTrabajaContinuoExtremosJornadaModelo(
            trabajadores, tipoContrato, franjas, x, iniciosJornadas, tiempoMaxTC + 6, tiempoMaxMT)
    else:
        # el sabado no hay almuerzo
        agregarRestriccionTrabajaContinuoExtremosJornadaModelo(
            trabajadores, tipoContrato, franjas, x, iniciosJornadas, tiempoMaxTC, tiempoMaxMT)

    # Se debe sacar 1 pausa activa despues de trabajar minimo 1 hora o maximo 2 horas
    if (diaSemana != 5):
        agregarRestriccionPausasActivasModelo(
            trabajadores, tipoContrato, franjas, x, iniciosAlmuerzos, iniciosJornadas)
    else:
        agregarRestriccionPausasActivasSabadoModelo(
            trabajadores, tipoContrato, franjas, x, iniciosJornadas)

    # Resuelve el problema
    solver = pulp.PULP_CBC_CMD(msg=0)
    problem.solve(solver)


def crearSemillaIniciosJornadasAlmuerzosSabados(trabajadores, tipoContrato):
    iniciosJornadas = []
    iniciosAlmuerzos = []

    # Cada trabajador TC puede comenzar a trabjar entre la franja 0 y 15 (Inclusives)
    franjaInicialJornadaTC = 0  # 7:30 am

    # Cada trabajador MT maximo puede entrar en la flanja 33 (3:45 pm), si entra mas tarde no cumple sus 4 horas de trabajo
    # DUDA: Entonces por qué el enunciado dice que puede entrar a mas tardar a las 4:30pm?
    franjaInicialJornadaMT = 33  # 3:45 pm

    # El inicio del almuerzo puede ir entre la franja 16 y 24 (Inclusives)
    franjaInicialAlmuerzoTC = 16  # 11:30 am

    for indexTrabajador in range(len(trabajadores)):

        if (tipoContrato[indexTrabajador] == "TC"):
            iniciosJornadas += [franjaInicialJornadaTC]
            franjaInicialJornadaTC += 1

            iniciosAlmuerzos += [franjaInicialAlmuerzoTC]
            franjaInicialAlmuerzoTC += 2
        else:
            iniciosJornadas += [franjaInicialJornadaMT]
            franjaInicialJornadaMT -= 5

            iniciosAlmuerzos += [-1]  # Los MT no almuerzan

    # En caso de que sea sabado, no hay almuerzos y los inicios de jornadas puede ser diferente al semanal
    iniciosSabados = []
    franjaInicialJornada = 0  # 7:30 am
    for i in trabajadores:
        iniciosSabados += [franjaInicialJornada]
        franjaInicialJornada += 1

    return [iniciosJornadas, iniciosAlmuerzos, iniciosSabados]


def conseguirIniciosJornadasOptimosSucursal(suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados):

    # Variables globales
    trabajadores = list(trabajadores_df_sucursal.documento)
    tipoContrato = list(trabajadores_df_sucursal.contrato)

    # Valor inicial de la sobredemanda optima e inicios optimos de las jornadas
    sobredemandaOptima = optimizaciónJornadasSucursal(
        suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados)
    iniciosJornadasOptimo = iniciosJornadas.copy()

    for indexTrabajador in range(len(trabajadores)):

        contrato = tipoContrato[indexTrabajador]
        if (contrato == "TC"):
            franjaMinima = 0
            franjaMaxima = 15  # Inclusive
        else:
            franjaMinima = 0
            franjaMaxima = 33  # Inclusive

        for franjaInicialTrabajador in range(franjaMinima, franjaMaxima+1):
            # Nueva combinación de inicio de jornadas en base al ultimo optimo encontrado
            iniciosJornadasActual = iniciosJornadasOptimo.copy()
            iniciosJornadasActual[indexTrabajador] = franjaInicialTrabajador

            # Correr modelo con la nueva combinación de iniciosJornadas y calcula su sobredemanda
            sobredemandaActual = optimizaciónJornadasSucursal(
                suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadasActual, iniciosAlmuerzos, iniciosSabados)

            if (sobredemandaActual < sobredemandaOptima):
                sobredemandaOptima = sobredemandaActual
                iniciosJornadasOptimo = iniciosJornadasActual.copy()

    return iniciosJornadasOptimo


def conseguirIniciosAlmuerzosOptimosSucursal(suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados):

    # Variables globales
    trabajadores = list(trabajadores_df_sucursal.documento)
    tipoContrato = list(trabajadores_df_sucursal.contrato)

    # Valor inicial de la sobredemanda optima e inicios optimos de las jornadas
    sobredemandaOptima = optimizaciónJornadasSucursal(
        suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados)
    iniciosAlmuerzosOptimo = iniciosAlmuerzos.copy()

    for indexTrabajador in range(len(trabajadores)):

        contrato = tipoContrato[indexTrabajador]
        if (contrato == "TC"):
            franjaMinima = 16
            franjaMaxima = 24  # Inclusive
        else:
            franjaMinima = 0
            franjaMaxima = -1

        for franjaInicialTrabajador in range(franjaMinima, franjaMaxima+1):
            # Nueva combinación de inicio de almuerso en base al ultimo optimo encontrado
            iniciosAlmuerzosActual = iniciosAlmuerzosOptimo.copy()
            iniciosAlmuerzosActual[indexTrabajador] = franjaInicialTrabajador

            # Correr modelo con la nueva combinación de iniciosJornadas y calcula su sobredemanda
            sobredemandaActual = optimizaciónJornadasSucursal(
                suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzosActual, iniciosSabados)

            if (sobredemandaActual < sobredemandaOptima):
                sobredemandaOptima = sobredemandaActual
                iniciosAlmuerzosOptimo = iniciosAlmuerzosActual.copy()

    return iniciosAlmuerzosOptimo


def conseguirIniciosSabadosOptimosSucursal(suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados):

    # Variables globales
    trabajadores = list(trabajadores_df_sucursal.documento)
    tipoContrato = list(trabajadores_df_sucursal.contrato)

    # Valor inicial de la sobredemanda optima e inicios optimos de las jornadas
    sobredemandaOptima = optimizaciónJornadasSucursal(
        suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados)
    iniciosSabadosOptimo = iniciosSabados.copy()

    for indexTrabajador in range(len(trabajadores)):

        contrato = tipoContrato[indexTrabajador]
        if (contrato == "TC"):
            franjaMinima = 0
            franjaMaxima = 9  # Inclusive
        else:
            franjaMinima = 0
            franjaMaxima = 13  # Inclusive

        for franjaInicialTrabajador in range(franjaMinima, franjaMaxima+1):
            # Nueva combinación de inicio de sabados en base al ultimo optimo encontrado
            iniciosSabadosActual = iniciosSabadosOptimo.copy()
            iniciosSabadosActual[indexTrabajador] = franjaInicialTrabajador

            # Correr modelo con la nueva combinación de iniciosJornadas y calcula su sobredemanda
            sobredemandaActual = optimizaciónJornadasSucursal(
                suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabadosActual)

            if (sobredemandaActual < sobredemandaOptima):
                sobredemandaOptima = sobredemandaActual
                iniciosSabadosOptimo = iniciosSabadosActual.copy()

    return iniciosSabadosOptimo


def crearDataframeOptimoVacio(solucionOptima_df):

    # Definir la estructura del DataFrame
    columnas = ["suc_cod", "documento", "fecha",
                "hora", "estado", "hora_franja"]

    # Crear un DataFrame vacío
    solucionOptima_df = pd.DataFrame(columns=columnas, dtype="object")

    return solucionOptima_df


def guardarResultadoOptimoDia(solucionOptimaSucursal_df, trabajadores, tipoContrato, franjas, iniciosAlmuerzos, fecha_hora, suc_cod, fecha_actual, diaSemana):
    global x

    # Vamos a rellenar toda la data optima de este dia para guardarlo en el dataframe acumulador
    horas = [fechaHora.time().strftime("%H:%M") for fechaHora in fecha_hora]

    suc_codOptimo = [suc_cod]*(len(franjas)*len(trabajadores))
    documentoOptimo = []
    fechaOptimo = [fecha_actual.strftime(
        "%d/%m/%Y")]*(len(franjas)*len(trabajadores))
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
                    if(diaSemana != 5 and contrato == "TC" and t in range(iniciosAlmuerzos[indexTrabajador], iniciosAlmuerzos[indexTrabajador]+6)):
                        # Solo entra a este condicional si es dia en semana (Lunes a Viernes) y si es un trabajador TC y se encuentra en tiempo de almuerzo
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
    data = {'suc_cod': suc_codOptimo, 'documento': documentoOptimo, 'fecha': fechaOptimo,
            'hora': horaOptimo, 'estado': estadoOptimo, 'hora_franja': franjaOptimo}

    solucionOptimaDia_df = pd.DataFrame(data)
    solucionOptimaDia_df = solucionOptimaDia_df.sort_values(
        by=['documento', 'hora_franja'])

    # Concatenar los datos optimos de ese dia con los otros dias que hemos recolectado hasta ahora
    solucionOptimaSucursal_df = pd.concat(
        [solucionOptimaSucursal_df, solucionOptimaDia_df], ignore_index=True)

    return solucionOptimaSucursal_df


def crearCSVResultadoOptimo():
    global solucionOptima_df

    # Archivo CSV
    solucionOptima_df.to_csv(
        "./src/PuLP/Etapa2/solucionOptimaEtapa2.csv", index=False)

    print("Asignación Óptima de Horarios realizada")


def resultadoSobredemanda(demanda_df, solucionOptima_df):
    # Acomodar el df de demanda al mismo formato de la solución
    demanda = demanda_df.copy()
    demanda['fecha'] = demanda['fecha_hora'].dt.strftime("%d/%m/%Y")
    demanda['hora'] = demanda['fecha_hora'].dt.strftime("%H:%M")
    demanda = demanda.drop('fecha_hora', axis=1)

    # agrupar por sucursal/dia/hora para saber cuandos trabajadores trabajan en esa agrupación
    solucion = solucionOptima_df.copy()
    solucion = solucion[solucion['estado'] == 'Trabaja'].groupby(
        ['suc_cod', 'fecha', 'hora'])['estado'].count().reset_index()

    # Hacer merge con la demanda para luego encontrar el resultado de la demanda - trabajadores
    solucion = solucion.merge(demanda[['suc_cod', 'fecha', 'hora', 'demanda']], on=[
                              'suc_cod', 'fecha', 'hora'], how='left')
    solucion = solucion.rename(columns={'estado': 'trabajadores'})
    solucion['resultado'] = solucion['demanda'] - solucion['trabajadores']

    # Encontrar la sobredemanda (solo sumar los valores positvos)
    sobredemanda = solucion[solucion['resultado'] > 0]['resultado'].sum()

    return sobredemanda


def optimizaciónJornadasSucursal(suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados):
    global problem
    global solucionOptimaSucursal_df

    # Crea la estructura del dataframe de resultados de la sucursal
    solucionOptimaSucursal_df = pd.DataFrame()
    solucionOptimaSucursal_df = crearDataframeOptimoVacio(
        solucionOptimaSucursal_df)

    # Variables completas
    trabajadores = list(trabajadores_df_sucursal.documento)
    tipoContrato = list(trabajadores_df_sucursal.contrato)

    # Fechas unicas
    fechasUnicas = demanda_df_sucursal.fecha_hora.dt.date.unique()

    # Lista para almacenar los estados de los modelos diarios para evaluarlos luego
    estadosModelosSucursal = []

    # De lunes a sabado
    for indexFecha in range(len(fechasUnicas)):
        fecha_actual = fechasUnicas[indexFecha]
        diaSemana = fecha_actual.weekday()  # 0:Lunes ... 5:Sabado

        # DataFrame por dia (No es necesario hacerlo por trabajador)
        demanda_df_dia = demanda_df_sucursal[(
            demanda_df_sucursal["fecha_hora"].dt.date == fecha_actual)]

        # Variables completas por dia
        fecha_hora = list(demanda_df_dia.fecha_hora)
        demanda_clientes = list(demanda_df_dia.demanda)

        # Franjas de cada dia
        # De 0 (7:30am) hasta la ultima demanda registrada
        franjas = list(range(0, len(demanda_clientes)))

        # En caso de que sea sabado, no hay almuerzos y los inicios de jornadas puede ser diferente al semanal
        if (diaSemana == 5):
            iniciosJornadas = iniciosSabados.copy()

        # Modelo por dia
        optimizacionJornadas(trabajadores, tipoContrato, franjas,
                             demanda_clientes, iniciosAlmuerzos, iniciosJornadas, diaSemana)

        # Guarda el estado del modelo del dia (óptimo, subóptimo, etc.)
        estadosModelosSucursal += [pulp.LpStatus[problem.status]]

        # Guarda los resultados del dia en un dataframe acumulador
        solucionOptimaSucursal_df = guardarResultadoOptimoDia(
            solucionOptimaSucursal_df, trabajadores, tipoContrato, franjas, iniciosAlmuerzos, fecha_hora, suc_cod, fecha_actual, diaSemana)

    # Resultado de la sobredemanda de la sucursal
    if (estadosModelosSucursal == ['Optimal', 'Optimal', 'Optimal', 'Optimal', 'Optimal', 'Optimal']):
        sobredemanda = resultadoSobredemanda(
            demanda_df_sucursal, solucionOptimaSucursal_df)
    else:
        sobredemanda = 1000000

    return sobredemanda


class stopwatch:
    def __init__(self):
        self.start = datetime.now()

    @property
    def time(self):
        return datetime.now() - self.start

    def reset(self):
        self.start = datetime.now()


# Inicio del Main
# os.chdir("..")
# os.chdir("..")
# os.chdir("..")

old_stdout = sys.stdout  # backup current stdout
sys.stdout = open(os.devnull, "w")


# Inicializar la variable que contará el tiempo de ejecución
timer = stopwatch()

# Inicializa la variable que tendrá el modelo de optimización
problem = pulp.LpProblem("OptimizacionJornadasLaborales", pulp.LpMinimize)

# Crea los dataFrame vacios donde irá la respuesta optima guardada
solucionOptima_df = pd.DataFrame()
solucionOptima_df = crearDataframeOptimoVacio(solucionOptima_df)

# Extración de datos del excel
dataton2023 = './src/PuLP/Etapa2/Dataton 2023 Etapa 2.xlsx'

# DataFrames generales
demanda_df = pd.read_excel(dataton2023, sheet_name='demand')
trabajadores_df = pd.read_excel(dataton2023, sheet_name='workers')

# Realizar el mismo proceso por cada sucursal (5 sucursales)
sobredemanda = 0
for suc_cod in demanda_df.suc_cod.unique():

    # DataFrames por sucursal
    demanda_df_sucursal = demanda_df[(demanda_df["suc_cod"] == suc_cod)]
    trabajadores_df_sucursal = trabajadores_df[(
        trabajadores_df["suc_cod"] == suc_cod)]

    # Variables globales
    trabajadores = list(trabajadores_df_sucursal.documento)
    tipoContrato = list(trabajadores_df_sucursal.contrato)

    # Semilla de los inicios de almuerzos, jornadas y sabados (No sigue una razón en particular)
    iniciosSemilla = crearSemillaIniciosJornadasAlmuerzosSabados(
        trabajadores, tipoContrato)
    iniciosJornadas = iniciosSemilla[0]
    iniciosAlmuerzos = iniciosSemilla[1]
    iniciosSabados = iniciosSemilla[2]

    for iteracion in range(2):
        # Encontrar inicios optimos de jornadas de la sucursal
        iniciosJornadas = conseguirIniciosJornadasOptimosSucursal(
            suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados)

        # Encontrar inicios optimos de almuerzos de la sucursal
        iniciosAlmuerzos = conseguirIniciosAlmuerzosOptimosSucursal(
            suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados)

        # Encontrar inicios optimos de la jornada del sabado de la sucursal
        iniciosSabados = conseguirIniciosSabadosOptimosSucursal(
            suc_cod, demanda_df_sucursal, trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados)

    # Modelo final que optimiza las jornadas laborales por esa sucursal
    sobredemanda += optimizaciónJornadasSucursal(suc_cod, demanda_df_sucursal,
                                                 trabajadores_df_sucursal, iniciosJornadas, iniciosAlmuerzos, iniciosSabados)

    solucionOptima_df = pd.concat(
        [solucionOptima_df, solucionOptimaSucursal_df], ignore_index=True)


# Resultado de la función objetivo
print('La sobredemanda resultante es: ', sobredemanda)

# Luego de correr los modelos por sucursal y por dia, guardar los resultados acumulados en un .csv
crearCSVResultadoOptimo()

# Imprime el tiempo que se demoró en ejecutar el código
print('El tiempo de ejecución es de: ', timer.time)
