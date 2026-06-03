import re

from django.core.exceptions import ValidationError


RUT_PATTERN = re.compile(r"^(\d{1,2}\.\d{3}\.\d{3}|\d{7,8})-[\dkK]$")
PHONE_PATTERN = re.compile(r"^(\+56)?9\d{8}$")


def normalizar_rut(rut):
    return rut.strip().replace(".", "").replace("-", "").upper()


def formatear_rut_sin_puntos(rut):
    normalized = normalizar_rut(rut)
    return f"{normalized[:-1]}-{normalized[-1]}"


def formatear_telefono_con_codigo_pais(telefono):
    normalized = telefono.strip().replace(" ", "").replace("-", "")
    if normalized.startswith("+56"):
        return normalized
    return f"+56{normalized}"


def validar_rut_chileno(rut):
    if not rut or not RUT_PATTERN.match(rut.strip()):
        raise ValidationError("El RUT debe tener formato 12.345.678-9 o 12345678-9.")

    normalized = normalizar_rut(rut)
    body = normalized[:-1]
    check_digit = normalized[-1]

    reversed_digits = map(int, reversed(body))
    factors = [2, 3, 4, 5, 6, 7]
    total = sum(digit * factors[index % len(factors)] for index, digit in enumerate(reversed_digits))
    expected_value = 11 - (total % 11)

    if expected_value == 11:
        expected = "0"
    elif expected_value == 10:
        expected = "K"
    else:
        expected = str(expected_value)

    if check_digit != expected:
        raise ValidationError("El digito verificador del RUT no es valido.")


def validar_telefono_chileno(telefono):
    if not telefono or not PHONE_PATTERN.match(telefono.strip()):
        raise ValidationError("El telefono debe tener formato 912345678 o +56912345678.")
