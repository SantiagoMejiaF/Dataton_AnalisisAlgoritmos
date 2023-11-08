from ejemplos.test_Restricciones_v010 import test_Restricciones_v01
from src.Modelo_PuLP import Sucursal_pulp as modelo_pulp
from datetime import datetime
from src.Servicios import stopwatch
from src.Servicios import Dataset
from src.Servicios import crearCSVPowerBI
from src.Servicios import result_output
from src.Parametros import Parametros


def main(Modelo):

    demanda_df, trabajadores_df = Dataset(
        './Datasets/Dataton 2023 Etapa 2.xlsx')
    # './Datasets/Dataton 2023 Etapa 2 - simplificada.xlsx')

    sucursales = [
        Modelo(suc_cod,
               demanda_df,
               trabajadores_df,
               # modo='escalonado'
               )
        for suc_cod in demanda_df.suc_cod.unique()]

    timer = stopwatch(show=True)
    i = 0
    prev_sobredemanda = None
    sobredemanda = 0
    while Modelo.iteracion() and sobredemanda != prev_sobredemanda:
        prev_sobredemanda = sobredemanda
        sobredemanda = 0

        timer.add_subtimer("Iteracion", end="")
        print(i, ":", sep="", end="\n")

        for sucursal in sucursales:
            timer.add_subtimer(sucursal.name, end=" ")

            sucursal.step()

            timer.subtimers[sucursal.name].current_time

        sobredemanda = sum([sucursal.sobredemanda
                            for sucursal in sucursales])

        file_name = "-".join([
            datetime.now().strftime("%y.%m.%d.%H.%M.%S"),
            "solucionOptimaEtapa2",
            str(i)])

        result_output(file_name, "./resultados/"
                      ).crearCSVResultadoOptimo(sucursales)

        solucion_path = "./resultados/" + file_name + ".csv"

        print('\nEl tiempo de ejecución: \nGlobal', end=" ")
        timer.current_time
        print('Iteración', end=" ")
        timer.subtimers['Iteracion'].current_time
        print('La sobredemanda resultante es: ', sobredemanda, end="\n\n")
        i += 1

    crearCSVPowerBI(demanda_df, solucion_path)
    print('Optimización finalizada con éxito')

if __name__ == "__main__":
    main(modelo_pulp)
