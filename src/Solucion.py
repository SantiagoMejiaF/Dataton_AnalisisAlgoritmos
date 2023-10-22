import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

RUTA_DEMANDA = '.\src\PuLP\Dataton2023_Etapa1.xlsx'
    
def mostrarSolucion(df_solucion: pd.DataFrame):
    df_demanda = pd.read_excel(RUTA_DEMANDA, sheet_name='demand')
    df_demanda['fecha'] = df_demanda['fecha_hora'].dt.strftime('%Y-%m-%d')
    df_demanda['hora'] = df_demanda['fecha_hora'].dt.strftime('%H:%M:%S')
    df_demanda = df_demanda.drop('fecha_hora', axis=1)

    # Crear un diccionario que mapea cada valor único de 'hora' a un identificador único
    unique_hours = df_demanda['hora'].unique()
    identifiers = range(30, 30 + len(unique_hours))
    identifier_dict = {hour: identifier for hour, identifier in zip(unique_hours, identifiers)}

    # Agregar una nueva columna 'identificador' basada en el mapeo del diccionario
    df_demanda['hora_franja'] = df_demanda['hora'].map(identifier_dict)

    # RUTA_SOLUCION = './src/PuLP/solucionOptima.xlsx'
    # df_solucion = pd.read_excel('./src/PuLP/solucionOptima.xlsx')
    df_solucion = df_solucion[df_solucion['estado'] == 'Trabaja'].groupby(['hora', 'hora_franja'])['estado'].count().reset_index()
    df_solucion = df_solucion.merge(df_demanda[['hora_franja', 'demanda']], on='hora_franja', how='left')
    df_solucion = df_solucion.rename(columns={'estado': 'trabajadores'})
    df_solucion['resultado'] = df_solucion['demanda'] - df_solucion['trabajadores']
    sobredemanda = df_solucion[df_solucion['resultado'] > 0]['resultado'].sum()
    print(df_solucion)
    print('La sobredemanda resultante es: ',sobredemanda)

    # Crear un gráfico de líneas
    plt.figure(figsize=(10, 6))  # Ajusta el tamaño del gráfico según tus preferencias

    # Graficar la columna 'demanda' en el eje y
    plt.bar(df_solucion['hora_franja'], df_solucion['demanda'], label='Demanda', color='gray')

    # Graficar la columna 'trabajadores' en el mismo gráfico
    plt.plot(df_solucion['hora_franja'], df_solucion['trabajadores'], label='Demanda', color='blue')

    # Rotar las etiquetas del eje x para mayor legibilidad
    plt.xticks(rotation=45)

    # Agregar etiquetas y título al gráfico
    plt.xlabel('Franja Horaria')
    plt.ylabel('Cantidad')
    plt.title('Capacidad vs. Demanda')

    # Agregar una leyenda
    plt.legend()

    # Mostrar el gráfico
    plt.grid(True)
    # plt.show()

    plt.figure(figsize=(10, 6))  # Ajusta el tamaño del gráfico
    colores = np.where(df_solucion['resultado'] >= 0, 'orange', 'green')
    # Crea el gráfico de barras con los colores personalizados
    plt.bar(df_solucion['hora_franja'], df_solucion['resultado'], color=colores)

    # Agrega una línea horizontal negra en el valor cero
    plt.axhline(0, color='black', linestyle='--', linewidth=1)

    plt.xlabel('Franja Hora')
    plt.ylabel('Resultado')
    plt.title('Demanda - Capacidad')
    plt.xticks(rotation=45)  # Rota las etiquetas del eje x para mayor legibilidad
    plt.show()

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import Solucion
df_solucion = pd.read_csv('.\src\PuLP\solucionOptima.csv')
Solucion.mostrarSolucion(df_solucion)