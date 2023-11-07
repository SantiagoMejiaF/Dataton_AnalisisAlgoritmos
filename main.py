from ejemplos.test_Restricciones_v010 import test_Restricciones_v01
from src.Modelo_PuLP import Sucursal_pulp as modelo_pulp
from datetime import datetime
from src.Servicios import stopwatch
from src.Servicios import Dataset
from src.Servicios import result_output
from src.Parametros import Parametros


def main(Modelo):

    demanda_df, trabajadores_df = Dataset(
        './Datasets/Dataton 2023 Etapa 2.xlsx')
    # './Datasets/Dataton 2023 Etapa 2 - simplificada.xlsx')

    sucursales = [Modelo(suc_cod, demanda_df, trabajadores_df, modo='escalonado')
                  for suc_cod in demanda_df.suc_cod.unique()]

    timer = stopwatch(show=True)
    i = 0
    while Modelo.iteracion():
        sobredemanda = 0

        timer.add_subtimer("Iteracion", end="")
        print(i, ":", sep="", end="\n")

        for sucursal in sucursales:
            timer.add_subtimer(sucursal.name, end=" ")

            sucursal.step()

            timer.subtimers[sucursal.name].current_time

        sobredemanda = sum([sucursal.sobredemanda
                            for sucursal in sucursales])

        result_output("-".join([
            datetime.now().strftime("%y.%m.%d.%H.%M.%S"),
            "solucionOptimaEtapa2",
            str(i)
        ]), "./resultados/"
        ).crearCSVResultadoOptimo(sucursales)

        print('\nEl tiempo de ejecución: \nGlobal', end=" ")
        timer.current_time
        print('Iteración', end=" ")
        timer.subtimers['Iteracion'].current_time
        print('La sobredemanda resultante es: ', sobredemanda, end="\n\n")
        i += 1


if __name__ == "__main__":
    main(modelo_pulp)
    # test_Restricciones_v01()
