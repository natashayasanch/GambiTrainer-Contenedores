import math


def _a_numero(valor, etiqueta):
    """Convierte un texto o número en float.

    Acepta coma o punto decimal ("0,5" y "0.5"). Lanza ValueError con un
    mensaje claro si no es un número válido (rechaza también nan e inf).
    """
    if isinstance(valor, str):
        valor = valor.strip().replace(",", ".")
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{etiqueta} debe ser un número, por ejemplo 0,5")
    if not math.isfinite(numero):
        raise ValueError(f"{etiqueta} debe ser un número válido")
    return numero


class ActivoFinanciero:
    """Representa una criptomoneda del portafolio del usuario.

    Guarda los datos básicos del activo (nombre, símbolo, cantidad y precio)
    y valida los valores cuando se modifican mediante los setters.
    """

    def __init__(self, id, nombre, simbolo, cantidad, precio):
        self._id = id
        self.set_nombre(nombre)
        self.set_simbolo(simbolo)
        self.set_cantidad(cantidad)
        self.set_precio(precio)

    # ---------- Getters ----------
    def get_id(self):
        return self._id

    def get_nombre(self):
        return self._nombre

    def get_simbolo(self):
        return self._simbolo

    def get_cantidad(self):
        return self._cantidad

    def get_precio(self):
        return self._precio

    # ---------- Setters (con validación) ----------
    def set_nombre(self, nombre):
        """Cambia el nombre. Lanza ValueError si está vacío o es muy largo."""
        nombre = str(nombre).strip()
        if nombre == "":
            raise ValueError("El nombre no puede estar vacío")
        if len(nombre) > 50:
            raise ValueError("El nombre no puede superar los 50 caracteres")
        self._nombre = nombre

    def set_simbolo(self, simbolo):
        """Cambia el símbolo (siempre en mayúsculas). Lanza ValueError si está vacío."""
        simbolo = str(simbolo).strip()
        if simbolo == "":
            raise ValueError("El símbolo no puede estar vacío")
        if len(simbolo) > 10:
            raise ValueError("El símbolo no puede superar los 10 caracteres")
        self._simbolo = simbolo.upper()

    def set_cantidad(self, cantidad):
        """Comprueba que la cantidad sea un número mayor que cero."""
        cantidad = _a_numero(cantidad, "La cantidad")
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        self._cantidad = cantidad

    def set_precio(self, precio):
        """Comprueba que el precio sea un número mayor que cero."""
        precio = _a_numero(precio, "El precio")
        if precio <= 0:
            raise ValueError("El precio debe ser mayor que cero")
        self._precio = precio

    # ---------- Métodos auxiliares ----------
    def calcular_valor_total(self):
        """Devuelve lo que vale esta posición (cantidad por precio)."""
        return self._cantidad * self._precio

    def a_diccionario(self):
        """Convierte el objeto en diccionario para poder guardarlo en la session."""
        return {
            "id": self._id,
            "nombre": self._nombre,
            "simbolo": self._simbolo,
            "cantidad": self._cantidad,
            "precio": self._precio,
        }


def crear_desde_diccionario(datos):
    """Reconstruye un ActivoFinanciero a partir de un diccionario de la session."""
    return ActivoFinanciero(
        datos["id"],
        datos["nombre"],
        datos["simbolo"],
        datos["cantidad"],
        datos["precio"],
    )