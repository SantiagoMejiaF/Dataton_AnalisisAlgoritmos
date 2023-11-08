class Parametros:
    BLOQUETRABAJOMINIMO = 4
    BLOQUETRABAJOMAXIMO = 8
    BLOQUEALMUERZO = 6
    # INICIOALMUERZOMINIMO = 16
    # INICIOALMUERZOMAXIMO = 24
    INICIOS = {'JORNADA': {'MIN': 0,
                           'MAX': 16},
               'ALMUERZO': {'MIN': 16,
                            'MAX': 24}}
    # DURACIONJORNADATRABAJADORTC = 34
    # DURACIONJORNADATRABAJADORMT = 16
    # DURACIONJORNADATRABAJADORSABADOTC = 20
    # DURACIONJORNADATRABAJADORSABADOMT = 16
    DURACIONJORNADATRABAJADOR = {'TC': {'SEMANA': 34,
                                        'SABADO': 20},
                                 'MT': {'SEMANA': 16,
                                        'SABADO': 16}}
    DURACIONTURNOTRABAJADOR = {'TC': {'SEMANA': 28,
                                      'SABADO': 16},
                               'MT': {'SEMANA': 20,
                                      'SABADO': 16}}
    DURACIONJORNADASUCURSAL = {'SEMANA': 34, 'SABADO': 20}
    SRC_DEMANDA = './src/Dataton2023_Etapa1.xlsx'
    ESTADOS = {'Nada': 0, 'Trabaja': 1, 'Pausa': 2, 'Almuerzo': 3}
