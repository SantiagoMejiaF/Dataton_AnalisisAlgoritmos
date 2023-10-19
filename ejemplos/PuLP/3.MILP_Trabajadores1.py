"""
Aquí tienes un ejemplo de un problema de programación lineal entera mixta (MILP) que tiene una unica solucion óptima con PuLP
"""

"""
Supongamos que deseas asignar trabajadores a proyectos de manera que maximices la productividad total de la empresa. Cada trabajador puede ser asignado a uno o más proyectos, y se deben cumplir ciertas restricciones.
"""

import pulp

# Crea un problema de maximización
problema = pulp.LpProblem("AsignacionDeTrabajadores", pulp.LpMaximize)

# Definir variables binarias (0 o 1) para asignar trabajadores a proyectos
trabajadores = ["Trabajador1", "Trabajador2", "Trabajador3"]
proyectos = ["ProyectoA", "ProyectoB", "ProyectoC"]

asignacion = pulp.LpVariable.dicts("Asignacion", 
                                   [(trabajador, proyecto) for trabajador in trabajadores for proyecto in proyectos],
                                   cat=pulp.LpBinary)


"""
pulp.LpVariable.dicts() es una función proporcionada por la biblioteca PuLP en Python que te permite crear un diccionario de variables de decisión de manera más conveniente y eficiente. 

El método pulp.LpVariable.dicts() toma como argumentos los nombres de las variables y sus categorías (por ejemplo, binarias, enteras o continuas) y devuelve un diccionario donde las claves son las combinaciones de nombres que proporcionas y los valores son las variables de decisión correspondientes. 
"""

"""
cat=pulp.LpBinary se utiliza para indicar que una variable en PuLP debe ser binaria, tomando solo los valores 0 o 1, lo que es apropiado para modelar decisiones discretas en problemas de optimización.

Este tipo de variable es útil en problemas de optimización donde las decisiones son binarias o categóricas, como asignación de recursos, programación de horarios, diseño de redes y muchos otros casos en los que deseas modelar opciones que son exclusivas o excluyentes.
"""


# Definir la función objetivo
productividad = {("Trabajador1", "ProyectoA"): 5, ("Trabajador2", "ProyectoA"): 4, ("Trabajador3", "ProyectoA"): 3,
                 ("Trabajador1", "ProyectoB"): 3, ("Trabajador2", "ProyectoB"): 6, ("Trabajador3", "ProyectoB"): 2,
                 ("Trabajador1", "ProyectoC"): 1, ("Trabajador2", "ProyectoC"): 2, ("Trabajador3", "ProyectoC"): 4}

problema += pulp.lpSum(asignacion[(trabajador, proyecto)] * productividad[(trabajador, proyecto)]
                      for trabajador in trabajadores for proyecto in proyectos), "ProductividadTotal"

"""
pulp.lpSum es una función proporcionada por la biblioteca PuLP en Python que se utiliza para calcular la suma de un conjunto de términos en una expresión lineal. 
"""

# Restricciones
# Restricción de que cada trabajador puede ser asignado a un máximo de 2 proyectos
for trabajador in trabajadores:
    problema += pulp.lpSum(asignacion[(trabajador, proyecto)] for proyecto in proyectos) <= 2

# Restricción de que cada proyecto debe tener al menos un trabajador asignado
for proyecto in proyectos:
    problema += pulp.lpSum(asignacion[(trabajador, proyecto)] for trabajador in trabajadores) >= 1

# Resuelve el problema
problema.solve()

# Muestra el resultado
print("Estado:", pulp.LpStatus[problema.status])
print("Asignaciones óptimas:")
for trabajador in trabajadores:
    for proyecto in proyectos:
        if asignacion[(trabajador, proyecto)].varValue == 1:
            print(f"Asignar {trabajador} a {proyecto}")

print("Valor óptimo de la función objetivo (productividad total):", pulp.value(problema.objective))
