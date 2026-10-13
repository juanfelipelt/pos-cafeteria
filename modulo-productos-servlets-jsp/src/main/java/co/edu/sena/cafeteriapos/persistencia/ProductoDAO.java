package co.edu.sena.cafeteriapos.persistencia;

import co.edu.sena.cafeteriapos.modelo.Producto;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

/**
 * Objeto de acceso a datos (DAO) del modulo de productos.
 *
 * <p>Implementa las operaciones de insercion, consulta, actualizacion y eliminacion (CRUD)
 * sobre la tabla {@code producto} usando JDBC y sentencias preparadas.</p>
 *
 * @author Juan Felipe Lopez Tobon
 * @version 1.0
 */
public class ProductoDAO {

    /**
     * Crea la tabla de productos si aun no existe.
     *
     * @throws SQLException si ocurre un error al ejecutar el DDL
     */
    public void crearTabla() throws SQLException {
        String sql = "CREATE TABLE IF NOT EXISTS producto ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                + "nombre TEXT NOT NULL, "
                + "categoria TEXT, "
                + "precio REAL NOT NULL, "
                + "activo INTEGER NOT NULL DEFAULT 1)";
        try (Connection conexion = ConexionBD.getConexion();
             Statement sentencia = conexion.createStatement()) {
            sentencia.execute(sql);
        }
    }

    /**
     * Consulta todos los productos registrados.
     *
     * @return lista de productos ordenada por nombre
     * @throws SQLException si ocurre un error en la consulta
     */
    public List<Producto> listar() throws SQLException {
        List<Producto> productos = new ArrayList<>();
        String sql = "SELECT id, nombre, categoria, precio, activo FROM producto ORDER BY nombre";
        try (Connection conexion = ConexionBD.getConexion();
             PreparedStatement sentencia = conexion.prepareStatement(sql);
             ResultSet resultado = sentencia.executeQuery()) {
            while (resultado.next()) {
                productos.add(mapear(resultado));
            }
        }
        return productos;
    }

    /**
     * Busca un producto por su identificador.
     *
     * @param id identificador del producto
     * @return el producto encontrado o {@code null} si no existe
     * @throws SQLException si ocurre un error en la consulta
     */
    public Producto buscarPorId(long id) throws SQLException {
        String sql = "SELECT id, nombre, categoria, precio, activo FROM producto WHERE id = ?";
        try (Connection conexion = ConexionBD.getConexion();
             PreparedStatement sentencia = conexion.prepareStatement(sql)) {
            sentencia.setLong(1, id);
            try (ResultSet resultado = sentencia.executeQuery()) {
                if (resultado.next()) {
                    return mapear(resultado);
                }
            }
        }
        return null;
    }

    /**
     * Inserta un nuevo producto en la base de datos.
     *
     * @param producto producto a insertar
     * @throws SQLException si ocurre un error al insertar
     */
    public void insertar(Producto producto) throws SQLException {
        String sql = "INSERT INTO producto (nombre, categoria, precio, activo) VALUES (?, ?, ?, ?)";
        try (Connection conexion = ConexionBD.getConexion();
             PreparedStatement sentencia = conexion.prepareStatement(sql)) {
            sentencia.setString(1, producto.getNombre());
            sentencia.setString(2, producto.getCategoria());
            sentencia.setDouble(3, producto.getPrecio());
            sentencia.setInt(4, producto.isActivo() ? 1 : 0);
            sentencia.executeUpdate();
        }
    }

    /**
     * Actualiza un producto existente.
     *
     * @param producto producto con los datos nuevos (debe traer id)
     * @throws SQLException si ocurre un error al actualizar
     */
    public void actualizar(Producto producto) throws SQLException {
        String sql = "UPDATE producto SET nombre = ?, categoria = ?, precio = ?, activo = ? WHERE id = ?";
        try (Connection conexion = ConexionBD.getConexion();
             PreparedStatement sentencia = conexion.prepareStatement(sql)) {
            sentencia.setString(1, producto.getNombre());
            sentencia.setString(2, producto.getCategoria());
            sentencia.setDouble(3, producto.getPrecio());
            sentencia.setInt(4, producto.isActivo() ? 1 : 0);
            sentencia.setLong(5, producto.getId());
            sentencia.executeUpdate();
        }
    }

    /**
     * Elimina un producto por su identificador.
     *
     * @param id identificador del producto a eliminar
     * @throws SQLException si ocurre un error al eliminar
     */
    public void eliminar(long id) throws SQLException {
        String sql = "DELETE FROM producto WHERE id = ?";
        try (Connection conexion = ConexionBD.getConexion();
             PreparedStatement sentencia = conexion.prepareStatement(sql)) {
            sentencia.setLong(1, id);
            sentencia.executeUpdate();
        }
    }

    /**
     * Convierte la fila actual del {@link ResultSet} en un objeto {@link Producto}.
     *
     * @param resultado resultado posicionado en una fila
     * @return el producto mapeado
     * @throws SQLException si ocurre un error al leer las columnas
     */
    private Producto mapear(ResultSet resultado) throws SQLException {
        return new Producto(
                resultado.getLong("id"),
                resultado.getString("nombre"),
                resultado.getString("categoria"),
                resultado.getDouble("precio"),
                resultado.getInt("activo") == 1);
    }
}
