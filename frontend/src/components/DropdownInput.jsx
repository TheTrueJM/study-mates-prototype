import InputWrapper from "./InputWrapper";

function DropdownInput({ name, label, hint, error, value, options, placeholder, onChange, multiple = false, disabled = false }) {
  const updateSelection = (event) => {
    if (multiple) {
      const values = Array.from(event.target.selectedOptions, option => option.value);
      onChange(values);
    } else {
      onChange(event.target.value);
    }
  };

  return (
    <InputWrapper name={name} label={label} hint={hint} error={error}>
      <select
        id={name}
        name={name}
        className={`input ${disabled ? "input-disabled" : ""}`}
        value={value ?? (multiple ? [] : "")}
        onChange={updateSelection}
        multiple={multiple}
        disabled={disabled}
      >
        {!multiple && <option value="" disabled>{placeholder}</option>}
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </InputWrapper>
  );
}

export default DropdownInput;
