function SliderInput({ name, label, hint, value, min, max, step, onChange, disabled=false }) {
  return (
    <div className="form-group">
      {label && <label htmlFor={name} className="input-label">{label}</label>}

      <div className="range-group">
        <input
          type="range"
          id={name}
          name={name}
          className={`input ${disabled ? "input-disabled" : ""}`}
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(event) => onChange(Number(event.target.value))}
          disabled={disabled}
        />
        <div className="range-value">{value}</div>
      </div>
      <div className="range-labels">
        <span>{min}</span>
        <span>{max}</span>
      </div>

      {hint && <div className="input-hint">{hint}</div>}
    </div>
  );
}

export default SliderInput;
