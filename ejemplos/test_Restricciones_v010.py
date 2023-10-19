import numpy as np
import pandas as pd

if __name__ == "__main__":
    import os
    os.chdir('..')


def test_Restricciones_v01():

    # --------- Estados -----------
    N = 0  # No Trabaja
    T = 1  # Trabajo
    P = 2  # Pausa Activa
    A = 3  # Almuerzo

    from src.Restricciones_v01 import Trabajador

    def generarTrabajador():  # Función de Prueba generador de rangos al azar
        return list(np.random.randint(0, 4, 46))

    # Trabajador Ejemplo debe tener longitúd de 46 correspondientes a todas las franjas posibles
    T1 = [N, N, N, T, T, T, T, P, T, T, T, T, T, T, T, A, A, A, A, A]

    # El objeto trabajador guarda su horario en lista y en bloques
    # Trabajador Ejemplo de bloques con el que se validan algunas restricciones
    T1 = [
        [N, 3],
        [T, 4],
        [P, 1],
        [T, 7],
        [A, 6]
    ]

    # Trabajador con rango válido según las resitrcciones
    print(Trabajador(
        [T]*8+[P]+[T]*8+[A]*6+[T] * 8+[P]+[T]*6+[N]*8
    ).rangoValido())

    # Prueba enviando datos aleatorios
    from src.Parametros import Parametros as Par
    sucursal = [Trabajador(generarTrabajador())
                for i in range(Par.CANTIDADEMPLEADOS)]

    for trabajador in sucursal:
        print(trabajador.rangoValido())

    input("-- Press any key to close --")


if __name__ == "__main__":
    test_Restricciones_v01()
