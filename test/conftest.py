import os
import sys

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuración de pytest
def pytest_configure(config):
    # Configurar variables de entorno para pruebas
    os.environ['FLASK_ENV'] = 'testing' 