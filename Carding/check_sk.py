import aiohttp
import asyncio
from typing import Dict, Any

async def verificar_sk(sk: str) -> str:
    url = "https://api.stripe.com/v1/balance"
    headers = {
        "Authorization": f"Bearer {sk}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as respuesta:
                if respuesta.status == 200:
                    datos = await respuesta.json()
                    disponible = datos['available'][0]['amount']
                    moneda = datos['available'][0]['currency']
                    return f"✅ SK válida\n💰 Saldo disponible: {disponible/100:.2f} {moneda.upper()}"
                elif respuesta.status == 401:
                    return "SK inválida o expirada. ❌"
                else:
                    return f"⚠️ Error desconocido. Código de estado: {respuesta.status}"
        except aiohttp.ClientError as e:
            return f"⚠️ Error de conexión: {str(e)}"
        except asyncio.TimeoutError:
            return "⚠️ Tiempo de espera agotado"
        except Exception as e:
            return f"⚠️ Error inesperado: {str(e)}"
