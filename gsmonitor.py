#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_socketio import SocketIO, emit
from bootstrap_flask import Bootstrap5
import json
import threading
import time
import os
from datetime import datetime, timedelta
import logging
from modules.gsm_monitor import GSMMonitor
from modules.imsi_generator import IMSIGenerator
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gsm_monitor_mx_secret_2024'
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'darkly'
Bootstrap5(app)
socketio = SocketIO(app, async_mode='eventlet')

# Estado global del monitoreo
monitor_status = {
    'active': False,
    'progress': 0,
    'current_operation': '',
    'detected_imsis': 0,
    'locations_found': 0,
    'start_time': None,
    'estimated_end': None
}

current_monitor = None

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    """Inicia el monitoreo GSM"""
    global current_monitor, monitor_status
    
    if monitor_status['active']:
        return jsonify({'status': 'error', 'message': 'Ya hay un monitoreo en curso'})
    
    try:
        data = request.json
        phone_number = data.get('phone_number', '').strip()
        operator = data.get('operator', 'telcel')
        duration = int(data.get('duration', 24))
        visualization = data.get('visualization', 'map')
        
        # Inicializar monitor
        current_monitor = GSMMonitor(duration)
        
        # Configurar monitoreo en hilo separado
        monitor_thread = threading.Thread(
            target=run_monitoring,
            args=(current_monitor, phone_number, operator, visualization),
            daemon=True
        )
        monitor_thread.start()
        
        monitor_status.update({
            'active': True,
            'progress': 0,
            'detected_imsis': 0,
            'locations_found': 0,
            'start_time': datetime.now(),
            'estimated_end': datetime.now() + timedelta(hours=duration),
            'current_operation': 'Iniciando captura GSM...'
        })
        
        return jsonify({'status': 'success', 'message': 'Monitoreo iniciado'})
        
    except Exception as e:
        logging.error(f"Error iniciando monitoreo: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/stop_monitoring', methods=['POST'])
def stop_monitoring():
    """Detiene el monitoreo en curso"""
    global current_monitor, monitor_status
    
    if current_monitor and monitor_status['active']:
        current_monitor.stop_monitoring()
        monitor_status['active'] = False
        monitor_status['current_operation'] = 'Monitoreo detenido'
        return jsonify({'status': 'success', 'message': 'Monitoreo detenido'})
    
    return jsonify({'status': 'error', 'message': 'No hay monitoreo activo'})

@app.route('/status')
def get_status():
    """Obtiene el estado actual del monitoreo"""
    if monitor_status['active'] and monitor_status['start_time']:
        elapsed = datetime.now() - monitor_status['start_time']
        total_time = monitor_status['estimated_end'] - monitor_status['start_time']
        monitor_status['progress'] = min(100, (elapsed.total_seconds() / total_time.total_seconds()) * 100)
    
    return jsonify(monitor_status)

@app.route('/results')
def get_results():
    """Obtiene resultados del monitoreo"""
    if current_monitor:
        results = current_monitor.get_current_results()
        return jsonify(results)
    return jsonify({})

@app.route('/export/<format_type>')
def export_data(format_type):
    """Exporta datos en diferentes formatos"""
    if not current_monitor:
        return jsonify({'status': 'error', 'message': 'No hay datos para exportar'})
    
    try:
        filename = current_monitor.export_data(format_type)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@socketio.on('connect')
def handle_connect():
    """Maneja conexión de SocketIO"""
    emit('status_update', monitor_status)

def run_monitoring(monitor, phone_number, operator, visualization):
    """Ejecuta el monitoreo en segundo plano"""
    try:
        monitor.start_monitoring(
            phone_number=phone_number if phone_number else None,
            operator=operator,
            visualization=visualization
        )
        
        # Actualizar progreso periódicamente
        while monitor.is_monitoring_active():
            time.sleep(5)
            
            # Emitir actualizaciones via SocketIO
            results = monitor.get_current_results()
            socketio.emit('monitoring_update', {
                'progress': monitor.get_progress(),
                'detected_imsis': len(results.get('detected_imsis', [])),
                'locations': len(results.get('locations', [])),
                'current_operation': monitor.get_current_operation()
            })
        
        # Monitoreo completado
        final_results = monitor.get_final_report()
        socketio.emit('monitoring_complete', final_results)
        monitor_status['active'] = False
        
    except Exception as e:
        logging.error(f"Error en monitoreo: {e}")
        socketio.emit('monitoring_error', {'error': str(e)})
        monitor_status['active'] = False

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
