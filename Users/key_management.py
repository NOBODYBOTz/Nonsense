from typing import Dict, Union
from datetime import datetime, timedelta
import random
import string
from Users.users_management import add_credits, update_plan, get_user

# Almacenamiento de claves (en memoria para este ejemplo)
keys_db: Dict[str, Dict[str, Union[str, int, datetime]]] = {}

def generate_key(reward_type: str, value: int, expiration_days: int = 30) -> str:
    """Genera una clave única con una recompensa específica."""
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    expiration_date = datetime.now() + timedelta(days=expiration_days)
    
    keys_db[key] = {
        "reward_type": reward_type,
        "value": value,
        "expiration_date": expiration_date
    }
    
    return key

def validate_and_use_key(user_id: int, key: str) -> Union[str, None]:
    """Valida y usa una clave, aplicando la recompensa al usuario."""
    if key not in keys_db:
        return None
    
    key_data = keys_db[key]
    if datetime.now() > key_data["expiration_date"]:
        del keys_db[key]
        return None
    
    reward_type = key_data["reward_type"]
    value = key_data["value"]
    
    if reward_type == "credits":
        if add_credits(user_id, value):
            del keys_db[key]
            return f"Se han añadido {value} créditos a tu cuenta."
    elif reward_type == "days":
        user = get_user(user_id)
        if user:
            current_plan = user.get('plan')
            if current_plan:
                if update_plan(user_id, current_plan, value):
                    del keys_db[key]
                    return f"Se han añadido {value} días a tu plan actual ({current_plan})."
                else:
                    return "No se pudo actualizar tu plan. Por favor, contacta al administrador."
            else:
                return "No tienes un plan activo. Por favor, contacta al administrador."
        else:
            return "No se pudo encontrar tu información de usuario."
    
    return None

def get_all_keys() -> Dict[str, Dict[str, Union[str, int, datetime]]]:
    """Devuelve todas las claves activas."""
    return keys_db