package co.edu.sena.cafeteriapos.modelo;

/**
 * Entidad que representa un producto de la cafeteria Cafetería POS.
 *
 * <p>Es un objeto de transferencia (DTO/entidad) con los atributos minimos de un
 * producto del punto de venta: identificador, nombre, categoria, precio y estado.</p>
 *
 * @author Juan Felipe Lopez Tobon
 * @version 1.0
 */
public class Producto {

    /** Identificador unico del producto. */
    private Long id;

    /** Nombre comercial del producto. */
    private String nombre;

    /** Categoria a la que pertenece el producto. */
    private String categoria;

    /** Precio de venta en pesos. */
    private double precio;

    /** Indica si el producto esta disponible para la venta. */
    private boolean activo;

    /** Constructor vacio requerido por las librerias de persistencia y las vistas. */
    public Producto() {
    }

    /**
     * Crea un producto con todos sus atributos.
     *
     * @param id        identificador del producto (null si aun no se ha guardado)
     * @param nombre    nombre del producto
     * @param categoria categoria del producto
     * @param precio    precio de venta
     * @param activo    estado de disponibilidad
     */
    public Producto(Long id, String nombre, String categoria, double precio, boolean activo) {
        this.id = id;
        this.nombre = nombre;
        this.categoria = categoria;
        this.precio = precio;
        this.activo = activo;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public String getCategoria() {
        return categoria;
    }

    public void setCategoria(String categoria) {
        this.categoria = categoria;
    }

    public double getPrecio() {
        return precio;
    }

    public void setPrecio(double precio) {
        this.precio = precio;
    }

    public boolean isActivo() {
        return activo;
    }

    public void setActivo(boolean activo) {
        this.activo = activo;
    }
}
