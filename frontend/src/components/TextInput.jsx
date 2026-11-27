import InputWrapper from "./InputWrapper";

function TextInput({
  name, label, hint, error, value, placeholder, onChange, disabled = false, password = false, ...props
}) {
  return (
    <InputWrapper name={name} label={label} hint={hint} error={error}>
      <input
        type={!password ? "text" : "password"}
        id={name}
        name={name}
        className={`input ${disabled ? "input-disabled" : ""} ${error ? "input-invalid" : ""}`}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        aria-invalid={!!error}
        aria-describedby={error ? `${name}-error` : hint ? `${name}-hint` : undefined}
        {...props}
      />
    </InputWrapper>
  );
}

export default TextInput;
