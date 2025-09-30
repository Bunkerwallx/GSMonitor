import threading
import time
import json
import logging
from datetime import datetime, timedelta
from .imsi_generator import IMSIGenerator
from .triangulator import TriangulatorGSM
from scapy.all import sniff
import numpy as np

class GSMMonitor:
    def __init__(self, duration_hours=24):
        self.duration = duration_hours
        self.is_active = False
        self.start_time = None
        self.end_time = None
        self.imsi_generator = IMSIGenerator()
        self.triangulator = TriangulatorGSM()
        self.results = {
            'detected_imsis': set(),
            'locations': [],
            'monitored_imsis': set(),
            'statistics': {
                'packets_analyzed': 0,
                'gsm_messages': 0,
                'unique_cells': set()
            }
        }
        self.current_operation = "Listo"
        self.monitor_thread = None

    def start_monitoring(self, phone_number=None, operator="telcel", visualization="map"):
        """Inicia el monitoreo GSM"""
        self.is_active = True
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=self.duration)
        
        # Generar IMSIs a monitorear
        if phone_number:
            imsis = self.imsi_generator.generate_from_phone(phone_number, operator)
        else:
            imsis = self.imsi_generator.generate_random(operator, 50)
        
        self.results['monitored_imsis'] = set(imsis)
        self.current_operation = f"Monitoreando {len(imsis)} IMSIs"
        
        # Iniciar captura en hilo separado
        self.monitor_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.is_active = False
        self.current_operation = "Monitoreo detenido"

    def is_monitoring_active(self):
        """Verifica si el monitoreo está activo"""
        return self.is_active and datetime.now() < self.end_time

    def get_progress(self):
        """Obtiene progreso del monitoreo"""
        if not self.start_time or not self.end_time:
            return 0
        elapsed = datetime.now() - self.start_time
        total = self.end_time - self.start_time
        return min(100, (elapsed.total_seconds() / total.total_seconds()) * 100)

    def get_current_operation(self):
        """Obtiene operación actual"""
        return self.current_operation

    def get_current_results(self):
        """Obtiene resultados actuales"""
        return {
            'detected_imsis': list(self.results['detected_imsis']),
            'locations': self.results['locations'][-50:],  # Últimas 50 ubicaciones
            'monitored_count': len(self.results['monitored_imsis']),
            'detected_count': len(self.results['detected_imsis']),
            'location_count': len(self.results['locations']),
            'statistics': {
                'packets_analyzed': self.results['statistics']['packets_analyzed'],
                'gsm_messages': self.results['statistics']['gsm_messages'],
                'unique_cells': len(self.results['statistics']['unique_cells'])
            }
        }

    def get_final_report(self):
        """Genera reporte final"""
        return {
            'summary': {
                'duration_hours': self.duration,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_monitored': len(self.results['monitored_imsis']),
                'total_detected': len(self.results['detected_imsis']),
                'total_locations': len(self.results['locations']),
                'success_rate': len(self.results['detected_imsis']) / len(self.results['monitored_imsis']) if self.results['monitored_imsis'] else 0
            },
            'detected_imsis': list(self.results['detected_imsis']),
            'locations': self.results['locations'],
            'statistics': self.results['statistics']
        }

    def export_data(self, format_type):
        """Exporta datos en formato específico"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'json':
            filename = f"gsm_monitor_export_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(self.get_final_report(), f, indent=2)
        elif format_type == 'csv':
            filename = f"gsm_monitor_export_{timestamp}.csv"
            self._export_to_csv(filename)
        
        return filename

    def _export_to_csv(self, filename):
        """Exporta a CSV"""
        import csv
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['IMSI', 'Timestamp', 'Latitude', 'Longitude', 'Precision', 'Cell_ID'])
            
            for location in self.results['locations']:
                writer.writerow([
                    location.get('imsi', ''),
                    location.get('timestamp', ''),
                    location.get('lat', ''),
                    location.get('lon', ''),
                    location.get('precision', ''),
                    location.get('cell_id', '')
                ])

    def _capture_loop(self):
        """Loop principal de captura de paquetes"""
        try:
            self.current_operation = "Iniciando captura de paquetes GSM..."
            
            def packet_handler(packet):
                if not self.is_active:
                    return
                
                self.results['statistics']['packets_analyzed'] += 1
                
                # Simular análisis de paquetes GSM (integrar con código anterior)
                gsm_data = self._analyze_packet(packet)
                if gsm_data:
                    self._process_gsm_data(gsm_data)
            
            # Capturar por el tiempo especificado
            remaining_time = (self.end_time - datetime.now()).total_seconds()
            if remaining_time > 0:
                sniff(
                    iface="lo",  # Ajustar según interfaz
                    filter="port 4729 and udp",
                    prn=packet_handler,
                    timeout=min(remaining_time, 3600),  # Máximo 1 hora por sesión
                    store=0
                )
            
            # Continuar si aún queda tiempo
            if self.is_active and datetime.now() < self.end_time:
                self._capture_loop()
            else:
                self.is_active = False
                self.current_operation = "Monitoreo completado"
                
        except Exception as e:
            logging.error(f"Error en captura: {e}")
            self.is_active = False

    def _analyze_packet(self, packet):
        """Analiza paquete en busca de datos GSM"""
        # Integrar aquí el código de análisis de paquetes anterior
        try:
            # Simulación de detección
            if len(packet) > 100:  # Paquete suficientemente grande
                self.results['statistics']['gsm_messages'] += 1
                
                # Simular detección aleatoria para demo
                if np.random.random() < 0.01:  # 1% de probabilidad de detección
                    monitored_imsis = list(self.results['monitored_imsis'])
                    if monitored_imsis:
                        imsi = np.random.choice(monitored_imsis)
                        return {
                            'imsi': imsi,
                            'mcc': '334',
                            'mnc': '020',
                            'lac': str(np.random.randint(1000, 9999)),
                            'cell_id': str(np.random.randint(10000, 99999)),
                            'rssi': np.random.randint(-110, -50),
                            'timestamp': datetime.now().isoformat()
                        }
        except Exception as e:
            logging.error(f"Error analizando paquete: {e}")
        
        return None

    def _process_gsm_data(self, gsm_data):
        """Procesa datos GSM detectados"""
        imsi = gsm_data['imsi']
        
        # Registrar IMSI detectado
        if imsi not in self.results['detected_imsis']:
            self.results['detected_imsis'].add(imsi)
            self.current_operation = f"IMSI detectado: {imsi[:8]}..."
        
        # Registrar celda única
        cell_key = f"{gsm_data['mcc']}-{gsm_data['mnc']}-{gsm_data['lac']}-{gsm_data['cell_id']}"
        self.results['statistics']['unique_cells'].add(cell_key)
        
        # Triangulación (simulada para demo)
        location = self.triangulator.triangulate([gsm_data])
        if location:
            location_data = {
                'imsi': imsi,
                'lat': location['lat'],
                'lon': location['lon'],
                'precision': location['precision'],
                'timestamp': gsm_data['timestamp'],
                'cell_id': gsm_data['cell_id'],
                'method': location['method']
            }
            self.results['locations'].append(location_data)
            
            # Mantener máximo 1000 ubicaciones
            if len(self.results['locations']) > 1000:
                self.results['locations'].pop(0)
