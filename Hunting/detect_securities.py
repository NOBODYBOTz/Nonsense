import aiohttp
from bs4 import BeautifulSoup
import re

async def analizar_url(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                headers = response.headers
                text = await response.text()

                seguridades = detectar_seguridades(headers, text)
                servidor = headers.get('Server', 'No detectado')
                tecnologias = detectar_tecnologias(text)

                resultado = f"Análisis de {url}\n\n"
                resultado += f"Seguridades detectadas: {', '.join(seguridades) if seguridades else 'Ninguna'}\n"
                resultado += f"Servidor: {servidor}\n"
                resultado += f"Tecnologías detectadas: {', '.join(tecnologias) if tecnologias else 'Ninguna'}\n"

                return resultado
        except Exception as e:
            return f"Error al analizar la URL: {str(e)}"

def detectar_seguridades(headers, text):
    seguridades = []
    if 'cf-ray' in headers:
        seguridades.append("Cloudflare")
    if 'captcha' in text.lower():
        seguridades.append("Captcha")
    if 'x-sucuri-id' in headers:
        seguridades.append("Sucuri")
    if 'x-fw-hash' in headers:
        seguridades.append("Incapsula")
    if 'x-akamai-transformed' in headers:
        seguridades.append("Akamai")
    
    if any(waf in str(headers) for waf in ['x-xss-protection', 'x-frame-options', 'x-content-type-options']):
        seguridades.append("WAF genérico")
    
    return seguridades

def detectar_tecnologias(text):
    tecnologias = set()
    soup = BeautifulSoup(text, 'html.parser')
    
    for meta in soup.find_all('meta'):
        if 'generator' in meta.get('name', '').lower():
            tecnologias.add(meta['content'])
    
    js_frameworks = re.findall(r'(React|Angular|Vue|jQuery)', text)
    tecnologias.update(js_frameworks)
    
    return tecnologias
