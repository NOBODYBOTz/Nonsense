import json
from datetime import datetime, timedelta
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserCache:
    def __init__(self):
        self.users = None
        self.last_load = None

    def get_users(self):
        if self.users is None or (datetime.now() - self.last_load).total_seconds() > 300:  # 5 minutos
            self.users = load_users()
            self.last_load = datetime.now()
        return self.users

    def save_users(self):
        save_users(self.users)
        self.last_load = datetime.now()

user_cache = UserCache()
user_lock = threading.Lock()

def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Archivo users.json no encontrado. Creando nuevo diccionario.")
        return {}
    except json.JSONDecodeError:
        logger.error("Error al decodificar users.json. Archivo corrupto.")
        raise

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4, default=str)

def get_user(user_id):
    users = user_cache.get_users()
    return users.get(str(user_id))

def add_premium_user(user_id, plan, dias):
    if not isinstance(dias, int) or dias <= 0:
        raise ValueError("Los días deben ser un número entero positivo.")
    if not isinstance(plan, str) or not plan:
        raise ValueError("El plan debe ser una cadena no vacía.")
    
    with user_lock:
        users = user_cache.get_users()
        tiempo_restante = (datetime.now() + timedelta(days=dias)).isoformat()
        users[str(user_id)] = {
            "plan": plan,
            "tiempo_restante": tiempo_restante,
            "creditos": 0
        }
        user_cache.save_users()
        logger.info(f"Usuario premium añadido: {user_id}")

def remove_premium_user(user_id):
    with user_lock:
        users = user_cache.get_users()
        if str(user_id) in users:
            del users[str(user_id)]
            user_cache.save_users()
            logger.info(f"Usuario premium eliminado: {user_id}")

def update_plan(user_id, new_plan, dias_adicionales):
    if not isinstance(dias_adicionales, int):
        raise ValueError("Los días adicionales deben ser un número entero.")
    if new_plan is not None and (not isinstance(new_plan, str) or not new_plan):
        raise ValueError("El nuevo plan debe ser una cadena no vacía o None.")

    with user_lock:
        users = user_cache.get_users()
        user = users.get(str(user_id))
        if user:
            tiempo_actual = datetime.fromisoformat(user['tiempo_restante'])
            nuevo_tiempo = tiempo_actual + timedelta(days=dias_adicionales)
            
            # Asegurarse de que el nuevo tiempo no sea anterior a la fecha actual
            if nuevo_tiempo < datetime.now():
                nuevo_tiempo = datetime.now()
            
            users[str(user_id)] = {
                "plan": new_plan if new_plan is not None else user['plan'],
                "tiempo_restante": nuevo_tiempo.isoformat(),
                "creditos": user.get('creditos', 0)
            }
            user_cache.save_users()
            logger.info(f"Plan actualizado para el usuario: {user_id}. Días ajustados: {dias_adicionales}")
            return True
        else:
            logger.warning(f"Usuario no encontrado: {user_id}")
            return False

def add_credits(user_id, credits):
    if not isinstance(credits, int) or credits <= 0:
        raise ValueError("Los créditos deben ser un número entero positivo.")

    def update(user):
        user['creditos'] = user.get('creditos', 0) + credits
    return update_user(user_id, update)

def update_user(user_id, update_func):
    with user_lock:
        users = user_cache.get_users()
        user = users.get(str(user_id))
        if user:
            update_func(user)
            user_cache.save_users()
            logger.info(f"Usuario actualizado: {user_id}")
            return True
    logger.warning(f"Usuario no encontrado: {user_id}")
    return False

def is_premium_user(user_id):
    user = get_user(user_id)
    if user and 'tiempo_restante' in user:
        tiempo_restante = datetime.fromisoformat(user['tiempo_restante'])
        return tiempo_restante > datetime.now()
    return False

# Función auxiliar para limpiar usuarios expirados (puede ejecutarse periódicamente)
def clean_expired_users():
    users = load_users()
    current_time = datetime.now()
    expired_users = [
        user_id for user_id, user_data in users.items()
        if datetime.fromisoformat(user_data['tiempo_restante']) <= current_time
    ]
    for user_id in expired_users:
        del users[user_id]
    save_users(users)
    return len(expired_users)

# Ejemplo de uso:
if __name__ == "__main__":
    try:
        add_premium_user("123", "plan_basico", 30)
        print(get_user("123"))
        add_credits("123", 100)
        print(get_user("123"))
        update_plan("123", "plan_avanzado", 60)
        print(get_user("123"))
        print(f"¿Es usuario premium? {is_premium_user('123')}")
        remove_premium_user("123")
        print(get_user("123"))
    except Exception as e:
        logger.error(f"Error en la ejecución: {str(e)}")