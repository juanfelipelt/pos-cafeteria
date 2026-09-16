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
    def test_nombre_obligatorio(self):
        with pytest.raises(ValueError):
            Producto(nombre="   ")

    def test_precio_negativo(self):
        with pytest.raises(ValueError):
            Producto(nombre="Cafe", precio=-1)

    def test_stock_negativo(self):
        with pytest.raises(ValueError):
            Producto(nombre="Cafe", stock=-1)

    def test_esta_disponible(self):
        assert Producto(nombre="Cafe", stock=5, estado=True).esta_disponible
        assert not Producto(nombre="Cafe", stock=0, estado=True).esta_disponible
        assert not Producto(nombre="Cafe", stock=5, estado=False).esta_disponible


class TestVenta:
    def _detalle(self):
        return DetalleVenta(
            producto_id="p1", nombre_producto="Cafe", cantidad=2, precio_unitario=1.5
        )

    def test_total(self):
        v = Venta(detalles=[self._detalle()])
        assert v.total == 3.0

    def test_registrar_pago_y_pendiente(self):
        v = Venta(detalles=[self._detalle()])
        v.registrar_pago(Pago(monto=1.0, metodo=MetodoPago.EFECTIVO))
        assert v.total_pagado == 1.0
        assert v.pendiente == 2.0
        assert not v.esta_pagada

    def test_rechaza_sobrepago(self):
        v = Venta(detalles=[self._detalle()])
        with pytest.raises(ValueError):
            v.registrar_pago(Pago(monto=5.0, metodo=MetodoPago.EFECTIVO))

    def test_anular_dos_veces(self):
        v = Venta(detalles=[self._detalle()])
        v.anular()
        with pytest.raises(ValueError):
            v.anular()

    def test_sin_detalles(self):
        with pytest.raises(ValueError):
            Venta(detalles=[])


class TestCompra:
    def test_total_y_anular(self):
        detalle = DetalleCompra(
            tipo="producto",
            producto_id="p1",
            nombre_producto="Cafe",
            cantidad=10,
            precio_unitario=1.0,
        )
        c = Compra(proveedor_id="prov1", detalles=[detalle])
        assert c.total == 10.0
        c.anular()
        assert c.anulada

    def test_detalle_insumo(self):
        detalle = DetalleCompra(
            tipo="insumo",
            insumo_id="i1",
            nombre_insumo="Azucar",
            cantidad=2.5,
            precio_unitario=3.0,
        )
        assert detalle.nombre == "Azucar"
        assert detalle.subtotal == 7.5


class TestUsuario:
    def test_es_admin(self):
        assert Usuario(
            nombre="A", email="a@x.com", contraseña_hash="h", rol=Rol.ADMIN
        ).es_admin
        assert not Usuario(
            nombre="A", email="a@x.com", contraseña_hash="h", rol=Rol.CAJERO
        ).es_admin

    def test_to_dict_no_expone_hash(self):
        u = Usuario(nombre="A", email="a@x.com", contraseña_hash="secreto")
        assert "contraseña_hash" not in u.to_dict()


class TestNota:
    def test_texto_obligatorio(self):
        with pytest.raises(ValueError):
            Nota(texto="   ")

    def test_tipo_invalido(self):
        with pytest.raises(ValueError):
            Nota(texto="x", tipo="otro")

    def test_pendiente(self):
        assert Nota(texto="x", tipo="tarea").pendiente
        assert not Nota(texto="x", tipo="tarea", hecho=True).pendiente
        assert Nota(texto="x", tipo="nota").pendiente
        n = Nota(texto="x", tipo="nota")
        n.archivar()
        assert not n.pendiente


class TestPago:
    def test_metodo_desde_string(self):
        p = Pago(monto=1.0, metodo="tarjeta")
        assert p.metodo == MetodoPago.TARJETA

    def test_metodo_invalido(self):
        with pytest.raises(ValueError):
            Pago(monto=1.0, metodo="bitcoin")

    def test_monto_invalido(self):
        with pytest.raises(ValueError):
            Pago(monto=0, metodo=MetodoPago.EFECTIVO)
