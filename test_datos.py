import pandas as pd

# 1. Cargar el dataset
df = pd.read_csv('rym_clean1.csv')

# 2. Identificar todos los registros que tienen duplicados (mostrando todas las ocurrencias)
# Usamos keep=False para ver tanto el original como la copia
duplicates = df[df.duplicated(subset=['release_name', 'artist_name'], keep=False)]

# 3. Ordenar para que aparezcan juntos y sea fácil comparar
duplicates_sorted = duplicates.sort_values(by=['artist_name', 'release_name'])

print(f"--- Auditoría de Duplicados ---")
print(f"Se encontraron {len(duplicates_sorted)} filas que generan colisiones.")
print(duplicates_sorted[['artist_name', 'release_name']])

# Opcional: Guardar a un CSV aparte para revisar con calma
# duplicates_sorted.to_csv('auditoria_duplicados.csv', index=False)