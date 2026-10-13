package co.edu.sena.cafeteriapos.web;

import co.edu.sena.cafeteriapos.modelo.Producto;
import co.edu.sena.cafeteriapos.persistencia.ProductoDAO;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.sql.SQLException;
import java.util.List;

/**
 * Servlet que atiende el modulo de productos del sistema Cafetería POS.
 *
 * <p>Recibe las peticiones del formulario HTML y de los enlaces de la vista, ejecuta la
 * operacion correspondiente sobre la base de datos (a traves de {@link ProductoDAO}) y
 * redirige o reenvia a las vistas JSP.</p>
 *
 * <p>Operaciones soportadas:</p>
 * <ul>
 *   <li>GET  {@code /productos}                     -> lista los productos</li>
 *   <li>GET  {@code /productos?accion=nuevo}        -> muestra el formulario vacio</li>
 *   <li>GET  {@code /productos?accion=editar&id=N}  -> muestra el formulario con datos</li>
 *   <li>GET  {@code /productos?accion=eliminar&id=N}-> elimina el producto</li>
 *   <li>POST {@code /productos} (accion=guardar)    -> inserta o actualiza un producto</li>
 * </ul>
 *
 * @author Juan Felipe Lopez Tobon
 * @version 1.0
 */
@WebServlet(name = "ProductoServlet", urlPatterns = {"/productos"})
public class ProductoServlet extends HttpServlet {

    /** DAO que encapsula el acceso a datos del modulo de productos. */
    private final ProductoDAO productoDAO = new ProductoDAO();

    /**
     * Inicializa el servlet creando la tabla de productos si no existe.
     *
     * @throws ServletException si ocurre un error de base de datos al inicializar
     */
    @Override
    public void init() throws ServletException {
        try {
            productoDAO.crearTabla();
        } catch (SQLException e) {
            throw new ServletException("No se pudo inicializar el modulo de productos", e);
        }
    }

    /**
     * Atiende las peticiones GET: listar, mostrar formulario (nuevo/editar) y eliminar.
     *
     * @param request  peticion del cliente
     * @param response respuesta hacia el cliente
     * @throws ServletException si ocurre un error en el servlet
     * @throws IOException      si ocurre un error de entrada/salida
     */
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String accion = request.getParameter("accion");
        if (accion == null) {
            accion = "listar";
        }
        try {
            switch (accion) {
                case "nuevo":
                    mostrarFormulario(request, response, new Producto());
                    break;
                case "editar":
                    editar(request, response);
                    break;
                case "eliminar":
                    eliminar(request, response);
                    break;
                case "listar":
                default:
                    listar(request, response);
                    break;
            }
        } catch (SQLException e) {
            throw new ServletException("Error al procesar la peticion GET", e);
        }
    }

    /**
     * Atiende las peticiones POST del formulario: guardar (insertar o actualizar).
     *
     * @param request  peticion del cliente con los datos del formulario
     * @param response respuesta hacia el cliente
     * @throws ServletException si ocurre un error en el servlet
     * @throws IOException      si ocurre un error de entrada/salida
     */
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String accion = request.getParameter("accion");
        try {
            if ("guardar".equals(accion)) {
                guardar(request);
                response.sendRedirect(request.getContextPath() + "/productos");
            } else {
                response.sendRedirect(request.getContextPath() + "/productos");
            }
        } catch (SQLException e) {
            throw new ServletException("Error al guardar el producto", e);
        }
    }

    /**
     * Consulta los productos y los envia a la vista de lista.
     */
    private void listar(HttpServletRequest request, HttpServletResponse response)
            throws SQLException, ServletException, IOException {
        List<Producto> productos = productoDAO.listar();
        request.setAttribute("productos", productos);
        request.getRequestDispatcher("/WEB-INF/vistas/productos/lista.jsp").forward(request, response);
    }

    /**
     * Carga un producto existente y lo envia a la vista del formulario.
     */
    private void editar(HttpServletRequest request, HttpServletResponse response)
            throws SQLException, ServletException, IOException {
        long id = Long.parseLong(request.getParameter("id"));
        Producto producto = productoDAO.buscarPorId(id);
        if (producto == null) {
            response.sendRedirect(request.getContextPath() + "/productos");
            return;
        }
        mostrarFormulario(request, response, producto);
    }

    /**
     * Reenvia a la vista del formulario con el producto indicado.
     */
    private void mostrarFormulario(HttpServletRequest request, HttpServletResponse response, Producto producto)
            throws ServletException, IOException {
        request.setAttribute("producto", producto);
        request.getRequestDispatcher("/WEB-INF/vistas/productos/formulario.jsp").forward(request, response);
    }

    /**
     * Elimina el producto indicado y redirige al listado.
     */
    private void eliminar(HttpServletRequest request, HttpServletResponse response)
            throws SQLException, IOException {
        long id = Long.parseLong(request.getParameter("id"));
        productoDAO.eliminar(id);
        response.sendRedirect(request.getContextPath() + "/productos");
    }

    /**
     * Lee los datos del formulario y decide si inserta o actualiza el producto.
     */
    private void guardar(HttpServletRequest request) throws SQLException {
        String idParametro = request.getParameter("id");
        String nombre = request.getParameter("nombre");
        String categoria = request.getParameter("categoria");
        double precio = parsearPrecio(request.getParameter("precio"));
        boolean activo = request.getParameter("activo") != null;

        Producto producto = new Producto();
        producto.setNombre(nombre);
        producto.setCategoria(categoria);
        producto.setPrecio(precio);
        producto.setActivo(activo);

        if (idParametro == null || idParametro.isEmpty()) {
            productoDAO.insertar(producto);
        } else {
            producto.setId(Long.parseLong(idParametro));
            productoDAO.actualizar(producto);
        }
    }

    /**
     * Convierte el precio recibido del formulario a un valor numerico seguro.
     *
     * @param valor texto del campo precio (puede ser null o vacio)
     * @return el precio convertido, o 0 si no es valido
     */
    private double parsearPrecio(String valor) {
        if (valor == null || valor.isEmpty()) {
            return 0.0;
        }
        try {
            return Double.parseDouble(valor);
        } catch (NumberFormatException e) {
            return 0.0;
        }
    }
}
