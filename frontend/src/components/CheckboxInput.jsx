function CheckboxInput({ name, label, hint, value, onChange, disabled = false }) {
  return (
    <div className="form-group-tight">
      <div className="checkbox-group">
        <input
          type="checkbox"
          id={name}
          name={name}
          checked={!!value}
          onChange={(event) => onChange(event.target.checked)}
          disabled={disabled}
        />

        {label && <label htmlFor={name}>{label}</label>}
      </div>

      {hint && <div className="input-hint">{hint}</div>}
    </div>
  );
}

export default CheckboxInput;
