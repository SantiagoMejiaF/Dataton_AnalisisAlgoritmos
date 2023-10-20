def definirVariablesDecision(trabajadores, franjas):
    x = pulp.LpVariable.dicts('Duplas binarias', [(i, t) for i in trabajadores for t in franjas], 0, 1, pulp.LpBinary)
    return x


def definirDiccionariosDiferencia(franjas):
    diferencias = pulp.LpVariable.dicts('diferencia', franjas, 0, None)
    return diferencias


def agregarRestriccionesDiferenciaModelo(trabajadores, franjas, demanda_clientes, diferencias, x):
    ## Permite que el valor de la variable diferencias sea el valor absoluto de la diferencia entre la demanda y la asignación en cada hora.

    """
    La razón detrás de agregar tanto la resta positiva como negativa de las diferencias se relaciona con la forma en que se modela el problema de optimización. En este contexto, estás tratando de medir la diferencia entre la demanda de clientes y la asignación de trabajadores en cada hora, y esta diferencia puede ser tanto positiva como negativa.

    Agregar ambas restricciones (una para la diferencia positiva y otra para la diferencia negativa) es necesario para modelar de manera efectiva este problema de optimización. Permite que el valor de la variable diferencias sea el valor absoluto de la diferencia entre la demanda y la asignación en cada hora.
    """

    global problem
    global franjasTotales

    
    for t in franjas:
        if (len(franjas) != franjasTotales):
            t = t-16
        problem += diferencias[t] >= pulp.lpSum(x[(i, t)] for i in trabajadores) - demanda_clientes[t]
        problem += diferencias[t] >= demanda_clientes[t] - pulp.lpSum(x[(i, t)] for i in trabajadores)
        


def agregarFuncionObjetivoModelo(diferencias,franjas):
    global problem
    problem += pulp.lpSum(diferencias[t] for t in franjas)


def agregarRestriccionfranjasTrabajadasModelo(trabajadores, franjas, x, numMinimo, numMaximo):
    global problem
    for i in trabajadores:
        problem += pulp.lpSum(x[(i, t)] for t in franjas) >= numMinimo
        problem += pulp.lpSum(x[(i, t)] for t in franjas) <= numMaximo


def agregarRestriccionFranjaAtendidaTrabajadorModelo(trabajadores, franjas, x):
    global problem
    for t in franjas:
        problem += pulp.lpSum(x[(i, t)] for i in trabajadores) >= 1


def agregarRestriccionAlmuerzoModelo(trabajadores, franjas, x):
    ## El almurzo debe ser entre 11:30 (Flanja 16) y maximo hasta las 15:00 (Flanja 30 no inclusive)
    ## entonces entre esas 14 franjas debe descansar 6 franjas para el almuerzo, 
    ## además entre ese tiempo solo es posible sacar maximo 1 pausa activa
    ## En conlusión, en esa bloque de 14 franjas se debe trabajar entre 7 y 8 franjas

    global problem
    for i in trabajadores:
        problem += pulp.lpSum(x[(i, t)] for t in franjas[16:30]) >= 7
        problem += pulp.lpSum(x[(i, t)] for t in franjas[16:30]) <= 8


def agregarRestriccionAlmuerzoContinuoModelo(trabajadores, franjas, x, iniciosAlmuerzo):
    global problem

    for indexTrabajador in range(len(trabajadores)):
        # Diferente a -1 es porque se sabe cuando inicia a almorzar ese trabajador
        # En caso contrario, no se sabe
        flanjaInicial = iniciosAlmuerzo[indexTrabajador]
        if (flanjaInicial != -1):
            # El trabajador no puede trabajar durante las 6 franjas del almuerzo
            problem += pulp.lpSum(x[(trabajadores[indexTrabajador], t)] for t in franjas[flanjaInicial:flanjaInicial+6]) == 0




def crearExcelConResultadosOptimos(trabajadores, franjas, x):
    global fecha_hora

    horas = [str(i).split()[1] for i in fecha_hora]

    documentoOptimo = []
    estadoOptimo = []
    horaOptimo = []
    franjaOptimo = []

    for t in franjas:
        for i in trabajadores:
            documentoOptimo += [i]
            
            if pulp.value(x[(i, t)]) == 1:
                estadoOptimo += ["Trabaja"]
            else:
                estadoOptimo += ["Nada"]
            
            horaOptimo += [horas[t]]
            franjaOptimo += [t+30]
                
    suc_codeOptimo = [60]*(len(franjas)*len(trabajadores))
    fechaOptimo = [str(fecha_hora[0]).split()[0]]*(len(franjas)*len(trabajadores))


    data = {'suc_code': suc_codeOptimo, 'documento': documentoOptimo, 'fecha': fechaOptimo, 'hora': horaOptimo, 'estado': estadoOptimo, 'hora_franja': franjaOptimo}
    solucionOptima = pd.DataFrame(data)
    solucionOptima = solucionOptima.sort_values(by=['documento','hora_franja'])

    solucionOptima.to_excel("./src/PuLP/solucionOptima.xlsx", index=False)

    print("Asignación Óptima de Horarios realizada")


def optimizacionJornadas(trabajadores, franjas, demanda_clientes, iniciosAlmuerzos):
    global problem
    global franjasTotales
    global final

    # Crea un problema (Modelo) de minimización lineal
    problem = pulp.LpProblem("OptimizacionIniciosAlmuerzo", pulp.LpMinimize)

    # Define las variables de decisión
    x = definirVariablesDecision(trabajadores, franjas)

    # Define un diccionario para almacenar las diferencias de cada franja
    diferencias = definirDiccionariosDiferencia(franjas)

    # Agrega las restricciones de las diferencias
    agregarRestriccionesDiferenciaModelo(trabajadores, franjas, demanda_clientes, diferencias, x)

    # Agrega la función objetivo para minimizar las diferencias
    agregarFuncionObjetivoModelo(diferencias, franjas)

    # Agrega las restricciones de las variables de decisión

    #El código de optimización se puede reutilizar para tramos de franjas, entonces solo aplicar esta restricción cuando se renga todas las franjas
    if (len(franjas) == franjasTotales):
        ## Cada trabajador tiene que trabajar 8 horas al dia
        ## (Sin son franjas de 15 min entonces 8 horas son 32 franjas al dia)
        ## Pero hay que tener en cuenta que hay pausas activas. En general un trabajador puede sacar entre 2-6 pausas activas dependiendo de como las saca.
        ## Entonces solo tiene que trabajar minimo 26 franjas y maximo 30 franjas 
        agregarRestriccionfranjasTrabajadasModelo(trabajadores, franjas, x, 26, 30)

    ## Cada flanja debe ser atendida por al menos un trabajador
    agregarRestriccionFranjaAtendidaTrabajadorModelo(trabajadores, franjas, x)

    ## Cada trabajador debe sacar 1h 30 min continua de almuerzo (6 franjas)
    ## El bloque del almuerzo corresponde entre las franjas 16 y 29 (Inclusives)
    ## Cada trabajador debe iniciar a almorzar entre la flanja 16 y 24 (Inclusives)
    agregarRestriccionAlmuerzoContinuoModelo(trabajadores, franjas, x, iniciosAlmuerzos)

    # Resuelve el problema
    problem.solve()

    # Imprime el estado del problema (óptimo, subóptimo, etc.)
    print("Estado:", pulp.LpStatus[problem.status])

    # Imprime el valor optimo de la diferencia
    print("Valor optimo de la Diferencia:", pulp.value(problem.objective))

    # Guarda la asignación óptima de horarios en un excel
    ## Solo si es el modelo final
    if (final):
        crearExcelConResultadosOptimos(trabajadores, franjas, x)


def encontrarIniciosAlmuerzoOptimos(trabajadores, franjas, demanda_clientes):
    # El objetivo es encontrar los inicios de almuerzos:
    # El bloque del almuerzo corresponde entre las franjas 16 y 29 (Inclusives)

    global problem

    # -1 corresponde a que aun no se sabe cual es la flanja inicial de almuerzo de cada cliente
    iniciosAlmuerzos = [-1,-1,-1,-1,-1,-1,-1,-1]


    # Encuentra la flanja inicial de cada trabajador
    for indexTrabajador in range(len(trabajadores)):
        valoresOptimos = []
        franjasOptimas = []

        # cada trabajador debe iniciar a almorzar entre la flanja 16 y 24 (Inclusives)
        for flanjaInicial in range(16,25):

            iniciosAlmuerzos[indexTrabajador] = flanjaInicial
            optimizacionJornadas(trabajadores, franjas, demanda_clientes, iniciosAlmuerzos)

            if (pulp.LpStatus[problem.status] == "Optimal"):
                valoresOptimos += [pulp.value(problem.objective)]
                franjasOptimas += [flanjaInicial]
        
        maxValorOptimo = max(valoresOptimos)
        indiceMaxOptimo = valoresOptimos.index(maxValorOptimo) #Primera Ocurrencia
        flanjaOptimaTrabajador = franjasOptimas[indiceMaxOptimo]

        iniciosAlmuerzos[indexTrabajador] = flanjaOptimaTrabajador


    return iniciosAlmuerzos


#Inicio del Main

import pulp
import pandas as pd

# Extración de datos del excel
dataton2023 = './src/PuLP/Dataton2023_Etapa1.xlsx'

demanda_df = pd.read_excel(dataton2023, sheet_name='demand')
trabajadores_df = pd.read_excel(dataton2023, sheet_name='workers')

# Variables completas
fecha_hora = list(demanda_df.fecha_hora)
demanda_clientes = list(demanda_df.demanda)
trabajadores = list(trabajadores_df.documento)
franjas = list(range(0, len(demanda_clientes)))  # De 0 (7:30am) hasta la ultima demanda registrada (de 0-45)
franjasTotales = len(franjas)

# Encuentra las franjas iniciales del almuerzo de cada trabajador
final = False
problem = pulp.LpProblem("OptimizacionIniciosAlmuerzo", pulp.LpMinimize)
iniciosAlmuerzos = encontrarIniciosAlmuerzoOptimos(trabajadores, franjas, demanda_clientes)

## Modelo final
final = True
optimizacionJornadas(trabajadores, franjas, demanda_clientes, iniciosAlmuerzos)

"""
# Crea un problema (Modelo) de minimización lineal
problem = pulp.LpProblem("OptimizacionJornadasLaborales", pulp.LpMinimize)

# Define las variables de decisión
x = definirVariablesDecision(trabajadores, franjas)

# Define un diccionario para almacenar las diferencias de cada franja
diferencias = definirDiccionariosDiferencia(franjas)

# Agrega las restricciones de las diferencias
agregarRestriccionesDiferenciaModelo(trabajadores, franjas, demanda_clientes, diferencias, x)

# Agrega la función objetivo para minimizar las diferencias
agregarFuncionObjetivoModelo(diferencias,franjas)

# Agrega las restricciones de las variables de decisión

## Cada trabajador tiene que trabajar 8 horas al dia
## (Sin son franjas de 15 min entonces 8 horas son 32 franjas al dia)
## Pero hay que tener en cuenta que hay pausas activas. En general un trabajador puede sacar entre 2-6 pausas activas dependiendo de como las saca.
## Entonces solo tiene que trabajar minimo 26 franjas y maximo 30 franjas 
agregarRestriccionfranjasTrabajadasModelo(trabajadores, franjas, x, 26, 30)

## Cada franja debe ser atendida por al menos un trabajador
agregarRestriccionFranjaAtendidaTrabajadorModelo(trabajadores, franjas, x)

## Cada trabajador debe sacar 1.5h de almuerzo al dia
agregarRestriccionAlmuerzoModelo(trabajadores, franjas, x)

# Resuelve el problema
problem.solve()

# Imprime el estado del problema (óptimo, subóptimo, etc.)
print("Estado:", pulp.LpStatus[problem.status])

# Imprime el valor optimo de la diferencia
print("Valor optimo de la Diferencia:", pulp.value(problem.objective))

# Guarda la asignación óptima de horarios en un excel
fecha_hora = list(demanda_df.fecha_hora)
crearExcelConResultadosOptimos(trabajadores, franjas, x, fecha_hora)
"""

print(iniciosAlmuerzos)