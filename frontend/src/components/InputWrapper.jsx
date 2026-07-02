function InputWrapper({ children, name, label, hint }) {
  return (
    <div className="form-group">
      {label && <label htmlFor={name} className="input-label">{label}</label>}

      {children}

      {hint && <div className="input-hint">{hint}</div>}
    </div>
  );
}

export default InputWrapper;
