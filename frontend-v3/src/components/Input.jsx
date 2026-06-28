function Input({ label, type = 'text', value, min, max, step, onChange, placeholder, disabled = false, hint }) {
  return (
    <div className="form-group">
      {label && <label className="input-label">{label}</label>}

      <input
        type={type}
        className={`input ${disabled ? 'input-disabled' : ''}`}
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
      />

      {hint && <div className="input-hint">{hint}</div>}
    </div>
  );
}

export default Input;
