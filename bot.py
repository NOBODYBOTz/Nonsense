import asyncio
import logging
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from config import API_TOKEN, ADMIN_ID
from Carding.gen_cards import GenerarTarjeta
from Carding.bin_check import check_bin
from Carding.check_sk import verificar_sk
from Users.users_management import (
    get_user, add_premium_user, remove_premium_user,
    update_plan, add_credits, is_premium_user, clean_expired_users
)
from Users.key_management import generate_key, validate_and_use_key, get_all_keys
from Carding.random_address import obtener_direccion_aleatoria
from Hunting.site_analize import analyze_page

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TOKEN = API_TOKEN

dp = Dispatcher()
logger = logging.getLogger(__name__)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hola, {message.from_user.full_name} Bienvenido al bot de Carding!")

@dp.message(Command('genkey', prefix='/.!'))
async def generate_key_command(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        await message.reply("No tienes permiso para usar este comando.")
        return
    
    try:
        _, reward_type, value = message.text.split()
        value = int(value)
        
        if reward_type not in ["credits", "days"]:
            raise ValueError("El tipo de recompensa debe ser 'credits' o 'days'")
        
        key = generate_key(reward_type, value)
        await message.reply(f"Clave generada: {key}\nTipo: {reward_type}\nValor: {value}")
    except ValueError as e:
        await message.reply(f"Error: {str(e)}\nFormato correcto: /genkey [credits|days] valor")
    except Exception as e:
        logger.error(f"Error al generar clave: {str(e)}")
        await message.reply("Ocurrió un error al procesar la solicitud.")

@dp.message(Command('usekey', prefix='/.!'))
async def use_key_command(message: Message) -> None:
    try:
        # Dividimos el mensaje en partes y nos aseguramos de tener al menos dos partes
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            raise ValueError("Falta la clave")
        
        key = parts[1].strip()  # Tomamos la segunda parte como la clave y eliminamos espacios en blanco
        result = validate_and_use_key(message.from_user.id, key)
        
        if result:
            await message.reply(result)
        else:
            await message.reply("La clave ingresada no es válida o ha expirado.")
    except ValueError as e:
        await message.reply(f"Error: {str(e)}\nFormato correcto: /usekey CLAVE")
    except Exception as e:
        logger.error(f"Error al usar clave: {str(e)}")
        await message.reply("Ocurrió un error al procesar la solicitud.")

@dp.message(Command('listkeys', prefix='/.!'))
async def list_keys_command(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        await message.reply("No tienes permiso para usar este comando.")
        return
    
    keys = get_all_keys()
    if not keys:
        await message.reply("No hay claves activas en este momento.")
        return
    
    response = "Claves activas:\n\n"
    for key, data in keys.items():
        response += f"Clave: {key}\n"
        response += f"Tipo: {data['reward_type']}\n"
        response += f"Valor: {data['value']}\n"
        response += f"Expira: {data['expiration_date'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    await message.reply(response)

@dp.message(Command('gen', prefix='/.!'))
async def gen_cards(message: Message) -> None:
    if not is_premium_user(message.from_user.id):
        await message.reply("No tienes un plan premium activo o ha expirado.")
        return
    
    try:
        _, BIN = message.text.split()

        Cantidad = 10
        generador = GenerarTarjeta(BIN=BIN, cantidad=Cantidad)
        await message.reply(f"Tarjetas Generadas:\n\n{generador}", parse_mode='MarkdownV2')
    except ValueError:
        await message.reply("Formato incorrecto. Usa: /gen BIN")
    except Exception as e:
        await message.reply(f"Ocurrió un error: {str(e)}")

@dp.message(Command('premium', prefix='/.!'))
async def add_premium(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        await message.reply("No tienes permiso para usar este comando.")
        return
    try:
        _, user_id, plan, dias = message.text.split()
        user_id = int(user_id)
        dias = int(dias)
        add_premium_user(user_id, plan, dias)
        await message.reply(f"Usuario {user_id} agregado con plan {plan} por {dias} días.")
    except ValueError as e:
        await message.reply(f"Error: {str(e)}\nFormato correcto: /premium user_id plan dias")
    except Exception as e:
        logger.error(f"Error al agregar usuario premium: {str(e)}")
        await message.reply("Ocurrió un error al procesar la solicitud.")

@dp.message(Command('remove_premium', prefix='/.!'))
async def remove_premium(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        await message.reply("No tienes permiso para usar este comando.")
        return
    try:
        _, user_id = message.text.split()
        user_id = int(user_id)
        remove_premium_user(user_id)
        await message.reply(f"Usuario {user_id} removido de premium.")
    except ValueError as e:
        await message.reply(f"Error: {str(e)}\nFormato correcto: /remove_premium user_id")
    except Exception as e:
        logger.error(f"Error al remover usuario premium: {str(e)}")
        await message.reply("Ocurrió un error al procesar la solicitud.")

@dp.message(Command('update_plan', prefix='/.!'))
async def update_user_plan(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        await message.reply("No tienes permiso para usar este comando.")
        return
    try:
        _, user_id, new_plan, dias = message.text.split()
        user_id = int(user_id)
        dias = int(dias)
        update_plan(user_id, new_plan, dias)
        await message.reply(f"Plan actualizado para el usuario {user_id} a {new_plan} con {dias} días adicionales.")
    except ValueError as e:
        await message.reply(f"Error: {str(e)}\nFormato correcto: /update_plan user_id nuevo_plan dias_adicionales")
    except Exception as e:
        logger.error(f"Error al actualizar plan: {str(e)}")
        await message.reply("Ocurrió un error al procesar la solicitud.")

@dp.message(Command('add_credits', prefix='/.!'))
async def add_user_credits(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        await message.reply("No tienes permiso para usar este comando.")
        return
    try:
        _, user_id, credits = message.text.split()
        user_id = int(user_id)
        credits = int(credits)
        if add_credits(user_id, credits):
            await message.reply(f"Se han agregado {credits} créditos al usuario {user_id}.")
        else:
            await message.reply(f"No se pudo agregar créditos. El usuario {user_id} no existe.")
    except ValueError as e:
        await message.reply(f"Error: {str(e)}\nFormato correcto: /add_credits user_id cantidad")
    except Exception as e:
        logger.error(f"Error al agregar créditos: {str(e)}")
        await message.reply("Ocurrió un error al procesar la solicitud.")

@dp.message(Command('my', prefix='/.!'))
async def user_info(message: Message) -> None:
    user = get_user(message.from_user.id)
 
    tiempo_restante = datetime.fromisoformat(user['tiempo_restante'])
    dias_restantes = (tiempo_restante - datetime.now()).days
    await message.reply(f"Información de usuario:\n"
                        f"ID: `{message.from_user.id}\n`"
                        f"Nombre: {message.from_user.full_name}\n"
                        f"Plan: {user['plan']}\n"
                        f"Días restantes: {dias_restantes}\n"
                        f"Créditos disponibles: {user.get('creditos', 0)}", parse_mode='MarkdownV2')

@dp.message(Command('bin', prefix='/.!'))
async def check_bin_command(message: Message) -> None:
    if not is_premium_user(message.from_user.id):
        await message.reply("No tienes un plan premium activo o ha expirado.")
        return
    
    try:
        _, bin_number = message.text.split()
        if len(bin_number) < 6:
            raise ValueError("El BIN debe tener al menos 6 dígitos.")
    except ValueError as e:
        await message.reply(f"Formato incorrecto. {str(e)} Usa: /bin XXXXXX")
        return
    
    try:
        bin = bin_number[:6]
        result = await check_bin(bin)
        if isinstance(result, dict):
            response = f"*BIN: {bin}\n*"
            for key, value in result.items():
                response += f"*{key}*: `{value}`\n"
        else:
            response = result
        await message.reply(response, parse_mode='MarkdownV2')
    except Exception as e:
        logger.error(f"Error al verificar BIN: {str(e)}")
        await message.reply("Ocurrió un error al procesar la solicitud. Por favor, intenta de nuevo más tarde.")


@dp.message(Command('cleanup', prefix='.!'))
async def manual_cleanup(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        await message.reply("No tienes permiso para usar este comando.")
        return
    
    try:
        cleaned_users = clean_expired_users()
        if cleaned_users > 0:
            await message.reply(f"Se eliminaron {cleaned_users} usuarios expirados.")
        else:
            await message.reply("No se encontraron usuarios expirados para eliminar.")
    except Exception as e:
        logger.error(f"Error durante la limpieza manual: {str(e)}")
        await message.reply("Ocurrió un error al intentar limpiar los usuarios expirados. Por favor, revisa los logs para más detalles.")

@dp.message(Command('dir', prefix='/.!'))
async def get_random_address(message: Message) -> None:
    if not is_premium_user(message.from_user.id):
        await message.reply("No tienes un plan premium activo o ha expirado.")
        return
    
    try:
        _, country = message.text.split()
    except ValueError:
        await message.reply("Formato incorrecto. Usa: /address PAÍS")
        return
    
    try:
        address = await obtener_direccion_aleatoria(country)
        if isinstance(address, dict):
            response = f"*📍Dirección {country}📍*\n\n"
            for key, value in address.items():
                response += f"*{key}*: `{value}`\n"
        else:
            response = address
        await message.reply(response, parse_mode='MarkdownV2')

    except Exception as e:
        logger.error(f"Error al obtener dirección aleatoria: {str(e)}")
        await message.reply("Ocurrió un error al procesar la solicitud. Por favor, intenta de nuevo más tarde.")

@dp.message(Command('sk', prefix='/.!'))
async def check_sk_command(message: Message) -> None:
    if not is_premium_user(message.from_user.id):
        await message.reply("No tienes un plan premium activo o ha expirado.")
        return
    sk = message.text.split()
    resultado = await verificar_sk(sk)
    await message.reply(resultado)

@dp.message(Command('site', prefix='/.!'))
async def analyze_site_command(message: Message) -> None:
    if not is_premium_user(message.from_user.id):
        await message.reply("No tienes un plan premium activo o ha expirado.")
        return
    
    try:
        _, url = message.text.split()
    except ValueError:
        await message.reply("Formato incorrecto. Usa: /site URL")
        return
    
    try:
        analysis = analyze_page(url)
        if 'error' in analysis:
            await message.reply(f"Error: {analysis['error']}")
        else:
            server_name = analysis['server_name'].replace('.', r'\.')
            security_indicators = ', '.join(analysis['security_indicators']).replace('.', r'\.') or 'No detectadas'
            payment_gateways = ', '.join(analysis['payment_gateways']).replace('.', r'\.') or 'No detectadas'
            
            response = f"""Server: {server_name}\nSecurities: {security_indicators}\nPayment Gateways:{payment_gateways}"""
            
            await message.reply(response, parse_mode="MarkdownV2")
    except Exception as e:
        logger.error(f"Error al analizar el sitio: {str(e)}")
        await message.reply("Ocurrió un error al procesar la solicitud. Por favor, intenta de nuevo más tarde.")
  
async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())