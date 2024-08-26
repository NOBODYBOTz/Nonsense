import json
import random
import re
import datetime
from typing import Optional, Dict, Any

class GenerarTarjeta:
    def __init__(self, BIN: str, cantidad: int = 1, solo_impresion: bool = False):
        self._validar_entrada(BIN, cantidad)
        self.ccnum, self.mes, self.ano, self.cvv = self._parse_BIN(BIN)
        self.localidad_bin = "Desconocida"
        self.RONDAS_GEN = 1000
        self.CANTIDAD_TARJETAS = cantidad
        self.lista_tarjetas = []
        self.dic_tarjetas = {}
        
        if self.CANTIDAD_TARJETAS > 0:
            self.generar_tarjetas()
        elif not solo_impresion:
            self.crear_tarjeta()

    def _validar_entrada(self, BIN: str, cantidad: int):
        if not BIN or len(BIN.split('|')[0]) < 6:
            raise ValueError("El BIN debe tener al menos 6 dígitos")
        if cantidad < 1:
            raise ValueError("La cantidad debe ser al menos 1")

    def _parse_BIN(self, BIN: str):
        parts = BIN.split('|')
        return (self._limpiar_datos(parts[i]) if i < len(parts) else None for i in range(4))

    def _limpiar_datos(self, dato: str) -> str:
        return re.sub(r"[^\d]", "", dato)

    def __repr__(self) -> str:
        return "\n".join(f"`{n}`" for n in self.lista_tarjetas)

    def json(self) -> str:
        return json.dumps(self.dic_tarjetas)

    def generar_tarjetas(self):
        for i in range(self.CANTIDAD_TARJETAS):
            tarj_creada = self.crear_tarjeta()
            self.lista_tarjetas.append(tarj_creada["datos_completos"])
            self.dic_tarjetas[i] = tarj_creada

    def _generar_numero_base(self) -> Optional[str]:
        if not self.ccnum:
            return None

        longitud = 15 if self.ccnum[0] == '3' else 16
        return self.ccnum.ljust(longitud - 1, 'x')

    def _calcular_check_digit(self, numero: str) -> int:
        num = [int(d) for d in numero]
        for i in range(-2, -len(num)-1, -2):
            num[i] *= 2
            if num[i] > 9:
                num[i] -= 9
        return (10 - (sum(num) % 10)) % 10

    def luhn_check(self, cc: str) -> bool:
        num = [int(d) for d in cc]
        return sum(num[-1::-2] + [sum(divmod(d * 2, 10)) for d in num[-2::-2]]) % 10 == 0

    def crear_numero(self) -> Optional[str]:
        numero_base = self._generar_numero_base()
        if not numero_base:
            return None

        digitos_faltantes = numero_base.count('x')
        for _ in range(self.RONDAS_GEN):
            numero_parcial = numero_base.replace('x', '{}').format(*[random.randint(0, 9) for _ in range(digitos_faltantes)])
            check_digit = self._calcular_check_digit(numero_parcial)
            numero_final = numero_parcial + str(check_digit)
            if self.luhn_check(numero_final):
                return numero_final
        
        return None  # Si no se pudo generar un número válido

    def generar_fecha_venc(self) -> Dict[str, str]:
        anio_actual = datetime.datetime.now().year
        anio = self.ano or str(random.randint(anio_actual + 1, anio_actual + 5))
        mes = self.mes or str(random.randint(1, 12)).zfill(2)
        return {
            "anio": anio,
            "mes": mes,
            "fecha_completa": f"{mes}|{anio[-2:]}"  # Usar solo los últimos 2 dígitos del año
        }

    def generar_codigo_seguridad(self) -> str:
        longitud = 4 if self.ccnum and self.ccnum[0] == '3' else 3
        if self.cvv:
            cvv = self._limpiar_datos(self.cvv).ljust(longitud, 'x')
            return ''.join(str(random.randint(0, 9)) if ch == 'x' else ch for ch in cvv)[:longitud]
        return str(random.randint(10**(longitud-1), 10**longitud - 1))

    def crear_tarjeta(self) -> Dict[str, Any]:
        """Genera una tarjeta de crédito completa."""
        numero_tarjeta = self.crear_numero()
        if not numero_tarjeta:
            raise ValueError("No se pudo generar un número de tarjeta válido")
        
        fecha_venc = self.generar_fecha_venc()
        codigo_seg = self.generar_codigo_seguridad()
        datos_completos = f"{numero_tarjeta}|{fecha_venc['fecha_completa']}|{codigo_seg}"
        return {
            "numero_tarjeta": numero_tarjeta,
            "venc": fecha_venc['fecha_completa'],
            "codigo_seg": codigo_seg,
            "datos_completos": datos_completos,
        }
