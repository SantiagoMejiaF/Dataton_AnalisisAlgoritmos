from ejemplos.test_Restricciones_v010 import test_Restricciones_v01
from src.PuLP.Etapa2.Modelo_PuLP import ejecutar_modelo as modelo_pulp


def main(optimizacion):
    optimizacion()


if __name__ == "__main__":
    main(modelo_pulp)
    # test_Restricciones_v01()
