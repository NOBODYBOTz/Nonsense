import requests
import time
import base64
import sys
from typing import Dict, Any, Optional
from api_key import client_key

class AntiCaptchaClient:
    def __init__(self, client_key: str):
        self.host = "api.anti-captcha.com"
        self.scheme = "https"
        self.client_key = client_key
        self.verbose_mode = False
        self.task_id: Optional[int] = None
        self.task_info: Optional[Dict[str, Any]] = None

    def create_task(self, task_data: Dict[str, Any]) -> bool:
        endpoint = f"{self.scheme}://{self.host}/createTask"
        payload = {
            "clientKey": self.client_key,
            "task": task_data
        }
        response = self._make_request(endpoint, payload)
        if response and response.get("errorId") == 0:
            self.task_id = response.get("taskId")
            self._debout(f"Tarea creada con ID {self.task_id}", "yellow")
            return True
        else:
            self._debout(f"Error de API {response.get('errorCode')} : {response.get('errorDescription')}", "red")
            return False

    def wait_for_result(self, max_seconds: int = 300) -> Optional[Dict[str, Any]]:
        if not self.task_id:
            return None
        
        endpoint = f"{self.scheme}://{self.host}/getTaskResult"
        start_time = time.time()
        while time.time() - start_time < max_seconds:
            payload = {
                "clientKey": self.client_key,
                "taskId": self.task_id
            }
            response = self._make_request(endpoint, payload)
            if response and response.get("status") == "ready":
                self.task_info = response
                self._debout("Tarea completada", "green")
                return response.get("solution")
            elif response and response.get("status") == "processing":
                self._debout("La tarea aún está en proceso")
                time.sleep(5)
            else:
                self._debout(f"Error de API {response.get('errorCode')} : {response.get('errorDescription')}", "red")
                return None
        self._debout("Tiempo de espera agotado", "red")
        return None

    def get_balance(self) -> Optional[float]:
        endpoint = f"{self.scheme}://{self.host}/getBalance"
        payload = {"clientKey": self.client_key}
        response = self._make_request(endpoint, payload)
        if response and response.get("errorId") == 0:
            return response.get("balance")
        return None

    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if self.verbose_mode:
                print(f"Error en la solicitud: {e}")
            return None

    def set_verbose_mode(self, mode: bool):
        self.verbose_mode = mode

    def _debout(self, message: str, color: str = "white"):
        if not self.verbose_mode:
            return
        CLIcolors = {
            "cyan": "\033[0;36m",
            "green": "\033[0;32m",
            "blue": "\033[0;34m",
            "red": "\033[0;31m",
            "yellow": "\033[1;33m",
            "white": "\033[0m"
        }
        print(f"{CLIcolors.get(color, CLIcolors['white'])}{message}\033[0m")

def image_to_base64(image_path: str) -> str:
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except IOError as e:
        print(f"Error al leer la imagen: {e}")
        sys.exit(1)

def main():
    try:
        client = AntiCaptchaClient(client_key)
        client.set_verbose_mode(True)

        print("Selecciona el tipo de captcha que deseas resolver:")
        print("1. Captcha de imagen")
        print("2. reCAPTCHA v2")
        print("3. hCaptcha")

        option = input("Introduce el número de la opción: ")

        if option == "1":
            image_path = input("Introduce la ruta de la imagen del captcha: ")
            image_base64 = image_to_base64(image_path)
            task_data = {
                "type": "ImageToTextTask",
                "body": image_base64
            }
        elif option == "2":
            website_url = input("Introduce la URL del sitio web: ")
            website_key = input("Introduce la clave del sitio web: ")
            task_data = {
                "type": "NoCaptchaTaskProxyless",
                "websiteURL": website_url,
                "websiteKey": website_key
            }
        elif option == "3":
            website_url = input("Introduce la URL del sitio web: ")
            website_key = input("Introduce la clave del sitio web: ")
            task_data = {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": website_url,
                "websiteKey": website_key
            }
        else:
            print("Opción no válida.")
            return

        if client.create_task(task_data):
            result = client.wait_for_result()
            if result:
                print("Resultado:", result)
            else:
                print("No se pudo obtener el resultado.")
        else:
            print("No se pudo crear la tarea.")

        balance = client.get_balance()
        if balance is not None:
            print(f"Saldo: {balance:.2f}")
        else:
            print("No se pudo obtener el saldo.")

    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()