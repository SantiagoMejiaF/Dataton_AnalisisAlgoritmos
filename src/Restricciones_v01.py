from .Parametros import Parametros as C

# --------- Estados -----------
N = 0  # No Trabaja
T = 1  # Trabajo
P = 2  # Pausa Activa
A = 3  # Almuerzo


class Trabajador:
    def __init__(self, distribucion: list):
        self.lista = distribucion
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
    def __init__(self):
        pass

    def trabajadoresActivos(self, franja: int, estado: int = T):
        return len([
            trabajador
            for trabajador in self.trabajadores
            if trabajador.lista[franja] == estado])

    def validacionDisponibilidad(self):
        return self.trabajadoresActivos() > 0
