import sqlite3
import pandas as pd
import plotly.express as px
import os

def visualize():
    # Ruta a la DB desde la subcarpeta scripts
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"Error: No se encontró la base de datos en {db_path}")
        return

    conn = sqlite3.connect(db_path)
    query = "SELECT title, artist, lastfm_listeners, lastfm_playcount, avg_rating, rating_count FROM album"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Filtro de calidad (al menos 1000 oyentes)
    df = df[df['lastfm_listeners'] >= 1000]

    # 1. Reproducciones vs Oyentes
    fig1 = px.scatter(df, x='lastfm_listeners', y='lastfm_playcount', 
                     hover_data=['title', 'artist'], title='Reproducciones vs Oyentes (Last.fm)')
    fig1.show()

    # 2. Rating vs 'Obsesión' (Playcount/Listeners)
    df['obsession'] = df['lastfm_playcount'] / df['lastfm_listeners']
    fig2 = px.scatter(df, x='avg_rating', y='obsession', 
                     hover_data=['title', 'artist'], title='Rating vs Índice de Obsesión')
    fig2.show()

if __name__ == "__main__":
    visualize()
