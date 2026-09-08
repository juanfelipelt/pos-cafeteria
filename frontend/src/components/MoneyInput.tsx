import { useEffect, useState } from "react";
import { formatNumber, separators } from "../lib/format";

interface Props {
  value?: number;
  onChange?: (value: number) => void;
  placeholder?: string;
}

export default function MoneyInput({ value, onChange, placeholder }: Props) {
  const { dec, grp } = separators();
  const [text, setText] = useState("");
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    if (!focused) {
      setText(value != null && value !== 0 ? formatNumber(value) : "");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, focused]);

  function group(intPart: string): string {
    return intPart ? intPart.replace(/\B(?=(\d{3})+(?!\d))/g, grp) : "";
  }

  function handle(raw: string) {
    const chars = raw.split("");
    let t = chars.filter((ch) => ch === dec || /\d/.test(ch)).join("");

    const idx = t.indexOf(dec);
    if (idx !== -1) {
      t = t.slice(0, idx + 1) + t.slice(idx + 1).split(dec).join("");
    }

    const intPart = (idx === -1 ? t : t.slice(0, idx)).replace(/\D/g, "");
    const decPart =
      idx === -1 ? "" : t.slice(idx + 1).replace(/\D/g, "").slice(0, 2);
    const hasDec = idx !== -1;

    const display = hasDec
      ? `${intPart ? group(intPart) : "0"}${dec}${decPart}`
      : group(intPart);

    setText(display);
    onChange?.(
      parseInt(intPart || "0", 10) +
        (decPart ? Number(`0.${decPart}`) : 0)
    );
  }

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
