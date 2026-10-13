/*
 * components/MoneyInput.tsx — Campo de entrada para valores de dinero.
 *
 * ¿Qué es? Un <input> controlado y "inteligente" pensado para escribir montos
 * de dinero: solo acepta dígitos y un separador decimal, y va agrupando los
 * miles (ej. 1.234,56) mientras el usuario escribe.
 *
 * ¿Para qué sirve?
 *   - Mostrar el número ya formateado cuando el campo NO está enfocado.
 *   - Permitir escribir con separadores locales (coma o punto) sin errores.
 *   - Avisar al componente padre del valor numérico real mediante onChange.
 *
 * ¿Cómo se relaciona con el resto de la app?
 *   Se usa en formularios de precios y pagos (Productos, POS, Compras...).
 *   Se apoya en las funciones separators() y formatNumber() de ../lib/format.
 */

import { useEffect, useState } from "react";
import { formatNumber, separators } from "../lib/format";

// Propiedades que recibe el componente desde su padre.
interface Props {
  value?: number; // Valor numérico actual (controlado por el padre).
  onChange?: (value: number) => void; // Notifica el nuevo valor numérico.
  placeholder?: string; // Texto de ayuda cuando está vacío.
}

export default function MoneyInput({ value, onChange, placeholder }: Props) {
  // Símbolos del locale actual: dec = decimal, grp = separador de miles.
  const { dec, grp } = separators();
  // Estado con el texto que se ve en el input (lo que el usuario escribe).
  const [text, setText] = useState("");
  // Estado que indica si el input tiene el foco (para saber si reformatear).
  const [focused, setFocused] = useState(false);

  // Efecto: cuando cambia el valor externo o el foco, actualizamos el texto.
  // Si el input NO está enfocado, mostramos el número formateado; si está
  // vacío o es 0, dejamos el campo en blanco. Mientras el usuario escribe
  // (focused) no interfierimos para no moverle el cursor.
  useEffect(() => {
    if (!focused) {
      setText(value != null && value !== 0 ? formatNumber(value) : "");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, focused]);

  // group: inserta el separador de miles (grp) en la parte entera.
  // La expresión regular agrega el separador cada 3 dígitos desde la derecha.
  function group(intPart: string): string {
    return intPart ? intPart.replace(/\B(?=(\d{3})+(?!\d))/g, grp) : "";
  }

  // handle: se ejecuta con cada tecla. Limpia lo escrito, evita más de un
  // separador decimal y separa la parte entera de los decimales (máx. 2).
  function handle(raw: string) {
    const chars = raw.split("");
    // Conservamos solo dígitos y el separador decimal del locale.
    let t = chars.filter((ch) => ch === dec || /\d/.test(ch)).join("");

    // Si hay decimal, eliminamos cualquier separador decimal repetido,
    // dejando únicamente el primero.
    const idx = t.indexOf(dec);
    if (idx !== -1) {
      t = t.slice(0, idx + 1) + t.slice(idx + 1).split(dec).join("");
    }

    // Parte entera: solo dígitos antes del separador decimal.
    const intPart = (idx === -1 ? t : t.slice(0, idx)).replace(/\D/g, "");
    // Parte decimal: solo dígitos después del separador, con máximo 2 dígitos.
    const decPart =
      idx === -1 ? "" : t.slice(idx + 1).replace(/\D/g, "").slice(0, 2);
    // ¿El usuario ya escribió el separador decimal?
    const hasDec = idx !== -1;

    // Texto final que se muestra: con decimales usamos "0" delante si hace
    // falta; sin decimales, solo los miles agrupados.
    const display = hasDec
      ? `${intPart ? group(intPart) : "0"}${dec}${decPart}`
      : group(intPart);

    setText(display);
    // Avisamos al padre del valor numérico real (entero + decimales).
    onChange?.(
      parseInt(intPart || "0", 10) +
        (decPart ? Number(`0.${decPart}`) : 0)
    );
  }

  // Renderizamos el <input>. La lista de atributos es:
  //   - inputMode="decimal": pide al móvil un teclado numérico con decimales.
  //   - placeholder: el texto de ayuda.
  //   - value={text}: el valor mostrado lo controla nuestro estado "text".
  //   - onFocus/onBlur: activan y desactivan "focused" para saber si el
  //     usuario está escribiendo.
  //   - onChange: cada cambio de texto pasa por handle() para limpiar y
  //     formatear el número.
  return (
    <input
      inputMode="decimal"
      placeholder={placeholder}
      value={text}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      onChange={(e) => handle(e.target.value)}
    />
  );
}
