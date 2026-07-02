
function CheckboxInput({ name, label, hint, value, onChange, disabled=false }) {
  return (
    <div className="checkbox-group">
      <input
        type="checkbox"
        id={name}
        name={name}
        checked={value}
        onChange={(event) => onChange(event.target.checked)}
        disbaled={disabled}
      />

      {label && <label htmlFor={name}>{label}</label>}

      {hint && <div className="input-hint">{hint}</div>}
    </div>
  );
}

export default CheckboxInput;