import { ATTRIBUTES, ATTRIBUTE_ORDER, DEFAULT_AVAILABLE_ATTRIBUTES, sortAttributes } from "../constants/attributes";


// Staff Selection of which Details Students are asked for in a Tutorial Session
export default function AttributeToggleList({ value = [], onChange, name = "attributes", hasCustom = false }) {
  const toggle = (attribute, checked) => {
    const next = checked ? [...value, attribute] : value.filter((a) => a !== attribute);
    onChange(sortAttributes(next));
  };

  const isDefault = value.length === DEFAULT_AVAILABLE_ATTRIBUTES.length
    && DEFAULT_AVAILABLE_ATTRIBUTES.every((attribute) => value.includes(attribute));

  return (
    <div className="form-group">
      <div className="input-label-row">
        <span className="input-label" id={`${name}-label`}>Student Details</span>
        {!isDefault && (
          <button type="button" className="btn-text" onClick={() => onChange([...DEFAULT_AVAILABLE_ATTRIBUTES])}>
            Reset to Defaults
          </button>
        )}
      </div>
      <p className="input-hint mb-xs">
        Choose what Students can Share. Every Detail is optional for Students, and they decide whether their Group can see it.
      </p>

      <div className="attr-toggle-list" role="group" aria-labelledby={`${name}-label`}>
        {ATTRIBUTE_ORDER.map((attribute) => {
          const meta = ATTRIBUTES[attribute];
          const checked = value.includes(attribute);
          const id = `${name}-${attribute}`;

          return (
            <label key={attribute} htmlFor={id} className={`attr-toggle ${checked ? "is-on" : ""}`}>
              <input
                type="checkbox"
                id={id}
                checked={checked}
                onChange={(event) => toggle(attribute, event.target.checked)}
              />
              <span className="attr-toggle-text">
                <span className="attr-toggle-label">{meta.label}</span>
                <span className="attr-toggle-hint">{meta.staffHint}</span>
              </span>
              <span className={`tag ${meta.shareable ? "tag-primary" : ""}`}>
                {meta.shareable ? "Matching" : "Display only"}
              </span>
            </label>
          );
        })}
      </div>

      {value.length === 0 && !hasCustom && (
        <p className="input-hint mt-xs">No details selected. Groups will be formed randomly.</p>
      )}
    </div>
  );
}
