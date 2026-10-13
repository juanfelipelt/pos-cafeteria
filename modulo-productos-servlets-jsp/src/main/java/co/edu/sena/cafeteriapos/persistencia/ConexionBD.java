package co.edu.sena.cafeteriapos.persistencia;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

/**
 * Clase utilitaria que centraliza la conexion JDBC con la base de datos del proyecto Cafetería POS.
 *
 * <p>Se usa el patron de fabrica simple: todas las clases DAO obtienen su conexion a traves
 * de {@link #getConexion()}, evitando repetir la cadena de conexion en cada consulta.</p>
 *
 * @author Juan Felipe Lopez Tobon
 * @version 1.0
 */
public final class ConexionBD {

    /** Cadena de conexion JDBC contra el archivo de base de datos SQLite del proyecto. */
    private static final String URL = "jdbc:sqlite:pos-cafeteria.db";

    /** Constructor privado: esta clase solo expone metodos estaticos. */
    private ConexionBD() {
    }

    /**
     * Abre una conexion JDBC contra la base de datos.
     *
     * @return la conexion lista para ejecutar sentencias SQL
     * @throws SQLException si no es posible establecer la conexion
     */
    public static Connection getConexion() throws SQLException {
        return DriverManager.getConnection(URL);
    }
}
