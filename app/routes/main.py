from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.utils import process_csv_to_db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Renderizamos un template básico (que crearemos luego)
    return render_template('index.html')

@main_bp.route('/data')
def data():
    return "Aquí se mostrará la tabla de datos."

@main_bp.route('/analysis')
def analysis():
    return "Aquí se mostrarán los gráficos y análisis."

@main_bp.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        flash('No se subió ningún archivo')
        return redirect(url_for('main.index'))
        
    file = request.files['file']
    if file.filename == '':
        flash('Archivo no seleccionado')
        return redirect(url_for('main.index'))
        
    if file and file.filename.endswith('.csv'):
        # process_csv_to_db ahora soporta file-like objects, así que le pasamos el file de Flask
        process_csv_to_db(file)
        flash('Datos del CSV fusionados con éxito en la base de datos.')
        return redirect(url_for('main.data'))
    else:
        flash('Por favor sube un archivo .csv')
        return redirect(url_for('main.index'))

