import pulp
import pandas as pd

dataton2023 = 'Dataton2023_Etapa1.xlsx'

demanda_df = pd.read_excel(dataton2023, sheet_name='demand')
trabajadores_df = pd.read_excel(dataton2023, sheet_name='workers')

# Demanda de clientes por cada 15 min
demanda_clientes = list(demanda_df.demanda)

# Crea un problema de minimización lineal
problem = pulp.LpProblem("OptimizacionJornadasLaborales", pulp.LpMinimize)

# Define las variables de decisión
trabajadores = list(trabajadores_df.documento)

franjas = list(range(0, len(demanda_clientes)))  # De 0 (7:30am) hasta la ultima demanda registrada (de 0-45)

x = pulp.LpVariable.dicts('asignado', [(i, t) for i in trabajadores for t in franjas], 0, 1, pulp.LpBinary)

# Define un diccionario para almacenar las diferencias de cada franja
diferencias = pulp.LpVariable.dicts('diferencia', franjas, 0, None)

# Agrega las restricciones de las diferencias
## Permite que el valor de la variable diferencias sea el valor absoluto de la diferencia entre la demanda y la asignación en cada hora.
for t in franjas:
    problem += diferencias[t] >= pulp.lpSum(x[(i, t)] for i in trabajadores) - demanda_clientes[t]
    problem += diferencias[t] >= demanda_clientes[t] - pulp.lpSum(x[(i, t)] for i in trabajadores)

"""
La razón detrás de agregar tanto la resta positiva como negativa de las diferencias se relaciona con la forma en que se modela el problema de optimización. En este contexto, estás tratando de medir la diferencia entre la demanda de clientes y la asignación de trabajadores en cada hora, y esta diferencia puede ser tanto positiva como negativa.

Agregar ambas restricciones (una para la diferencia positiva y otra para la diferencia negativa) es necesario para modelar de manera efectiva este problema de optimización. Permite que el valor de la variable diferencias sea el valor absoluto de la diferencia entre la demanda y la asignación en cada hora.
"""

# Define la función objetivo para minimizar las diferencias
problem += pulp.lpSum(diferencias[t] for t in franjas)

# Restricciones

## Cada trabajador tiene que trabajar 8 horas al dia
## (Sin son flanjas de 15 min entonces 8 horas son 32 flanjas al dia)
## Pero hay que tener en cuenta que hay pausas activas. En general un trabajador puede sacar entre 2-6 pausas activas dependiendo de como las saca.
## Entonces solo tiene que trabajar minimo 26 flanjas y maximo 30 flanjas 
for i in trabajadores:
    problem += pulp.lpSum(x[(i, t)] for t in franjas) >= 26
    problem += pulp.lpSum(x[(i, t)] for t in franjas) <= 30

## Cada flanja debe ser atendida por al menos un trabajador
for t in franjas:
    problem += pulp.lpSum(x[(i, t)] for i in trabajadores) >= 1

## Cada trabajador debe sacar 1.5h de almuerzo al dia
## El almurzo debe ser entre 11:30 (Flanja 16) y maximo hasta las 15:00 (Flanja 30 no inclusive)
## entonces entre esas 14 flanjas debe descansar 6 flanjas para el almurzo, 
## además entre ese tiempo solo es posible sacar maximo 1 pausa activa
## En conlusión, en esa bloque de 14 flanjas se debe trabajar entre 7 y 8 flanjas
for i in trabajadores:
    problem += pulp.lpSum(x[(i, t)] for t in franjas[16:30]) >= 7
    problem += pulp.lpSum(x[(i, t)] for t in franjas[16:30]) <= 8

# Resuelve el problema
problem.solve()

# Imprime el estado del problema (óptimo, subóptimo, etc.)
print("Estado:", pulp.LpStatus[problem.status])

# Imprime el valor optimo de la diferencia
print("Valor optimo de la Diferencia:", pulp.value(problem.objective))

# Guarda la asignación óptima de horarios en un excel
fecha_hora = list(demanda_df.fecha_hora)
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

solucionOptima.to_excel("solucionOptima.xlsx", index=False)

print("Asignación Óptima de Horarios realizada")

