import requests
from bs4 import BeautifulSoup
import re
import logging

# Configurar el logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Función para extraer el nombre del servidor de la URL
def get_server_name(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        server = response.headers.get('Server', 'Desconocido')
        return server
    except requests.Timeout:
        logger.warning(f"Tiempo de espera agotado al obtener el nombre del servidor para {url}")
        return "Tiempo de espera agotado"
    except requests.RequestException as e:
        logger.error(f"Error al obtener el nombre del servidor para {url}: {e}")
        return "Error de conexión"

# Función para extraer el contenido de la URL y buscar características de seguridad y pasarelas de pago
def analyze_page(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP no exitosos
        content = response.text
        
        # Buscar características de seguridad
        security_indicators = {
            'captcha': re.search(r'captcha', content, re.IGNORECASE),
            'cloudflare': re.search(r'cloudflare', content, re.IGNORECASE),
            'recaptcha': re.search(r'recaptcha', content, re.IGNORECASE)
        }
        
        # Buscar pasarelas de pago
        pasarelas = {
            'Stripe': [r'stripe\.com', r'stripe\.js'],
            'Braintree': [r'braintreegateway\.com', r'braintree-api\.com'],
            'Magento': [r'magento', r'mage-'],
            'Payeezy': [r'payeezy\.com', r'payeezy\.js'],
            'Shopify': [r'shopify\.com', r'shopify\.js'],
            'PayPal': [r'paypal\.com', r'paypal-sdk'],
            'Square': [r'squareup\.com', r'square-payment-sdk'],
            'Authorize.Net': [r'authorize\.net', r'authorizenet'],
            'WooCommerce': [r'woocommerce', r'wc-'],
            'Adyen': [r'adyen\.com', r'adyen-checkout'],
            'CyberSource': [r'cybersource\.com', r'cybersource-sdk'],
            'Vantiv': [r'vantiv\.com', r'vantiv-sdk'],
            'Worldpay': [r'worldpay\.com', r'worldpay-js'],
            'Chase Paymentech': [r'chasepaymentech\.com', r'orbital-sdk'],
            'First Data': [r'firstdata\.com', r'firstdata-sdk'],
            'Global Payments': [r'globalpayments\.com', r'globalpayments-sdk'],
            'Elavon': [r'elavon\.com', r'elavon-sdk'],
            'Ingenico': [r'ingenico\.com', r'ingenico-js'],
            'Klarna': [r'klarna\.com', r'klarna-sdk'],
            'Affirm': [r'affirm\.com', r'affirm-js']
        }
        
        found_gateways = []
        for gateway, patterns in pasarelas.items():
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                found_gateways.append(gateway)
        
        return {
            'server_name': get_server_name(url),
            'security_indicators': [key for key, value in security_indicators.items() if value],
            'payment_gateways': found_gateways
        }
    except requests.Timeout:
        logger.warning(f"Tiempo de espera agotado al analizar la página {url}")
        return {'error': 'Tiempo de espera agotado'}
    except requests.HTTPError as e:
        logger.error(f"Error HTTP al analizar la página {url}: {e}")
        return {'error': f'Error HTTP: {e}'}
    except requests.RequestException as e:
        logger.error(f"Error de conexión al analizar la página {url}: {e}")
        return {'error': f'Error de conexión: {e}'}
    except Exception as e:
        logger.error(f"Error inesperado al analizar la página {url}: {e}")
        return {'error': f'Error inesperado: {e}'}
