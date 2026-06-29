import InputWrapper from "./InputWrapper";

function TextInput({ name, label, hint, value, placeholder, onChange, disabled=false, password=false }) {
  return (
    <InputWrapper name={name} label={label} hint={hint}>
      <input
        type={!password ? "text" : "password"}
        id={name}
        name={name}
        className={`input ${disabled ? 'input-disabled' : ''}`}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        disabled={disabled}
      />
    </InputWrapper>
  );
}

export default TextInput;
