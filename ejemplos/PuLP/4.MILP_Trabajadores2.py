"""
Supongamos que tienes tres trabajadores (A, B y C) y tres tareas (W, Y y Z) que deben completarse. Cada trabajador tiene una tarifa por hora y cada tarea requiere cierta cantidad de tiempo para completarse. Queremos asignar trabajadores a tareas de manera que se minimicen los costos totales, y hay restricciones que deben cumplirse:

Los trabajadores solo pueden estar asignados a una tarea a la vez.
Cada tarea debe ser completada por un solo trabajador.
Cada trabajador tiene un límite en la cantidad de horas que puede trabajar en un día.
"""

"""
Variables de decisión:
    xIJ : Representa si el trabajador I está asignado a la tarea J. Es una variable binaria que toma el valor 1 si el trabajador I está asignado a la tarea J, y 0 en caso contrario.
"""

"""
Función objetivo:
Minimizar el costo total, que se calcula como la suma de las tarifas por hora de los trabajadores multiplicadas por el tiempo que dedican a cada tarea asignada.
    Minimizar Z=5xAW +7xAY +6xAZ +6xBW +8xBY +7xBZ +4xCW +5xCY +6xCZ

"""

"""
Restricciones:
    - Cada tarea debe ser completada por exactamente un trabajador:
        xAW + xBW + xCW = 1 (Para la tarea W)
        xAY + xBY + xCY = 1 (Para la tarea Y)
        xAZ + xBZ + xCZ = 1 (Para la tarea Z)

    - Cada trabajador no puede estar asignado a más de una tarea a la vez:
        xAW + xAY + xAZ <= 1 (Para el trabajador A)
        xBW + xBY + xBZ <= 1 (Para el trabajador B)
        xCW + xCY + xCZ <= 1 (Para el trabajador C)

    - Restricciones de límite de horas de trabajo para cada trabajador
"""

import pulp

# Crea un problema de minimización lineal
problem = pulp.LpProblem("AsignacionTrabajadores", pulp.LpMinimize)

# Definir variables de decisión binarias
trabajadores = ['A', 'B', 'C']
tareas = ['W', 'Y', 'Z']
x = pulp.LpVariable.dicts('asignado', [(i, j) for i in trabajadores for j in tareas], 0, 1, pulp.LpBinary)

# Definir la función objetivo
costos = {
    ('A', 'W'): 5, ('A', 'Y'): 7, ('A', 'Z'): 6,
    ('B', 'W'): 6, ('B', 'Y'): 8, ('B', 'Z'): 7,
    ('C', 'W'): 4, ('C', 'Y'): 5, ('C', 'Z'): 6,
}

problem += pulp.lpSum(costos[(i, j)] * x[(i, j)] for i in trabajadores for j in tareas), "Costo_Total"

# Restricciones de que cada tarea debe ser completada por exactamente un trabajador
for j in tareas:
    problem += pulp.lpSum(x[(i, j)] for i in trabajadores) == 1, f"Restriccion_Tarea_{j}"

# Restricciones de que cada trabajador no puede estar asignado a más de una tarea a la vez
for i in trabajadores:
    problem += pulp.lpSum(x[(i, j)] for j in tareas) <= 1, f"Restriccion_Trabajador_{i}"

# Resuelve el problema
problem.solve()

# Imprime el estado del problema (óptimo, subóptimo, etc.)
print("Estado:", pulp.LpStatus[problem.status])

# Imprime la asignación óptima de trabajadores a tareas
print("Asignación Óptima:")
for i in trabajadores:
    for j in tareas:
        if pulp.value(x[(i, j)]) == 1:
            print(f"Trabajador {i} está asignado a la tarea {j}")

# Imprime el costo total óptimo
print("Costo Total Óptimo:", pulp.value(problem.objective))
