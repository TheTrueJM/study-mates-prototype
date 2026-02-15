// Input - Reusable form input component
// Passes e.target.value directly to onChange for convenience with setState

function Input({ label, type = 'text', value, onChange, placeholder, hint, disabled = false }) {
  return (
    <div className="form-group">
      {label && <label className="input-label">{label}</label>}

      <input
        type={type}
        className={`input ${disabled ? 'input-disabled' : ''}`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
      />

      {hint && <div className="input-hint">{hint}</div>}
    </div>
  );
}

export default Input;
