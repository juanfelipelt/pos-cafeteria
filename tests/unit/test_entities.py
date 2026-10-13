"""Pruebas unitarias de las ENTIDADES del dominio.

Las entidades son las clases que representan los conceptos del negocio
(Producto, Venta, Compra, Usuario, Nota, Pago). Aquí verificamos que sus reglas
de negocio se cumplan SIN base de datos ni API: construimos objetos en memoria y
comprobamos cálculos, validaciones y errores esperados.

Se usa pytest.raises(ValueError) para confirmar que las entidades rechazan
datos inválidos (nombre vacío, precio negativo, sobrepago, etc.).
"""

import pytest

from domain.entities.compra import Compra
from domain.entities.detalle_compra import DetalleCompra
from domain.entities.detalle_venta import DetalleVenta
from domain.entities.enums import MetodoPago, Rol
from domain.entities.nota import Nota
from domain.entities.pago import Pago
from domain.entities.producto import Producto
from domain.entities.usuario import Usuario
from domain.entities.venta import Venta


class TestProducto:
    """Prueba las validaciones y la disponibilidad de la entidad Producto."""

    def test_nombre_obligatorio(self):
        """Un producto sin nombre (o solo espacios) debe lanzar ValueError."""
        # act + assert: crear con nombre en blanco debe fallar.
        with pytest.raises(ValueError):
            Producto(nombre="   ")

    def test_precio_negativo(self):
        """El precio no puede ser negativo."""
        # act + assert: un precio negativo no es válido.
        with pytest.raises(ValueError):
            Producto(nombre="Cafe", precio=-1)

    def test_stock_negativo(self):
        """El stock (cantidad disponible) no puede ser negativo."""
        # act + assert: un stock negativo no es válido.
        with pytest.raises(ValueError):
            Producto(nombre="Cafe", stock=-1)

    def test_esta_disponible(self):
        """Un producto está disponible solo si tiene stock>0 y estado=True."""
        # assert: con stock y activo -> disponible.
        assert Producto(nombre="Cafe", stock=5, estado=True).esta_disponible
        # assert: sin stock -> no disponible.
        assert not Producto(nombre="Cafe", stock=0, estado=True).esta_disponible
        # assert: inactivo -> no disponible aunque tenga stock.
        assert not Producto(nombre="Cafe", stock=5, estado=False).esta_disponible


class TestVenta:
    """Prueba los totales, pagos y la anulación de la entidad Venta."""

    def _detalle(self):
        """Helper: crea un detalle de venta reutilizable (2 cafés a 1.5)."""
        return DetalleVenta(
            producto_id="p1", nombre_producto="Cafe", cantidad=2, precio_unitario=1.5
        )

    def test_total(self):
        """El total es la suma de cantidad × precio de sus detalles (2×1.5=3.0)."""
        # arrange: una venta con un solo detalle.
        v = Venta(detalles=[self._detalle()])
        # assert: el total se calcula automáticamente.
        assert v.total == 3.0

    def test_registrar_pago_y_pendiente(self):
        """Registrar un pago parcial actualiza total_pagado, pendiente y esta_pagada."""
        # arrange: venta de 3.0 y pago parcial de 1.0.
        v = Venta(detalles=[self._detalle()])
        # act: registramos el pago.
        v.registrar_pago(Pago(monto=1.0, metodo=MetodoPago.EFECTIVO))
        # assert: pagado 1.0, pendiente 2.0 y todavía no está totalmente pagada.
        assert v.total_pagado == 1.0
        assert v.pendiente == 2.0
        assert not v.esta_pagada

    def test_rechaza_sobrepago(self):
        """No se puede pagar más que el total de la venta."""
        # arrange: venta de 3.0.
        v = Venta(detalles=[self._detalle()])
        # act + assert: pagar 5.0 (más que el total) debe fallar.
        with pytest.raises(ValueError):
            v.registrar_pago(Pago(monto=5.0, metodo=MetodoPago.EFECTIVO))

    def test_anular_dos_veces(self):
        """Una venta ya anulada no puede volver a anularse."""
        # arrange: venta válida.
        v = Venta(detalles=[self._detalle()])
        # act: la anulamos una vez.
        v.anular()
        # act + assert: anular de nuevo debe fallar.
        with pytest.raises(ValueError):
            v.anular()

    def test_sin_detalles(self):
        """Una venta sin detalles no es válida."""
        # act + assert: crear una venta vacía debe fallar.
        with pytest.raises(ValueError):
            Venta(detalles=[])


class TestCompra:
    """Prueba el total, la anulación y los detalles de la entidad Compra."""

    def test_total_y_anular(self):
        """El total suma los subtotales y anular() marca la compra como anulada."""
        # arrange: compra de 10 unidades a 1.0 => total 10.0.
        detalle = DetalleCompra(
            tipo="producto",
            producto_id="p1",
            nombre_producto="Cafe",
            cantidad=10,
            precio_unitario=1.0,
        )
        c = Compra(proveedor_id="prov1", detalles=[detalle])
        # assert: el total se calcula correctamente.
        assert c.total == 10.0
        # act: anulamos la compra.
        c.anular()
        # assert: queda marcada como anulada.
        assert c.anulada

    def test_detalle_insumo(self):
        """Un detalle de tipo insumo expone su nombre y subtotal (2.5×3=7.5)."""
        # arrange: detalle de insumo (azúcar).
        detalle = DetalleCompra(
            tipo="insumo",
            insumo_id="i1",
            nombre_insumo="Azucar",
            cantidad=2.5,
            precio_unitario=3.0,
        )
        # assert: nombre y subtotal correctos.
        assert detalle.nombre == "Azucar"
        assert detalle.subtotal == 7.5


class TestUsuario:
    """Prueba el rol de administrador y la seguridad de la entidad Usuario."""

    def test_es_admin(self):
        """es_admin es True solo cuando el rol es ADMIN."""
        # assert: rol ADMIN -> es admin.
        assert Usuario(
            nombre="A", email="a@x.com", contraseña_hash="h", rol=Rol.ADMIN
        ).es_admin
        # assert: rol CAJERO -> no es admin.
        assert not Usuario(
            nombre="A", email="a@x.com", contraseña_hash="h", rol=Rol.CAJERO
        ).es_admin

    def test_to_dict_no_expone_hash(self):
        """to_dict() no debe incluir el hash de la contraseña (seguridad)."""
        # arrange: usuario con un hash "secreto".
        u = Usuario(nombre="A", email="a@x.com", contraseña_hash="secreto")
        # assert: el diccionario exportado no filtra el hash.
        assert "contraseña_hash" not in u.to_dict()


class TestNota:
    """Prueba las validaciones y el estado 'pendiente' de la entidad Nota."""

    def test_texto_obligatorio(self):
        """Una nota con texto vacío (solo espacios) no es válida."""
        # act + assert: crear con texto en blanco debe fallar.
        with pytest.raises(ValueError):
            Nota(texto="   ")

    def test_tipo_invalido(self):
        """El tipo debe ser 'tarea' o 'nota'; cualquier otro valor falla."""
        # act + assert: un tipo desconocido no es válido.
        with pytest.raises(ValueError):
            Nota(texto="x", tipo="otro")

    def test_pendiente(self):
        """Una tarea pendiente lo está mientras no esté hecha; las notas también."""
        # assert: tarea sin hecho -> pendiente.
        assert Nota(texto="x", tipo="tarea").pendiente
        # assert: tarea hecha -> ya no pendiente.
        assert not Nota(texto="x", tipo="tarea", hecho=True).pendiente
        # assert: una nota normal también está pendiente.
        assert Nota(texto="x", tipo="nota").pendiente
        # arrange: creamos una nota y la archivamos.
        n = Nota(texto="x", tipo="nota")
        n.archivar()
        # assert: una nota archivada deja de estar pendiente.
        assert not n.pendiente


class TestPago:
    """Prueba la validación del método y del monto en la entidad Pago."""

    def test_metodo_desde_string(self):
        """El método de pago se puede pasar como texto ('tarjeta') y se convierte."""
        # arrange: creamos el pago con el método como string.
        p = Pago(monto=1.0, metodo="tarjeta")
        # assert: se convirtió al valor del enum.
        assert p.metodo == MetodoPago.TARJETA

    def test_metodo_invalido(self):
        """Un método de pago desconocido lanza ValueError."""
        # act + assert: "bitcoin" no es un método válido.
        with pytest.raises(ValueError):
            Pago(monto=1.0, metodo="bitcoin")

    def test_monto_invalido(self):
        """Un pago de monto 0 (o negativo) no es válido."""
        # act + assert: monto cero debe fallar.
        with pytest.raises(ValueError):
            Pago(monto=0, metodo=MetodoPago.EFECTIVO)
