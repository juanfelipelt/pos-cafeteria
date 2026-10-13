"""Servicio de costos fijos (caso de uso: "Gastos fijos del negocio").

¿Qué resuelve?
- Administrar los gastos que no dependen de cuánto se venda (arriendo, luz,
  sueldos, etc.), con su monto mensual y su estado activo/inactivo.

¿Cómo usa los repositorios?
- Recibe un ``CostoFijoRepository`` para crear, listar, actualizar y borrar
  costos fijos.
- Recibe una ``Session`` para confirmar los cambios.

Estos montos alimentan el cálculo del punto de equilibrio en el servicio de
costeo.
"""

from sqlalchemy.orm import Session

from application.utils import new_id
from domain.entities.costo_fijo import CostoFijo
from domain.exceptions import NotFoundError
from domain.repositories.costo_fijo_repository import CostoFijoRepository


class CostoFijoService:
    """Gestiona los costos fijos mensuales del negocio."""

    def __init__(self, costos: CostoFijoRepository, session: Session) -> None:
        """Guarda las dependencias del servicio.

        Parámetros:
            costos: repositorio de costos fijos.
            session: sesión de SQLAlchemy para confirmar cambios.
        """
        self.costos = costos
        self.session = session

    def crear(self, nombre: str, monto: float = 0.0) -> CostoFijo:
        """Crea un costo fijo nuevo.

        Parámetros:
            nombre: descripción del gasto (por ejemplo "Arriendo").
            monto: valor mensual; por defecto 0.

        Retorna:
            El costo fijo creado y confirmado.
        """
        costo = CostoFijo(id=new_id(), nombre=nombre, monto=monto)
        self.costos.add(costo)
        self.session.commit()
        return costo

    def listar(self, solo_activos: bool = False) -> list[CostoFijo]:
        """Lista los costos fijos.

        Parámetros:
            solo_activos: si es ``True``, excluye los inactivos.

        Retorna:
            Lista de costos fijos.
        """
        return self.costos.list(solo_activos)

    def obtener(self, costo_id: str) -> CostoFijo:
        """Busca un costo fijo por id.

        Parámetros:
            costo_id: identificador del costo fijo.

        Retorna:
            El costo fijo encontrado.

        Lanza:
            NotFoundError: si no existe.
        """
        costo = self.costos.get(costo_id)
        if costo is None:
            raise NotFoundError("Costo fijo no encontrado.")
        return costo

    def actualizar(
        self,
        costo_id: str,
        nombre: str | None = None,
        monto: float | None = None,
        activo: bool | None = None,
    ) -> CostoFijo:
        """Actualiza los campos enviados de un costo fijo.

        Solo se modifican los valores que no llegan en ``None``.

        Parámetros:
            costo_id: id del costo fijo a modificar.
            nombre: nuevo nombre (opcional).
            monto: nuevo monto mensual (opcional).
            activo: nuevo estado activo/inactivo (opcional).

        Retorna:
            El costo fijo actualizado.

        Lanza:
            NotFoundError: si no existe.
        """
        costo = self.obtener(costo_id)
        # Se aplica cada cambio solo si el llamador lo envió.
        if nombre is not None:
            costo.cambiar_nombre(nombre)
        if monto is not None:
            costo.cambiar_monto(monto)
        if activo is not None:
            # Delegamos en los métodos de la entidad para activar/desactivar.
            if activo:
                costo.activar()
            else:
                costo.desactivar()
        self.costos.update(costo)
        self.session.commit()
        return costo

    def eliminar(self, costo_id: str) -> None:
        """Elimina un costo fijo.

        Parámetros:
            costo_id: id del costo fijo a eliminar.

        Lanza:
            NotFoundError: si no existe.
        """
        # Se valida la existencia primero para dar un error claro.
        self.obtener(costo_id)
        self.costos.delete(costo_id)
        self.session.commit()
