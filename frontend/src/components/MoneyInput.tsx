import { useState } from "react";
import { formatNumber, parseNumber } from "../lib/format";

interface Props {
  value?: number;
  onChange?: (value: number) => void;
  placeholder?: string;
}

export default function MoneyInput({ value, onChange, placeholder }: Props) {
  const [focused, setFocused] = useState(false);
  const [raw, setRaw] = useState("");

  const display = focused
    ? raw
    : value != null && value !== 0
      ? formatNumber(value)
      : "";

  function focus() {
    setFocused(true);
    setRaw(
      value != null && value !== 0 ? String(value).replace(".", ",") : ""
    );
  }

  return (
    <input
      inputMode="decimal"
      placeholder={placeholder}
      value={display}
      onFocus={focus}
      onBlur={() => setFocused(false)}
      onChange={(e) => {
        setRaw(e.target.value);
        onChange?.(parseNumber(e.target.value));
      }}
    />
  );
}
