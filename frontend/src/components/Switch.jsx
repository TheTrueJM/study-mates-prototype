// An On/Off Toggle Switch, with a Label that can change to describe the Current State
export default function Switch({ checked, onChange, label, onLabel, offLabel, disabled = false, id }) {
  const text = checked ? (onLabel ?? label) : (offLabel ?? label);

  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      className={`switch ${checked ? "is-on" : ""}`}
      onClick={() => onChange(!checked)}
      disabled={disabled}
    >
      <span className="switch-track" aria-hidden="true">
        <span className="switch-thumb" />
      </span>
      {text && <span className="switch-label">{text}</span>}
    </button>
  );
}
