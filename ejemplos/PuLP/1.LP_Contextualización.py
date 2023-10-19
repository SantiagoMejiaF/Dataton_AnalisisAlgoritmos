"""
La librería PuLP en Python es una herramienta de optimización que se utiliza para resolver problemas de programación lineal (LP) y programación lineal entera mixta (MILP).

Algunas de las aplicaciones comunes de PuLP incluyen:
    Planificación de la producción.
    Optimización de la cadena de suministro.
    Diseño de redes.
    Optimización financiera.
    Planificación de la mano de obra.
    Diseño de rutas y horarios de personal.
"""

"""
Supongamos que deseas minimizar los costos de producción de ciertos productos sujetos a restricciones de recursos. En este caso, se utilizará un problema de mezcla de productos como ejemplo.
"""

import pulp

# Crea un problema de minimización
problema = pulp.LpProblem("MiEjemploDeOptimizacion", pulp.LpMinimize)

# Define las variables de decisión

x1 = pulp.LpVariable("Producto1", lowBound=0)  # Cantidad de Producto 1
x2 = pulp.LpVariable("Producto2", lowBound=0)  # Cantidad de Producto 2

"""
En algunos problemas de optimización, las variables pueden tener restricciones en su rango de valores válidos. Estas restricciones pueden ser en forma de límites inferiores (como lowBound en este caso), límites superiores (upBound), o incluso restricciones generales que definen un rango permitido para la variable. Estas restricciones ayudan a modelar de manera efectiva el comportamiento de las variables en el problema.
"""


# Define la función objetivo (minimizar los costos)
problema += 10 * x1 + 15 * x2, "CostoTotal"

"""
La coma en esta línea separa la expresión matemática de la función objetivo, que está compuesta por términos lineales (coeficientes y variables), del nombre descriptivo que se le da a la función objetivo. La función objetivo puede tener un nombre o etiqueta que te ayude a identificar su propósito o significado en el contexto del problema.

    problema += coeficiente1 * variable1 + coeficiente2 * variable2, "Nombre de la Función Objetivo"
    
"""

# Define las restricciones
problema += 2 * x1 + 3 * x2 >= 20  # Restricción de recursos
problema += x1 + 2 * x2 >= 10    # Restricción de recursos


# Resuelve el problema
problema.solve()

# Muestra el resultado
print("--------------------------------------------")
print("Estado:", pulp.LpStatus[problema.status])
print("Cantidad de Producto 1:", x1.varValue)
print("Cantidad de Producto 2:", x2.varValue)
print("Costo mínimo:", pulp.value(problema.objective))

"""
Los posibles estados que puede tomar problema.status y sus correspondientes descripciones son los siguientes:

    - pulp.LpStatusNotSolved: El problema no se ha resuelto.
    - pulp.LpStatusOptimal: Se encontró una solución óptima para el problema.
    - pulp.LpStatusInfeasible: El problema es infactible, lo que significa que no existe ninguna solución factible que satisfaga todas las restricciones.
    - pulp.LpStatusUnbounded: El problema es ilimitado, lo que significa que no existe un límite superior en la función objetivo y es posible aumentar o disminuir el valor de la función objetivo infinitamente.
    - pulp.LpStatusUndefined: El estado del problema no se ha definido, lo que podría deberse a errores en la formulación del problema o problemas con el solucionador.
"""

"""
Es posible que un problema tenga diferentes resultados optimos para la función objetivo?

    En teoría, es posible que un problema de optimización tenga múltiples soluciones óptimas para la función objetivo, pero esto depende del tipo de problema y de las restricciones involucradas. La posibilidad de tener múltiples soluciones óptimas se presenta principalmente en problemas de programación lineal entera mixta (MILP) y en algunos problemas de programación lineal continua (LP).
"""