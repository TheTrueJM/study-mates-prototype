// A Set of toggle "chips" for picking One Value (with an optional "none" choice) or Several Values.
// `renderIcon(value)` optionally shows an Icon before an Option's Label.
export default function ChipGroup({
  options, value, onChange, multiple = false, noneLabel, ariaLabelledBy, disabled = false, renderIcon,
}) {
  const selected = multiple ? (value || []) : value;

  const isSelected = (optionValue) =>
    multiple ? selected.includes(optionValue) : selected === optionValue;

  const toggle = (optionValue) => {
    if (multiple) {
      onChange(isSelected(optionValue)
        ? selected.filter((v) => v !== optionValue)
        : [...selected, optionValue]);
    } else {
      onChange(isSelected(optionValue) ? null : optionValue);
    }
  };

  const noneSelected = selected === null || selected === undefined;

  return (
    <div className="chip-group" role="group" aria-labelledby={ariaLabelledBy}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          className={`chip ${isSelected(option.value) ? "is-selected" : ""}`}
          aria-pressed={isSelected(option.value)}
          onClick={() => toggle(option.value)}
          disabled={disabled}
        >
          {renderIcon?.(option.value)}
          {option.label}
          {option.sublabel && <span className="chip-sublabel">{option.sublabel}</span>}
        </button>
      ))}

      {!multiple && noneLabel && (
        <button
          type="button"
          className={`chip chip-none ${noneSelected ? "is-selected" : ""}`}
          aria-pressed={noneSelected}
          onClick={() => onChange(null)}
          disabled={disabled}
        >
          {noneLabel}
        </button>
      )}
    </div>
  );
}
