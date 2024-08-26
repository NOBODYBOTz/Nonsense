import aiohttp
import asyncio
from bs4 import BeautifulSoup

async def obtener_direccion_aleatoria(country):
    country = country.lower()

    headers = {
        "authority": "www.bestrandoms.com",
        "path": f"/random-address-in-{country}",
        "cache-control": "max-age=0",
        "content-length": "18",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.bestrandoms.com",
        "priority": "u=0, i",
        "referer": f"https://www.bestrandoms.com/random-address-in-{country}",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }

    data = f"abbr={country}&quantity=1"

    url = f"https://www.bestrandoms.com/random-address-in-{country}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            if response.status == 200:
                headers = {
                    "authority": "www.bestrandoms.com",
                    "method": "GET",
                    "path": f"/random-address-in-{country}?quantity=1",
                    "priority": "u=0, i",
                    "referer": f"https://www.bestrandoms.com/random-address-in-{country}",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
                }

                url = f"https://www.bestrandoms.com/random-address-in-{country}?quantity=1"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        return parse_address(html_content)
                    else:
                        return f"Error: Código de estado {response.status}"
            else:
                return f"Error: Código de estado {response.status}"

def parse_address(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    address_div = soup.find('div', class_='content')
    if address_div:
        address_info = {}
        for p in address_div.find_all('p'):
            span = p.find('span')
            if span:
                key = span.find('b').text.strip(':')
                value = span.text.replace(span.find('b').text, '').strip()
                if key == 'Street':
                    address_info['Street'] = value
                elif key == 'City':
                    address_info['City'] = value
                elif key == 'State/province/area':
                    address_info['State/province/area'] = value
                elif key == 'Phone number':
                    address_info['Phone number'] = value
                elif key == 'Zip code':
                    address_info['Zip code'] = value
                elif key == 'Country calling code':
                    address_info['Country calling code'] = value
        return address_info
    return "No se pudo encontrar la información de la dirección"

async def main():
    country = input("Ingrese el país: ")
    resultado = await obtener_direccion_aleatoria(country)
    print(resultado)

if __name__ == "__main__":
    asyncio.run(main())
