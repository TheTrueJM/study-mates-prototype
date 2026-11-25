import InputWrapper from "./InputWrapper";

function NumberInput({ name, label, hint, error, value, min, max, step, placeholder, onChange, disabled = false }) {
  return (
    <InputWrapper name={name} label={label} hint={hint} error={error}>
      <input
        type="number"
        inputMode="numeric"
        id={name}
        name={name}
        className={`input ${disabled ? "input-disabled" : ""} ${error ? "input-invalid" : ""}`}
        value={value ?? ""}
        min={min}
        max={max}
        step={step}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        aria-invalid={!!error}
        aria-describedby={error ? `${name}-error` : hint ? `${name}-hint` : undefined}
      />
    </InputWrapper>
  );
}

export default NumberInput;
