from datetime import datetime
import pandas as pd


class stopwatch:
    def __init__(self, show=False, name: str = "", end=None):
        self.start = datetime.now()
        self.subtimers = {}
        self.show = show
        if show:
            print("Inicio " + name + ": " if name else 'Inicio: ', end=end)

    @property
    def current_time(self):
        t = datetime.now() - self.start
        if self.show:
            print(" ".join(["Time: ", str(t)]))

        return t

    def reset(self):
        self.start = datetime.now()

    def add_subtimer(self, name, end=None):
        self.subtimers[name] = stopwatch(show=self.show, name=name, end=end)


def Dataset(dataset: str) -> None:
    # directory = directory
    # dataset = directory + dataset

    demanda_df = pd.read_excel(dataset, sheet_name='demand')
    trabajadores_df = pd.read_excel(dataset, sheet_name='workers')

    return demanda_df, trabajadores_df


class result_output:
    def __init__(self, name=None, path="./src/PuLP/Etapa2/") -> None:
        self.df = pd.DataFrame()
        self.df = result_output.crearDataframeOptimoVacio(self.df)
        self.path = "".join(
            [path, name, ".csv"]) if name else ""

    def juntarSucursales(self, sucursales):
        df = pd.DataFrame()
        df = result_output.crearDataframeOptimoVacio(df)
        for sucursal in sucursales:
            df = pd.concat(
                [df, sucursal.df_optimo], ignore_index=True)
        return df

    def crearDataframeOptimoVacio(solucionOptima_df):

        # Definir la estructura del DataFrame
        columnas = ["suc_cod", "documento", "fecha",
                    "hora", "estado", "hora_franja"]

        # Crear un DataFrame vacío
        solucionOptima_df = pd.DataFrame(columns=columnas, dtype="object")

        return solucionOptima_df

    def crearCSVResultadoOptimo(self, sucursales):
        csv = self.juntarSucursales(sucursales)
        csv.to_csv(self.path, index=False)
