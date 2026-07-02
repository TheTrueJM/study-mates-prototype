import InputWrapper from "./InputWrapper";

function DropdownInput({ name, label, hint, value, options, placeholder, onChange, multiple=false, disabled=false }) {
  const updateSelection = (event) => {
    if (multiple) {
      const values = Array.from(event.target.selectedOptions, option => option.value);
      onChange(values);
    } else {
      onChange(event.target.value);
    }
  };

  return (
    <InputWrapper name={name} label={label} hint={hint}>
      <select 
        id={name}
        name={name}
        value={value} 
        onChange={updateSelection}
        multiple={multiple}
        disabled={disabled}
      >
        <option value="" disabled>{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
      {/* TODO: Optionally Display Selection Underneath */}
    </InputWrapper>
  );
}

export default DropdownInput;
