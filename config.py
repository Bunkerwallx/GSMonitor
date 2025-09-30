import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gsm_monitor_mx_secret_2024'
    BOOTSTRAP_BOOTSWATCH_THEME = 'darkly'
    
    # Configuración GSM
    DEFAULT_DURATION = 24
    DEFAULT_OPERATOR = 'telcel'
    
    # Rutas
    DATA_DIR = 'data'
    LOGS_DIR = 'logs'
    EXPORTS_DIR = 'exports'
    
    # Configuración de red
    GSM_PORTS = [4729, 4730]
    CAPTURE_INTERFACE = 'lo'  # Ajustar según el sistema
    
    @staticmethod
    def init_app(app):
        # Crear directorios necesarios
        for directory in [Config.DATA_DIR, Config.LOGS_DIR, Config.EXPORTS_DIR]:
            os.makedirs(directory, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
