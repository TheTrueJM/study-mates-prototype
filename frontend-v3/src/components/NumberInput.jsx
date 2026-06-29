import InputWrapper from "./InputWrapper";

function NumberInput({ name, label, hint, value, min, max, step, placeholder, onChange, disabled=false }) {
  return (
    <InputWrapper name={name} label={label} hint={hint}>
      <input
        type="number"
        id={name}
        name={name}
        className={`input ${disabled ? 'input-disabled' : ''}`}
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        disabled={disabled}
      />
    </InputWrapper>
  );
}

export default NumberInput;
