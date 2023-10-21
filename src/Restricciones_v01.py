
from datetime import datetime
if __name__ == "__main__":
    import os
    os.chdir("..")
# ----------------
from src.Parametros import Parametros as C
import pandas as pd

# --------- Estados -----------
N = 0  # No Trabaja
T = 1  # Trabajo
P = 2  # Pausa Activa
A = 3  # Almuerzo


class Trabajador:
    def __init__(self, distribucion: list, documento: int):
        self.lista = distribucion
        self.documento = documento
        self.bloques = Trabajador_services.bloquesTrabajador(self)

    def CantidadBloques(self, estado: int):
        return len([
            bloque
            for bloque in self.bloques
            if bloque[0] == estado])

    def validarInicioEstado(self, estado: int, minimo: int, maximo: int):
        if not(estado in self.lista):
            return False

        return minimo <= self.lista.index(estado) <= maximo

    def validaDuracionRango(self, estado: int, minimo: int, maximo: int = None):
        casos = []
        maximo = maximo if maximo else minimo
        for bloque in self.bloques:
            if bloque[0] == estado:
                casos.append(minimo <= bloque[1] <= maximo)

        return all(casos)

    def duracionBloques(self, excluir_estados: list = []):

        return sum([
            bloque[1]
            for bloque in self.bloques
            if not(bloque[0] in excluir_estados)
        ])

    def validacionBloquesAdyacentes(self,
                                    estado: int,
                                    estado_siguiente: int = None,
                                    estado_previo: int = None):

        estados = [bloque[0] for bloque in self.bloques]
        casos = []

        i_previo = None
        i_siguiente = 1

        for i, estado_i in enumerate(estados):

            if estado_i != estado:
                continue

            if i_previo != None and estado_siguiente != None:
                casos.append(estados[i_previo] == estado_previo)

            if i_siguiente < len(estados) and estado_previo != None:
                casos.append(estados[i_siguiente] == estado_siguiente)

            i_previo = i_previo + 1 if i_previo != None else None
            i_siguiente = i_siguiente + 1 if i_siguiente != None else None

        return all(casos)

    # ------- Validaciones ----------

    def rangoValido(self):

        if not(Trabajador_services.ValidacionBloqueAlmuerzo(self)):
            return False, "Almuerzo invalido"

        if not(Trabajador_services.ValidacionBloqueTrabajo(self)):
            return False, "Bloques de Trabajo invalidos"

        if not(Trabajador_services.validacionBloquePausaActiva(self)):
            return False, "Pausas Activas invalidas"

        if not(Trabajador_services.validacionJornada(self)):
            return False, "Jornada invalida"

        return True, "Rango Valido"


class Trabajador_services:

    def bloquesTrabajador(trabajador: Trabajador):

        if not trabajador.lista:
            return []

        result = []
        current_element = trabajador.lista[0]
        count = 1

        for element in trabajador.lista[1:]:
            if element == current_element:
                count += 1
            else:
                result.append([current_element, count])
                current_element = element
                count = 1

        result.append([current_element, count])
        return result

    def ValidacionBloqueAlmuerzo(trabajador: Trabajador):

        validaciones = [

            trabajador.validaDuracionRango(A, C.BLOQUEALMUERZO),

            trabajador.CantidadBloques(A) == 1,

            trabajador.validarInicioEstado(
                A, C.INICIOALMUERZOMINIMO, C.INICIOALMUERZOMAXIMO)
        ]

        return all(validaciones)

    def ValidacionBloqueTrabajo(trabajador: Trabajador):

        validaciones = [

            trabajador.validaDuracionRango(
                T, C.BLOQUETRABAJOMINIMO, C.BLOQUETRABAJOMAXIMO),

            trabajador.validarInicioEstado(T, 0, 10)
        ]

        return all(validaciones)

    def validacionJornada(trabajador: list):

        validaciones = [

            trabajador.CantidadBloques(N) in [1, 2],

            trabajador.duracionBloques(
                excluir_estados=[N]) == C.DURACIONJORNADATRABAJADOR,

            trabajador.duracionBloques() == C.DURACIONJORNADASUCURSAL
        ]

        return all(validaciones)

    def validacionBloquePausaActiva(trabajador: list):
        validaciones = [
            trabajador.validaDuracionRango(P, 1),
            trabajador.validacionBloquesAdyacentes(P, T)
        ]
        return all(validaciones)


class Sucursal:
    def __init__(self, horario: pd.DataFrame, demanda: pd.DataFrame):

        self.df = horario.copy()
        if not(self.checkInputFormat()):
            return "DataFrame de entrada invalido"

        self.demanda = demanda.copy()
        Sucursal.fechahora2horafranja(self.demanda)

        self.Jornadas = self.horario2trabajador()

    def horario2trabajador(self):

        fechas = {}
        for fecha in self.demanda.fecha.unique():
            trabajadores = []
            for documento in self.df.documento.unique():
                trabajador = self.df[
                    (self.df.fecha == datetime.strftime(fecha, '%Y-%m-%d')) &
                    (self.df.documento == documento)
                ][['hora_franja', 'estado']]
                trabajador = [
                    C.ESTADOS[
                        trabajador[trabajador.hora_franja ==
                                   franja].estado.iloc[0]
                    ]
                    for franja in trabajador.hora_franja]
                # print(trabajador)
                trabajadores.append(Trabajador(trabajador, documento))
            fechas[fecha] = trabajadores

        return fechas

        # self.trabajadores = [Trabajador()]

    def checkInputFormat(self):
        columns_needed = ['suc_code', 'documento',
                          'fecha_hora', 'estado', 'fecha', 'hora']
        cols = {col: col in self.df.columns for col in columns_needed}

        if not(cols['fecha_hora']) and cols['fecha'] and cols['hora']:
            def fecha_hora(s): return datetime.strptime(
                " ".join([s["fecha"], s.hora]), "%Y-%m-%d %H:%M:%S")
            self.df['fecha_hora'] = self.df.apply(fecha_hora, axis=1)
            cols['fecha_hora'] = 'fecha_hora' in self.df.columns

        return all([v for k, v in cols.items()])

    def fechahora2horafranja(df):

        def df_fecha(x): return datetime.date(x['fecha_hora'])
        def df_hora(x): return datetime.time(x['fecha_hora'])

        def df_hora_franja(x):
            return -30 + sum([
                int(int(t)*(60**i)/15)
                for i, t in enumerate(
                    datetime.strftime(
                        x['fecha_hora'], '%H:%M').split(":")[::-1]
                )])

        df['fecha'] = df.apply(df_fecha, axis=1)
        df['hora'] = df.apply(df_hora, axis=1)
        df['hora_franja'] = df.apply(df_hora_franja, axis=1)

    def trabajadoresActivos(self, franja: int, estado: int = T):
        return len([
            trabajador
            for trabajador in self.trabajadores
            if trabajador.lista[franja] == estado])

    def validacionDisponibilidad(self):

        df = self.df.copy()
        df = df[df.estado == 'Trabaja'][['fecha_hora', 'documento']
                                        ].groupby(by="fecha_hora").count()
        franjas_desatendidas = df[df.documento <= 0].size

        return franjas_desatendidas <= 0

    def evaluar(self):

        if not(self.validacionDisponibilidad()):
            return False, "Hay una franja desatendida"

        for fecha, trabajadores in self.Jornadas.items():
            for trabajador in trabajadores:
                valido, msg = trabajador.rangoValido()
                if not(valido):
                    return False, " ".join([datetime.strftime(fecha, '%Y-%m-%d'), msg])
        return True, ""


if __name__ == "__main__":

    dataton2023 = './src/Dataton2023_Etapa1.xlsx'
    demanda_df = pd.read_excel(dataton2023, sheet_name='demand')

    solucion = pd.read_excel('./src/PuLP/solucionOptima.xlsx')
    s = Sucursal(solucion, demanda_df)
    print(s.evaluar())
