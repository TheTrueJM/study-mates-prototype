function InputWrapper({ children, name, label, hint, error }) {
  return (
    <div className="form-group">
      {label && <label htmlFor={name} className="input-label">{label}</label>}

      {children}

      {error ? (
        <div className="input-error" id={`${name}-error`} role="alert">{error}</div>
      ) : (
        hint && <div className="input-hint" id={`${name}-hint`}>{hint}</div>
      )}
    </div>
  );
}

export default InputWrapper;
