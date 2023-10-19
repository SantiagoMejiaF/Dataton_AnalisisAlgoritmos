"""
Supongamos que tienes 8 trabajadores (A, B, C, D, E, F, G, H) y que quieres optimizar sus jornadas laborales en intervalos de 1 hora durante un día de trabajo de 10 horas para satisfacer la demanda de clientes de la sucursal. Cada trabajador puede trabajar hasta 8 horas al día, y la demanda de clientes en cada hora del día se conoce previamente.
"""

"""
Variables de Decisión:
    Para cada trabajador i y cada hora t, definimos una variable binaria xit que representa si el trabajador  i está programado para trabajar en la hora t.
"""

"""
Función Objetivo:
Minimizar el desequilibrio en la demanda de clientes a lo largo del día. Podemos expresar esto como la suma de las diferencias entre la demanda de clientes y el número de trabajadores asignados en cada hora:

    Minimizar Z= t=1..10∑ | Demanda[t] - i=1..8∑ xit |
"""

"""
Restricciones:
    - Cada trabajador tiene que trabajar exactamente 8 horas al día:
        t=1..10∑xit == 8 para i ∈ {A,B,C,D,E,F,G,H}

    - Cada hora debe ser atendida por al menos un trabajador:
        i=1..8∑ xit >= 1 para t ∈ {1,2,…,10}

    - Las variables xit son binarias.
"""

import pulp

# Demanda de clientes por hora (ejemplo)
demanda_clientes = [10, 8, 15, 12, 14, 11, 9, 10, 7, 5]

# Crea un problema de minimización lineal
problem = pulp.LpProblem("OptimizacionJornadasLaborales", pulp.LpMinimize)

# Define las variables de decisión
trabajadores = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
horas = list(range(1, 11))  # De 1 a 10 horas de trabajo
x = pulp.LpVariable.dicts('asignado', [(i, t) for i in trabajadores for t in horas], 0, 1, pulp.LpBinary)

"""
No es necesario poner el 0 y 1 porque ya se define que las variables son binarias, pero aun así la explicación de que significan:
0 es el valor mínimo que puede tomar una variable y 1 es el valor máximo que puede tomar una variable
"""

# Define las variables para representar las diferencias
diferencias = pulp.LpVariable.dicts('diferencia', horas, 0, None)

"""
Un valor de None en el límite superior (valor máximo) de una variable significa que la variable no tiene un límite superior específico

En este caso particular, la variable diferencias se utiliza para medir las diferencias entre la demanda de clientes y la asignación de trabajadores en cada hora. Al definir el límite superior de None, estás permitiendo que esta variable pueda tomar valores no restringidos, lo que es adecuado para modelar las diferencias entre la demanda y la asignación sin imponer un límite superior específico en esas diferencias.
"""

# Agrega las restricciones de las diferencias
for t in horas:
    problem += diferencias[t] >= pulp.lpSum(x[(i, t)] for i in trabajadores) - demanda_clientes[t - 1]
    problem += diferencias[t] >= demanda_clientes[t - 1] - pulp.lpSum(x[(i, t)] for i in trabajadores)

"""
Por que pones el valor positivo y negativo de la resta, es necesario? o se puede poner el valor absolutlo?

La razón detrás de agregar tanto la resta positiva como negativa de las diferencias se relaciona con la forma en que se modela el problema de optimización. En este contexto, estás tratando de medir la diferencia entre la demanda de clientes y la asignación de trabajadores en cada hora, y esta diferencia puede ser tanto positiva como negativa.

Agregar ambas restricciones (una para la diferencia positiva y otra para la diferencia negativa) es necesario para modelar de manera efectiva este problema de optimización. Permite que el valor de la variable diferencias sea el valor absoluto de la diferencia entre la demanda y la asignación en cada hora.

Si solo agregaras el valor absoluto, estarías limitando la variable diferencias a ser siempre no negativa, lo que no reflejaría adecuadamente la diferencia real entre la demanda y la asignación. Al agregar ambas restricciones, permites que la variable diferencias pueda ser positiva cuando la demanda es mayor que la asignación y negativa cuando la demanda es menor que la asignación, lo que es consistente con el objetivo de medir las diferencias en ambas direcciones.
"""


# Define la función objetivo para minimizar las diferencias
problem += pulp.lpSum(diferencias[t] for t in horas)

# Restricciones
for i in trabajadores:
    problem += pulp.lpSum(x[(i, t)] for t in horas) == 8
for t in horas:
    problem += pulp.lpSum(x[(i, t)] for i in trabajadores) >= 1

# Resuelve el problema
problem.solve()

# Imprime el estado del problema (óptimo, subóptimo, etc.)
print("Estado:", pulp.LpStatus[problem.status])

# Imprime la asignación óptima de horarios
print("Asignación Óptima de Horarios:")
for i in trabajadores:
    for t in horas:
        if pulp.value(x[(i, t)]) == 1:
            print(f"Trabajador {i} trabaja en la hora {t}")

# Imprime el valor optimo de la diferencia
print("Valor optimo de la Diferencia:", pulp.value(problem.objective))