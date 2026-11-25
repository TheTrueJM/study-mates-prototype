import { DAYS, TIMES, formatAvailability } from "../constants/attributes";


// Editable Weekly Availability Grid (days as rows, times as columns)
// Tapping a Day or Time heading toggles that whole Row/Column
export function AvailabilityGrid({ value = [], onChange, ariaLabelledBy }) {
  const selected = new Set(value);

  const setCodes = (codes, on) => {
    const next = new Set(selected);
    codes.forEach((code) => (on ? next.add(code) : next.delete(code)));
    onChange(DAYS.flatMap((d) => TIMES.map((t) => d.code + t.code)).filter((code) => next.has(code)));
  };

  const toggleGroup = (codes) => setCodes(codes, !codes.every((code) => selected.has(code)));

  return (
    <div className="availability-editor">
      <div className="availability-grid" role="group" aria-labelledby={ariaLabelledBy}>
        <span />
        {TIMES.map((time) => (
          <button
            key={time.code}
            type="button"
            className="availability-heading"
            onClick={() => toggleGroup(DAYS.map((d) => d.code + time.code))}
            aria-label={`Toggle every ${time.label.toLowerCase()}`}
          >
            {time.label}
          </button>
        ))}

        {DAYS.map((day) => (
          <div key={day.code} className="availability-row-cells" role="presentation">
            <button
              type="button"
              className="availability-day"
              onClick={() => toggleGroup(TIMES.map((t) => day.code + t.code))}
              aria-label={`Toggle all of ${day.label}`}
            >
              {day.short}
            </button>
            {TIMES.map((time) => {
              const code = day.code + time.code;
              const isOn = selected.has(code);
              return (
                <button
                  key={code}
                  type="button"
                  className={`availability-cell ${isOn ? "is-selected" : ""}`}
                  aria-pressed={isOn}
                  aria-label={`${day.label} ${time.label.toLowerCase()}`}
                  onClick={() => setCodes([code], !isOn)}
                >
                  <span aria-hidden="true">{isOn ? "✓" : ""}</span>
                </button>
              );
            })}
          </div>
        ))}
      </div>

      <div className="availability-footer">
        <span className="input-hint">
          {selected.size ? `${selected.size} time${selected.size === 1 ? "" : "s"} selected` : "Tap the times you're usually free"}
        </span>
        {selected.size > 0 && (
          <button type="button" className="btn-text" onClick={() => onChange([])}>Clear</button>
        )}
      </div>
    </div>
  );
}


// Compact Read-Only Availability, highlighting Times Shared with the Current Student
export function AvailabilityPreview({ value = [], shared = [] }) {
  const available = new Set(value);
  const common = new Set(shared);

  return (
    <div className="availability-preview">
      <div className="availability-preview-grid" aria-hidden="true">
        <span />
        {DAYS.map((day) => <span key={day.code} className="availability-preview-day">{day.short[0]}</span>)}
        {TIMES.map((time) => (
          <div key={time.code} className="availability-preview-row" role="presentation">
            <span className="availability-preview-time">{time.short}</span>
            {DAYS.map((day) => {
              const code = day.code + time.code;
              const state = common.has(code) ? "is-common" : available.has(code) ? "is-available" : "";
              return <span key={code} className={`availability-preview-cell ${state}`} title={`${day.label} ${time.label.toLowerCase()}`} />;
            })}
          </div>
        ))}
      </div>
      <p className="availability-preview-text">
        {formatAvailability(value)}
        {shared.length > 0 && (
          <span className="availability-preview-common"> · Free the Same Time as You: {formatAvailability(shared)}</span>
        )}
      </p>
    </div>
  );
}
