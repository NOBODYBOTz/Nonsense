import aiohttp
import asyncio

async def check_bin(bin_number):
    url = f"https://lookup.binlist.net/{bin_number}"
    async with aiohttp.ClientSession() as session:
        headers = {
            "authority": "lookup.binlist.net",
            "path": f"/{bin_number}",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        }
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    resultado = {
                        "Esquema": data.get("scheme", "Desconocido"),
                        "Tipo": data.get("type", "Desconocido"),
                        "Marca": data.get("brand", "Desconocida"),
                        "País": f"{data.get('country', {}).get('name', 'Desconocido')} {data.get('country', {}).get('emoji', '')}".strip(),
                        "Banco": data.get("bank", {}).get("name", "Desconocido"),
                    }
                    return resultado
                else:
                    return f"Error: Código de estado {response.status}"
        except aiohttp.ClientError as e:
            return f"Error de conexión: {str(e)}"
        except asyncio.TimeoutError:
            return "Error: Tiempo de espera agotado"
        except Exception as e:
            return f"Error inesperado: {str(e)}"
