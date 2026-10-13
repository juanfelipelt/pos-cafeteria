/*
 * main.tsx — Punto de entrada (arranque) de la aplicación React.
 *
 * ¿Qué es? Es el primer archivo JavaScript/TypeScript que se ejecuta cuando
 * se carga la página web de Cafetería POS en el navegador.
 *
 * ¿Para qué sirve?
 *   1. Importa los estilos globales (index.css) para que toda la app tenga
 *      el mismo aspecto visual.
 *   2. Busca en el HTML el elemento con id="root" (el "contenedor" vacío que
 *      definimos en index.html).
 *   3. Monta (dibuja) dentro de ese contenedor el componente <App />, que es
 *      la raíz de toda la interfaz.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   main.tsx -> App.tsx (rutas y providers) -> páginas (Login, Dashboard,
 *   POS, etc.). Es el "encendido" de todo el árbol de componentes.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Buscamos el contenedor #root del index.html y le pedimos a React que
// "renderice" (pinte) dentro de él la aplicación completa.
// El signo '!' al final asegura a TypeScript que el elemento sí existe
// (no es null), ya que en index.html siempre declaramos <div id="root">.
createRoot(document.getElementById('root')!).render(
  /* <StrictMode> es una herramienta de desarrollo de React: ejecuta el código
     dos veces en modo desarrollo para ayudarnos a detectar errores. En
     producción no tiene ningún efecto sobre la app final. */
  <StrictMode>
    {/* <App /> es el componente principal que contiene rutas y contextos. */}
    <App />
  </StrictMode>,
)
