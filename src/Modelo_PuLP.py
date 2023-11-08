from datetime import datetime
import pandas as pd
import pulp
from .Parametros import Parametros as P


class Services:

    def definirVariablesDecision(trabajadores, franjas):
        x = pulp.LpVariable.dicts('Duplas binarias', [(
            i, t) for i in trabajadores for t in franjas], 0, 1, pulp.LpBinary)
        return x

    # Variable intermedia para almacenar las diferencias

    def definirVariableDiferencia(franjas):
        diferencias = pulp.LpVariable.dicts('diferencia', franjas)
        return diferencias

    def crearDataframeOptimoVacio(solucionOptima_df):

        # Definir la estructura del DataFrame
        columnas = ["suc_cod", "documento", "fecha",
                    "hora", "estado", "hora_franja"]

        # Crear un DataFrame vacío
        solucionOptima_df = pd.DataFrame(columns=columnas, dtype="object")

        return solucionOptima_df

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

    def crear_df_optimo(
            solucionOptimaSucursal_df,
            trabajadores,
            tipoContrato,
            franjas,
            iniciosAlmuerzos,
            fecha_hora,
            suc_cod,
            fecha_actual,
            diaSemana,
            x
    ):
        # Vamos a rellenar toda la data optima de este dia para guardarlo en el dataframe acumulador
        horas = [fechaHora.time().strftime("%H:%M")
                 for fechaHora in fecha_hora]

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

        return solucionOptimaDia_df

    def guardarResultadoOptimoDia(
            solucionOptimaSucursal_df,
            trabajadores,
            tipoContrato,
            franjas,
            iniciosAlmuerzos,
            fecha_hora,
            suc_cod,
            fecha_actual,
            diaSemana,
            x
    ):

        solucionOptimaDia_df = Services.crear_df_optimo(
            solucionOptimaSucursal_df,
            trabajadores,
            tipoContrato,
            franjas,
            iniciosAlmuerzos,
            fecha_hora,
            suc_cod,
            fecha_actual,
            diaSemana,
            x)

        # Concatenar los datos optimos de ese dia con los otros dias que hemos recolectado hasta ahora
        solucionOptimaSucursal_df = pd.concat(
            [solucionOptimaSucursal_df, solucionOptimaDia_df], ignore_index=True)

        return solucionOptimaSucursal_df

    def Inicios_df_optimo(suc_cod, df_optimo):
        inicios = {}

        def hora2franja(hora):
            return int(sum([
                int(t)/(60**i)
                for i, t in enumerate(hora.split(':'))]
            )*4-30)

        for fecha in df_optimo.fecha.unique():
            inicios_dia = {}
            for estado in df_optimo.estado.unique():
                df_fecha = df_optimo.query(
                    f'suc_cod == {suc_cod} & fecha == "{fecha}" & estado == "{estado}"')

                inicios_estado = df_fecha.groupby(['documento'], dropna=False)[
                    'hora'].min()

                inicios_dia[estado] = [
                    hora2franja(inicios_estado[trabajador])
                    if trabajador in inicios_estado else -1
                    for trabajador in df_optimo.documento.unique()]

                if datetime.strptime(fecha, "%d/%m/%Y").weekday() == 5 and 'Trabaja' in inicios_dia:
                    inicios_dia['Sabado'] = inicios_dia['Trabaja']

            inicios[fecha] = inicios_dia

        return inicios


class modelo(pulp.LpProblem):
    def __init__(self, trabajadores, franjas):
        super().__init__("OptimizacionJornadasLaborales", pulp.LpMinimize)
        self.x = Services.definirVariablesDecision(trabajadores, franjas)

    def agregarAsignacionDiferenciaModelo(self,
                                          trabajadores,
                                          franjas,
                                          demanda_clientes,
                                          diferencias,
                                          x):

        for t in franjas:
            self += diferencias[t] == demanda_clientes[t] - \
                pulp.lpSum(x[(i, t)] for i in trabajadores)

    def agregarFuncionObjetivoModelo(self, diferencias, franjas):

        self += pulp.lpSum(diferencias[t] if (diferencias[t] >= 0) else -diferencias[t]
                           for t in franjas), "Sumatoria de diferencias absolutas"

    def agregarRestriccionFranjasTrabajadasModelo(self,
                                                  trabajadores,
                                                  tipoContrato,
                                                  franjas,
                                                  x,
                                                  tiempoMaxTC,
                                                  tiempoMaxMT):

        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]
            contrato = tipoContrato[indexTrabajador]

            if (contrato == "TC"):
                self += pulp.lpSum(x[(i, t)] for t in franjas) <= tiempoMaxTC
            else:
                self += pulp.lpSum(x[(i, t)] for t in franjas) <= tiempoMaxMT

    def agregarRestriccionFranjaAtendidaTrabajadorModelo(self,
                                                         trabajadores,
                                                         franjas,
                                                         demanda_clientes,
                                                         x):
        for t in franjas:
            if (demanda_clientes[t] >= 1):
                self += pulp.lpSum(x[(i, t)] for i in trabajadores) >= 1

    def agregarRestriccionAlmuerzoContinuoModelo(self,
                                                 trabajadores,
                                                 tipoContrato,
                                                 franjas,
                                                 x,
                                                 iniciosAlmuerzo):

        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]
            contrato = tipoContrato[indexTrabajador]
            franjaInicial = iniciosAlmuerzo[indexTrabajador]

            if (contrato == "TC"):
                # El trabajador TC no puede trabajar durante las 6 franjas del almuerzo
                self += pulp.lpSum(x[(i, t)]
                                   for t in franjas[franjaInicial:franjaInicial+6]) == 0

    def agregarRestriccionTrabajaContinuoAntesDespuesAlmuerzoModelo(self,
                                                                    trabajadores,
                                                                    tipoContrato,
                                                                    franjas,
                                                                    x,
                                                                    iniciosAlmuerzos):

        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]
            contrato = tipoContrato[indexTrabajador]
            franjaInicial = iniciosAlmuerzos[indexTrabajador]

            if (contrato == "TC"):
                # Cada trabajador TC tiene que trabajar 1 hora continua antes y despues de almorzar
                self += pulp.lpSum(x[(i, t)]
                                   for t in franjas[franjaInicial-4:franjaInicial]) == 4
                self += pulp.lpSum(x[(i, t)]
                                   for t in franjas[franjaInicial+6:franjaInicial+10]) == 4

    def agregarRestriccionDuracionJornadaInicial(self,
                                                 trabajadores,
                                                 tipoContrato,
                                                 franjas,
                                                 x,
                                                 diaSemana):

        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]
            contrato = tipoContrato[indexTrabajador]

            duracionjornada = P.DURACIONJORNADATRABAJADOR[contrato]['SEMANA' if diaSemana != 5 else 'SABADO']

            # Restricción intermedia. Un trabajador no tomará descansos ni almuerzo para estimar su hora de entrada
            self += pulp.lpSum(x[(i, t)] for t in franjas) == duracionjornada

            # Cada franja de trabajo, al sumar la jornada completa, debe ser de descanso indicando que ya salió
            for franja in franjas[:len(franjas) - duracionjornada]:
                # Validar si se debe sumar 1 o no
                self += x[(i, franja)] + x[(i, franja + duracionjornada)] <= 1
            for franja in franjas[::-1][:len(franjas) - duracionjornada]:
                # Validar si se debe sumar 1 o no
                self += x[(i, franja)] + x[(i, franja - duracionjornada)] <= 1

    def agregarRestriccionDuracionAlmuerzoInicial(self,
                                                  trabajadores,
                                                  tipoContrato,
                                                  franjas,
                                                  x,
                                                  iniciosJornadas,
                                                  diaSemana):
        if diaSemana == 5:
            return False

        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]

            if (contrato := tipoContrato[indexTrabajador]) == 'MT':
                continue

            duracionjornada = P.DURACIONJORNADATRABAJADOR[contrato]['SEMANA' if diaSemana != 5 else 'SABADO']

            franjaInicial = iniciosJornadas[indexTrabajador]
            franjasTrabajador = franjas[franjaInicial:franjaInicial+duracionjornada]

            # Restricción intermedia. Un trabajador solo tomará como descanso el almuerzo para estimar su hora óptima de almuerzo
            # Durante toda su jornada solo tendrá un descanso de 6 horas
            self += pulp.lpSum(1 - x[(i, t)]
                               for t in franjasTrabajador) == P.BLOQUEALMUERZO
            # Esas 6 horas deben ser continuas.
            for franja in franjasTrabajador[:len(franjasTrabajador) - P.BLOQUEALMUERZO]:
                # Validar si se debe sumar 1 o no
                self += (1 - x[(i, franja)]) + \
                    (1 - x[(i, franja + P.BLOQUEALMUERZO)]) <= 1

    def agregarRestriccionNoTrabajaAntesInicioJornadaModelo(self,
                                                            trabajadores,
                                                            franjas,
                                                            x,
                                                            iniciosJornadas):

        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]
            franjaInicial = iniciosJornadas[indexTrabajador]

            # El trabajador no puede trabajar antes de iniciar de jornada
            self += pulp.lpSum(x[(i, t)]
                               for t in franjas[0:franjaInicial]) == 0

    def agregarRestriccionNoTrabajaDespuesFinalJornadaModelo(self,
                                                             trabajadores,
                                                             tipoContrato,
                                                             franjas,
                                                             x,
                                                             iniciosJornadas,
                                                             tiempoMaxTC,
                                                             tiempoMaxMT):

        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]
            contrato = tipoContrato[indexTrabajador]
            franjaInicial = iniciosJornadas[indexTrabajador]

            # El trabajador no puede trabajar despues de finalizar su jornada
            if (contrato == "TC"):
                # El trabajador TC finaliza su jornada 34 franjas despues de iniciar la jornada (Se suma almuerzo)
                self += pulp.lpSum(x[(i, t)]
                                   for t in franjas[franjaInicial+tiempoMaxTC:len(franjas)]) == 0
            else:
                # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
                self += pulp.lpSum(x[(i, t)]
                                   for t in franjas[franjaInicial+tiempoMaxMT:len(franjas)]) == 0

    def agregarRestriccionTrabajaContinuoExtremosJornadaModelo(self,
                                                               trabajadores,
                                                               tipoContrato,
                                                               franjas,
                                                               x,
                                                               iniciosJornadas,
                                                               tiempoMaxTC,
                                                               tiempoMaxMT):

        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]
            contrato = tipoContrato[indexTrabajador]
            franjaInicial = iniciosJornadas[indexTrabajador]

            # Cada trabajador tiene que trabajar 1 hora continua despues de su jornada inicio
            self += pulp.lpSum(x[(i, t)]
                               for t in franjas[franjaInicial:franjaInicial+4]) == 4

            # Cada trabajador tiene que trabajar 1 hora continua antes de finalizar su jornada
            if (contrato == "TC"):
                # El trabajador TC finaliza su jornada 34 franjas despues de iniciar la jornada (Se suma almuerzo)
                self += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial +
                                                              tiempoMaxTC-4:franjaInicial+tiempoMaxTC]) == 4
            else:
                # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
                self += pulp.lpSum(x[(i, t)] for t in franjas[franjaInicial +
                                                              tiempoMaxMT-4:franjaInicial+tiempoMaxMT]) == 4

    def agregarRestriccionPausasActivasModelo(self,
                                              trabajadores,
                                              tipoContrato,
                                              franjas,
                                              x,
                                              iniciosAlmuerzos,
                                              iniciosJornadas):
        # Se debe sacar 1 pausa activa despues de trabajar minimo 1 hora o maximo 2 horas
        # Eso se traduce a que en cada intervalo de 5 franjas la suma debe dar mayor o igual a 4 (Maximo una pausa activa)
        # Y además, traduce que en cada intervalo de 9 franjas no puede sumar 9 franjas trabajadas

        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]
            contrato = tipoContrato[indexTrabajador]
            franjaInicialJornada = iniciosJornadas[indexTrabajador]
            franjaInicialAlmuerzo = iniciosAlmuerzos[indexTrabajador]

            if (contrato == "TC"):
                # Antes de almorzar
                for franjaEspecifica in range(franjaInicialJornada, franjaInicialAlmuerzo-4):

                    # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                    self += pulp.lpSum(x[(i, t)]
                                       for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                    # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                    self += pulp.lpSum(x[(i, t)]
                                       for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8

                # Despues de almorzar
                # El trabajador TC finaliza su jornada 34 franjas despues de iniciar la jornada
                for franjaEspecifica in range(franjaInicialAlmuerzo+6, franjaInicialJornada+30):

                    # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                    self += pulp.lpSum(x[(i, t)]
                                       for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                    # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                    if (franjaEspecifica <= len(franjas)-9):
                        self += pulp.lpSum(x[(i, t)]
                                           for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8

            else:
                # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
                for franjaEspecifica in range(franjaInicialJornada, franjaInicialJornada+12):

                    # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                    self += pulp.lpSum(x[(i, t)]
                                       for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                    # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                    if (franjaEspecifica <= len(franjas)-9):
                        self += pulp.lpSum(x[(i, t)]
                                           for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8

    def agregarRestriccionPausasActivasSabadoModelo(self,
                                                    trabajadores,
                                                    tipoContrato,
                                                    franjas,
                                                    x,
                                                    iniciosJornadas):
        # Se debe sacar 1 pausa activa despues de trabajar minimo 1 hora o maximo 2 horas
        # Eso se traduce a que en cada intervalo de 5 franjas la suma debe dar mayor o igual a 4 (Maximo una pausa activa)
        # Y además, traduce que en cada intervalo de 9 franjas no puede sumar 9 franjas trabajadas

        for indexTrabajador in range(len(trabajadores)):
            i = trabajadores[indexTrabajador]
            contrato = tipoContrato[indexTrabajador]
            franjaInicialJornada = iniciosJornadas[indexTrabajador]

            if (contrato == "TC"):
                # El trabajador TC finaliza su jornada 20 franjas despues de iniciar la jornada
                for franjaEspecifica in range(franjaInicialJornada, franjaInicialJornada+16):

                    # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                    self += pulp.lpSum(x[(i, t)]
                                       for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                    # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                    if (franjaEspecifica <= len(franjas)-9):
                        self += pulp.lpSum(x[(i, t)]
                                           for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8
            else:
                # El trabajador MT finaliza su jornada 16 franjas despues de iniciar la jornada
                for franjaEspecifica in range(franjaInicialJornada, franjaInicialJornada+12):

                    # Intervalos de 5 deben sumar 4 o 5 franjas trabajadas
                    self += pulp.lpSum(x[(i, t)]
                                       for t in franjas[franjaEspecifica:franjaEspecifica+5]) >= 4

                    # Intervalos de 9 no pueden sumar 9 franjas trabajadas
                    if (franjaEspecifica <= len(franjas)-9):
                        self += pulp.lpSum(x[(i, t)]
                                           for t in franjas[franjaEspecifica:franjaEspecifica+9]) <= 8

    def restriccionesInicios(
            self,
            trabajadores,
            tipoContrato,
            franjas,
            demanda_clientes,
            diaSemana,
            tiempoMaxTC,
            tiempoMaxMT,
            step):

        # Cada franja debe ser atendida por al menos un trabajador (Solo si la demanda es mayor o igual a 1)
        self.agregarRestriccionFranjaAtendidaTrabajadorModelo(
            trabajadores, franjas, demanda_clientes, self.x)

        if step == 'Inicio':
            self.agregarRestriccionDuracionJornadaInicial(trabajadores,
                                                          tipoContrato,
                                                          franjas,
                                                          self.x,
                                                          diaSemana)

    def restriccionesAlmuerzos(
            self,
            trabajadores,
            tipoContrato,
            franjas,
            demanda_clientes,
            iniciosJornadas,
            diaSemana,
            tiempoMaxTC,
            tiempoMaxMT,
            step):

        if step == 'Almuerzos':
            self.agregarRestriccionDuracionAlmuerzoInicial(trabajadores,
                                                           tipoContrato,
                                                           franjas,
                                                           self.x,
                                                           iniciosJornadas,
                                                           diaSemana)

        # Cada trabajador tiene que trabajar unas horas al dia determinadas por el tipo de contrato
        # Pero hay que tener en cuenta que hay pausas activas. Entonces esas franjas son la referencias maximas.
        self.agregarRestriccionFranjasTrabajadasModelo(
            trabajadores, tipoContrato, franjas, self.x, tiempoMaxTC, tiempoMaxMT)

        # Cada trabajador no puede trabajar antes de su jornada inicio
        self.agregarRestriccionNoTrabajaAntesInicioJornadaModelo(
            trabajadores, franjas, self.x, iniciosJornadas)

        # Cada trabajador no puede trabajar despues de su jornada final
        duracionJornada = tiempoMaxTC + 6 if (diaSemana != 5) else tiempoMaxTC
        # En semana hay que tener en cuenta el tiempo del almuerzo para saber la jornada final
        # el sabado no hay almuerzo
        self.agregarRestriccionNoTrabajaDespuesFinalJornadaModelo(
            trabajadores, tipoContrato, franjas, self.x, iniciosJornadas, duracionJornada, tiempoMaxMT)

        # Cada trabajador tiene que trabajar 1 hora continua despues de su jornada inicio y antes de su jornada final (Es decir, trabajar 1 hora continua en los extremos)
        duracionJornada = tiempoMaxTC + 6 if (diaSemana != 5) else tiempoMaxTC
        # En semana hay que tener en cuenta el tiempo del almuerzo para saber la jornada final
        # el sabado no hay almuerzo
        self.agregarRestriccionTrabajaContinuoExtremosJornadaModelo(
            trabajadores, tipoContrato, franjas, self.x, iniciosJornadas, duracionJornada, tiempoMaxMT)

    def restriccionesPausasActivas(
            self,
            trabajadores,
            tipoContrato,
            franjas,
            demanda_clientes,
            iniciosAlmuerzos,
            iniciosJornadas,
            diaSemana):

        # En dia de semana los trabajadores TC sacan almuerzo (No aplica para el sabado)
        if (diaSemana != 5):
            # Cada trabajador TC debe sacar 1h 30 min continua de almuerzo (6 franjas)
            # El bloque del almuerzo corresponde entre las franjas 16 y 29 (Inclusives)
            # Cada trabajador debe iniciar a almorzar entre la franja 16 y 24 (Inclusives)
            self.agregarRestriccionAlmuerzoContinuoModelo(
                trabajadores, tipoContrato, franjas, self.x, iniciosAlmuerzos)

            # Cada trabajador TC tiene que trabajar 1 hora continua antes y despues del almuerzo
            self.agregarRestriccionTrabajaContinuoAntesDespuesAlmuerzoModelo(
                trabajadores, tipoContrato, franjas, self.x, iniciosAlmuerzos)

        # Se debe sacar 1 pausa activa despues de trabajar minimo 1 hora o maximo 2 horas
        if (diaSemana != 5):
            self.agregarRestriccionPausasActivasModelo(
                trabajadores, tipoContrato, franjas, self.x, iniciosAlmuerzos, iniciosJornadas)
        else:
            self.agregarRestriccionPausasActivasSabadoModelo(
                trabajadores, tipoContrato, franjas, self.x, iniciosJornadas)

    def optimizacionHoraInicio(
            self,
            trabajadores,
            tipoContrato,
            franjas,
            demanda_clientes,
            iniciosAlmuerzos,
            iniciosJornadas,
            diaSemana) -> list:
        pass

    def optimizacionAlmuerzos(
            self,
            trabajadores,
            tipoContrato,
            franjas,
            demanda_clientes,
            iniciosAlmuerzos,
            iniciosJornadas,
            diaSemana) -> list:
        pass

    def optimizacionJornadas(
            self,
            trabajadores,
            tipoContrato,
            franjas,
            demanda_clientes,
            iniciosAlmuerzos,
            iniciosJornadas,
            diaSemana,
            step):

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

        # Define una variable intermedia para almacenar las diferencias de cada franja
        diferencias = Services.definirVariableDiferencia(franjas)

        # Agrega a que hace referencia la diferencia
        self.agregarAsignacionDiferenciaModelo(
            trabajadores, franjas, demanda_clientes, diferencias, self.x)

        # Agrega la función objetivo para minimizar las diferencias
        self.agregarFuncionObjetivoModelo(diferencias, franjas)

        # Agrega las restricciones de las variables de decisión

        self.restriccionesInicios(
            trabajadores,
            tipoContrato,
            franjas,
            demanda_clientes,
            diaSemana,
            tiempoMaxTC,
            tiempoMaxMT,
            step
        )

        if step in [None, 'Almuerzos', 'Pausas']:
            self.restriccionesAlmuerzos(
                trabajadores,
                tipoContrato,
                franjas,
                demanda_clientes,
                iniciosJornadas,
                diaSemana,
                tiempoMaxTC,
                tiempoMaxMT,
                step
            )

        if step in [None, 'Pausas']:
            self.restriccionesPausasActivas(
                trabajadores,
                tipoContrato,
                franjas,
                demanda_clientes,
                iniciosAlmuerzos,
                iniciosJornadas,
                diaSemana
            )

        # Resuelve el problema
        solver = pulp.PULP_CBC_CMD(msg=0)
        self.solve(solver)


class Semillas:
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

    def conseguirIniciosJornadasOptimosSucursal(
            suc_cod,
            demanda_df_sucursal,
            trabajadores_df_sucursal,
            iniciosJornadas,
            iniciosAlmuerzos,
            iniciosSabados):

        # Variables globales
        trabajadores = list(trabajadores_df_sucursal.documento)
        tipoContrato = list(trabajadores_df_sucursal.contrato)

        # Valor inicial de la sobredemanda optima e inicios optimos de las jornadas
        sobredemandaOptima = optimizaciónJornadasSucursal(
            suc_cod,
            demanda_df_sucursal,
            trabajadores_df_sucursal,
            iniciosJornadas,
            iniciosAlmuerzos,
            iniciosSabados
        )[0]
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
                    suc_cod,
                    demanda_df_sucursal,
                    trabajadores_df_sucursal,
                    iniciosJornadasActual,
                    iniciosAlmuerzos, iniciosSabados)[0]

                if (sobredemandaActual < sobredemandaOptima):
                    sobredemandaOptima = sobredemandaActual
                    iniciosJornadasOptimo = iniciosJornadasActual.copy()

        return iniciosJornadasOptimo

    def conseguirIniciosAlmuerzosOptimosSucursal(
            suc_cod,
            demanda_df_sucursal,
            trabajadores_df_sucursal,
            iniciosJornadas,
            iniciosAlmuerzos,
            iniciosSabados):

        # Variables globales
        trabajadores = list(trabajadores_df_sucursal.documento)
        tipoContrato = list(trabajadores_df_sucursal.contrato)

        # Valor inicial de la sobredemanda optima e inicios optimos de las jornadas
        sobredemandaOptima = optimizaciónJornadasSucursal(
            suc_cod,
            demanda_df_sucursal,
            trabajadores_df_sucursal,
            iniciosJornadas,
            iniciosAlmuerzos,
            iniciosSabados)[0]
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
                    suc_cod,
                    demanda_df_sucursal,
                    trabajadores_df_sucursal,
                    iniciosJornadas,
                    iniciosAlmuerzosActual,
                    iniciosSabados)[0]

                if (sobredemandaActual < sobredemandaOptima):
                    sobredemandaOptima = sobredemandaActual
                    iniciosAlmuerzosOptimo = iniciosAlmuerzosActual.copy()

        return iniciosAlmuerzosOptimo

    def conseguirIniciosSabadosOptimosSucursal(
            suc_cod,
            demanda_df_sucursal,
            trabajadores_df_sucursal,
            iniciosJornadas,
            iniciosAlmuerzos,
            iniciosSabados):

        # Variables globales
        trabajadores = list(trabajadores_df_sucursal.documento)
        tipoContrato = list(trabajadores_df_sucursal.contrato)

        # Valor inicial de la sobredemanda optima e inicios optimos de las jornadas
        sobredemandaOptima = optimizaciónJornadasSucursal(
            suc_cod,
            demanda_df_sucursal,
            trabajadores_df_sucursal,
            iniciosJornadas,
            iniciosAlmuerzos,
            iniciosSabados)[0]
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
                    suc_cod,
                    demanda_df_sucursal,
                    trabajadores_df_sucursal,
                    iniciosJornadas,
                    iniciosAlmuerzos,
                    iniciosSabadosActual)[0]

                if (sobredemandaActual < sobredemandaOptima):
                    sobredemandaOptima = sobredemandaActual
                    iniciosSabadosOptimo = iniciosSabadosActual.copy()

        return iniciosSabadosOptimo


def optimizaciónJornadasSucursal(
        suc_cod,
        demanda_df_sucursal,
        trabajadores_df_sucursal,
        iniciosJornadas,
        iniciosAlmuerzos,
        iniciosSabados,
        modo=None
):

    # Crea la estructura del dataframe de resultados de la sucursal
    solucionOptimaSucursal_df = pd.DataFrame()
    solucionOptimaSucursal_df = Services.crearDataframeOptimoVacio(
        solucionOptimaSucursal_df)

    # Variables completas
    trabajadores = list(trabajadores_df_sucursal.documento)
    tipoContrato = list(trabajadores_df_sucursal.contrato)

    # Fechas unicas
    fechasUnicas = demanda_df_sucursal.fecha_hora.dt.date.unique()

    # Lista para almacenar los estados de los modelos diarios para evaluarlos luego
    estadosModelosSucursal = []
    df_optimos_fecha = {}

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

        steps = [None] if modo != 'escalonado' else [
            'Inicio', 'Almuerzos', 'Pausas']
        for step in steps:
            # Crea un problema (Modelo) de minimización lineal
            problem = modelo(trabajadores, franjas)

            # Modelo por dia
            problem.optimizacionJornadas(trabajadores,
                                         tipoContrato,
                                         franjas,
                                         demanda_clientes,
                                         iniciosAlmuerzos,
                                         iniciosJornadas,
                                         diaSemana,
                                         step)

            df_optimo_fecha = Services.crear_df_optimo(
                solucionOptimaSucursal_df,
                trabajadores,
                tipoContrato,
                franjas,
                iniciosAlmuerzos,
                fecha_hora,
                suc_cod,
                fecha_actual,
                diaSemana,
                problem.x)

            inicios = Services.Inicios_df_optimo(suc_cod, df_optimo_fecha)

            # df_optimo_fecha.to_csv(
            #     "./resultados/"+str(suc_cod)+fecha_actual.strftime(".%d.%m.%Y")+pulp.LpStatus[problem.status]+step + ".csv")

            if step and 'Trabaja' in inicios[fecha_actual.strftime("%d/%m/%Y")]:
                iniciosJornadas = inicios[fecha_actual.strftime(
                    "%d/%m/%Y")]['Trabaja']
            if step and 'Almuerza' in inicios[fecha_actual.strftime("%d/%m/%Y")]:
                iniciosAlmuerzos = inicios[fecha_actual.strftime(
                    "%d/%m/%Y")]['Almuerza']

        # Guarda el estado del modelo del dia (óptimo, subóptimo, etc.)
        estadosModelosSucursal += [pulp.LpStatus[problem.status]]

        # Guarda los resultados del dia en un dataframe acumulador
        solucionOptimaSucursal_df = Services.guardarResultadoOptimoDia(
            solucionOptimaSucursal_df,
            trabajadores,
            tipoContrato,
            franjas,
            iniciosAlmuerzos,
            fecha_hora,
            suc_cod,
            fecha_actual,
            diaSemana,
            problem.x)

    # Resultado de la sobredemanda de la sucursal
    if (estadosModelosSucursal == ['Optimal']*6):
        sobredemanda = Services.resultadoSobredemanda(
            demanda_df_sucursal, solucionOptimaSucursal_df)
    else:
        sobredemanda = 1000000

    return sobredemanda, solucionOptimaSucursal_df


class Sucursal_pulp:
    def __init__(self, suc_cod, demanda_df, trabajadores_df, modo=None) -> None:
        # DataFrames por sucural
        self.suc_cod = suc_cod
        self.name = "sucursal " + str(suc_cod)
        self._sobredemanda = []
        self.demanda_df_sucursal = demanda_df[(
            demanda_df["suc_cod"] == suc_cod)]
        self.trabajadores_df_sucursal = trabajadores_df[(
            trabajadores_df["suc_cod"] == suc_cod)]
        self.df_optimo = None

        # Variables globales
        self.trabajadores = list(self.trabajadores_df_sucursal.documento)
        self.tipoContrato = list(self.trabajadores_df_sucursal.contrato)

        # Semilla de los inicios de almuerzos, jornadas y sabados (No sigue una razón en particular)
        self.iniciosSemilla = Semillas.crearSemillaIniciosJornadasAlmuerzosSabados(
            self.trabajadores,
            self.tipoContrato)
        self.iniciosJornadas = self.iniciosSemilla[0]
        self.iniciosAlmuerzos = self.iniciosSemilla[1]
        self.iniciosSabados = self.iniciosSemilla[2]

        self.step = {None: self.step_regular,
                     'escalonado': self.step_escalonado
                     }[modo]

    @property
    def sobredemanda(self):
        return self._sobredemanda[-1]

    def iteracion(modo=None):
        if modo:
            return False
        return True

    def step_escalonado(self):

        demanda, df_optimo = optimizaciónJornadasSucursal(
            self.suc_cod,
            self.demanda_df_sucursal,
            self.trabajadores_df_sucursal,
            self.iniciosJornadas,
            self.iniciosAlmuerzos,
            self.iniciosSabados,
            modo='escalonado'
        )

        self.df_optimo = df_optimo

        inicios_solucion = Services.Inicios_df_optimo(
            self.suc_cod, self.df_optimo)
        sobredemanda_min = 10000000

        dias_semana = [dia for dia in inicios_solucion.keys()
                       if datetime.strptime(dia, "%d/%m/%Y").weekday() != 5]
        dias_sabado = [dia for dia in inicios_solucion.keys()
                       if datetime.strptime(dia, "%d/%m/%Y").weekday() == 5]

        if len(dias_sabado) > 1:
            print("Más de un sábado en análisis")

        iniciosSabados = inicios_solucion[dias_sabado[0]]['Sabado']

        for fecha in dias_semana:
            iniciosJornadas = inicios_solucion[fecha]['Trabaja']
            iniciosAlmuerzos = inicios_solucion[fecha]['Almuerza']

            demanda, df_optimo = optimizaciónJornadasSucursal(
                self.suc_cod,
                self.demanda_df_sucursal,
                self.trabajadores_df_sucursal,
                iniciosJornadas,
                iniciosAlmuerzos,
                iniciosSabados
            )

            if sobredemanda_min > demanda:
                sobredemanda_min = demanda
                self.df_optimo = df_optimo

        self._sobredemanda.append(demanda)

    def step_regular(self):
        # Encontrar inicios optimos de jornadas de la sucursal
        self.iniciosJornadas = Semillas.conseguirIniciosJornadasOptimosSucursal(
            self.suc_cod,
            self.demanda_df_sucursal,
            self.trabajadores_df_sucursal,
            self.iniciosJornadas,
            self.iniciosAlmuerzos,
            self.iniciosSabados,
        )

        # Encontrar inicios optimos de almuerzos de la sucursal
        self.iniciosAlmuerzos = Semillas.conseguirIniciosAlmuerzosOptimosSucursal(
            self.suc_cod,
            self.demanda_df_sucursal,
            self.trabajadores_df_sucursal,
            self.iniciosJornadas,
            self.iniciosAlmuerzos,
            self.iniciosSabados
        )

        # Encontrar inicios optimos de la jornada del sabado de la sucursal
        self.iniciosSabados = Semillas.conseguirIniciosSabadosOptimosSucursal(
            self.suc_cod,
            self.demanda_df_sucursal,
            self.trabajadores_df_sucursal,
            self.iniciosJornadas,
            self.iniciosAlmuerzos,
            self.iniciosSabados)

        # Modelo final que optimiza las jornadas laborales por esa sucursal
        demanda, df_optimo = optimizaciónJornadasSucursal(
            self.suc_cod,
            self.demanda_df_sucursal,
            self.trabajadores_df_sucursal,
            self.iniciosJornadas,
            self.iniciosAlmuerzos,
            self.iniciosSabados
        )

        self.df_optimo = df_optimo

        self._sobredemanda.append(demanda)
