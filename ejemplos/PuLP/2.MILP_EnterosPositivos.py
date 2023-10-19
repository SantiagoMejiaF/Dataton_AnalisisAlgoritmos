"""
Aquí tienes un ejemplo sencillo de un problema de programación lineal entera mixta (MILP) con PuLP que tiene una unica solucion óptima:

    Maximizar Z=3x+2y

    Restricciones: 
        2x + y <= 5
        x + 2y <= 6
        x,y >= 0
        x,y son enteros

"""
import pulp

# Crea un problema de maximización
problema = pulp.LpProblem("MiEjemploDeOptimizacion", pulp.LpMaximize)

# Define las variables de decisión
x = pulp.LpVariable("x", lowBound=0, cat=pulp.LpInteger)
y = pulp.LpVariable("y", lowBound=0, cat=pulp.LpInteger)

"""
cat=pulp.LpInteger se utiliza para indicar que una variable debe tomar valores enteros en lugar de valores continuos, y esto es especialmente relevante en problemas MILP.
"""

# Define la función objetivo
problema += 3 * x + 2 * y, "FuncionObjetivo"

# Define las restricciones
problema += 2 * x + y <= 5
problema += x + 2 * y <= 6

# Resuelve el problema
problema.solve()

# Muestra el resultado
print("Estado:", pulp.LpStatus[problema.status])
print("x =", x.varValue)
print("y =", y.varValue)
print("Valor óptimo de la función objetivo:", pulp.value(problema.objective))

"""
La solución óptima que obtendrás puede ser (x=2, y=1), que maximiza la función objetivo Z=3x+2y
"""