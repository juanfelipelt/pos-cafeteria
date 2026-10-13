"""Seguridad: hashing de contraseñas.

Este módulo convierte una contraseña en texto plano (la que escribe el usuario)
en un "hash" seguro que se guarda en la base de datos, y permite verificar
después si una contraseña coincide con ese hash.

¿Por qué hashear?
- Nunca se guardan contraseñas en texto plano.
- Si alguien accede a la base de datos, solo verá hashes irreversibles.

¿Cómo se hace?
- Se usa PBKDF2-HMAC-SHA256 con una "sal" (salt) aleatoria por usuario y
  muchas iteraciones, lo que hace muy costoso probar contraseñas por fuerza
  bruta.
- La verificación usa comparación en tiempo constante para evitar ataques de
  temporización.

Formato del hash guardado: pbkdf2_sha256$<iteraciones>$<salt>$<digest>
Se mantiene compatibilidad con un formato antiguo (solo salt$digest) que usaba
menos iteraciones.
"""

import hashlib
import hmac
import os

# Iteraciones actuales recomendadas para PBKDF2.
_ITERATIONS = 260_000
# Iteraciones del formato antiguo; se aceptan al verificar por compatibilidad.
_LEGACY_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """Genera un hash seguro a partir de la contraseña en texto plano.

    Devuelve una cadena con el formato pbkdf2_sha256$iteraciones$salt$digest.
    """
    # Sal aleatoria de 16 bytes, distinta para cada contraseña.
    salt = os.urandom(16)
    # Derivamos la clave con PBKDF2-HMAC-SHA256.
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS
    )
    # Empaquetamos todo en texto para poder guardarlo en la base de datos.
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Comprueba si `password` corresponde al hash `hashed`.

    Acepta tanto el formato nuevo (4 partes) como el antiguo (2 partes).
    Retorna False ante cualquier hash inválido o corrupto.
    """
    # El separador "$" divide las partes del hash.
    parts = hashed.split("$")
    try:
        if len(parts) == 2:
            # Formato antiguo: <salt>$<digest>, con las iteraciones heredadas.
            salt_hex, digest_hex = parts
            iterations = _LEGACY_ITERATIONS
        elif len(parts) == 4:
            # Formato nuevo: pbkdf2_sha256$<iter>$<salt>$<digest>.
            _, iter_str, salt_hex, digest_hex = parts
            iterations = int(iter_str)
        else:
            # Formato desconocido: no se puede verificar.
            return False
        # Convertimos de hexadecimal a bytes.
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        # Si el hash viene corrupto (hex inválido, iter no numérica...),
        # consideramos que la verificación falló.
        return False

    # Recalculamos el hash con la sal y las iteraciones detectadas.
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    # Comparación en tiempo constante: evita filtrar información por tiempos.
    return hmac.compare_digest(digest, expected)
