import { useState } from "react";

import { CUSTOM_LIMITS, MATCHING_MODES, MATCHING_WEIGHTS } from "../constants/attributes";

import Button from "./Button";
import ChipGroup from "./ChipGroup";
import TextInput from "./TextInput";
import CheckboxInput from "./CheckboxInput";


const CHOICE_OPTIONS = [
  { value: "single", label: "One Option" },
  { value: "multiple", label: "Multiple Options" },
];

const BLANK = { label: "", hint: "", options: ["", ""], multiple: false, matching: "display", weight: "normal" };


/** Validates a Custom Detail's Form Values (mirrors backend/app/custom_attributes.py), returning any errors */
function validateCustomAttribute(values, otherLabels = []) {
  const errors = {};
  const label = values.label.trim();
  const options = values.options.map((option) => option.trim()).filter(Boolean);

  if (!label) errors.label = "Enter a Name.";
  else if (label.length > CUSTOM_LIMITS.label) errors.label = `Use at most ${CUSTOM_LIMITS.label} Characters.`;
  else if (otherLabels.some((other) => other.toLowerCase() === label.toLowerCase())) {
    errors.label = "There is already a Custom Detail with this Name.";
  }

  if (values.hint.trim().length > CUSTOM_LIMITS.hint) errors.hint = `Use at most ${CUSTOM_LIMITS.hint} Characters.`;

  const lowered = options.map((option) => option.toLowerCase());
  if (options.length < CUSTOM_LIMITS.minOptions || options.length > CUSTOM_LIMITS.maxOptions) {
    errors.options = `Add between ${CUSTOM_LIMITS.minOptions} and ${CUSTOM_LIMITS.maxOptions} Options.`;
  } else if (options.some((option) => option.length > CUSTOM_LIMITS.option)) {
    errors.options = `Each Option can be at most ${CUSTOM_LIMITS.option} Characters.`;
  } else if (new Set(lowered).size !== lowered.length) {
    errors.options = "Each Option must be Different.";
  }

  return errors;
}


/**
 * Creates or Edits a Custom Detail: a Question with Options for Students to choose from.
 * Staff with an Account can also Save it (or Update their Saved Copy) to reuse in other Sessions.
 */
export default function CustomAttributeEditor({ initial, otherLabels = [], canSave = false, onSubmit, onCancel }) {
  const [values, setValues] = useState(() => (initial ? { ...BLANK, ...initial, options: [...initial.options] } : BLANK));
  const [save, setSave] = useState(false);
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);

  const set = (key) => (value) => {
    setValues((current) => ({ ...current, [key]: value }));
    setErrors({});
  };

  const setOption = (index, value) => set("options")(values.options.map((option, i) => (i === index ? value : option)));
  const removeOption = (index) => set("options")(values.options.filter((_, i) => i !== index));

  const submit = async () => {
    const validationErrors = validateCustomAttribute(values, otherLabels);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length) return;

    setBusy(true);
    const error = await onSubmit({
      ...values,
      label: values.label.trim(),
      hint: values.hint.trim(),
      options: values.options.map((option) => option.trim()).filter(Boolean),
    }, save);
    setBusy(false);
    if (error) setErrors({ form: error });
  };

  const mode = MATCHING_MODES.find((m) => m.value === values.matching);
  const editingSaved = !!initial?.saved_id;

  return (
    <div className="custom-editor">
      <TextInput
        name="custom-label"
        label="Name"
        value={values.label}
        placeholder="e.g. Preferred Role"
        onChange={set("label")}
        error={errors.label}
        maxLength={CUSTOM_LIMITS.label}
      />
      <TextInput
        name="custom-hint"
        label="Question for Students (optional)"
        value={values.hint}
        placeholder="e.g. Which part of a project do you enjoy most?"
        onChange={set("hint")}
        error={errors.hint}
        maxLength={CUSTOM_LIMITS.hint}
      />

      <div className="form-group">
        <span className="input-label" id="custom-options-label">Options</span>
        <div className="custom-options" role="group" aria-labelledby="custom-options-label">
          {values.options.map((option, index) => (
            <div key={index} className="custom-option">
              <input
                className="input"
                value={option}
                placeholder={`Option ${index + 1}`}
                onChange={(event) => setOption(index, event.target.value)}
                maxLength={CUSTOM_LIMITS.option}
                aria-label={`Option ${index + 1}`}
              />
              <button
                type="button"
                className="student-action student-remove"
                onClick={() => removeOption(index)}
                disabled={values.options.length <= CUSTOM_LIMITS.minOptions}
                aria-label={`Remove Option ${index + 1}`}
              >
                &times;
              </button>
            </div>
          ))}
        </div>
        {values.options.length < CUSTOM_LIMITS.maxOptions && (
          <button type="button" className="btn-text mt-xs" onClick={() => set("options")([...values.options, ""])}>
            + Add Option
          </button>
        )}
        {errors.options && <div className="input-error" role="alert">{errors.options}</div>}
      </div>

      <div className="form-group">
        <span className="input-label" id="custom-choice-label">Students can Choose</span>
        <ChipGroup
          options={CHOICE_OPTIONS}
          value={values.multiple ? "multiple" : "single"}
          onChange={(value) => value && set("multiple")(value === "multiple")}
          ariaLabelledBy="custom-choice-label"
        />
      </div>

      <div className="form-group">
        <span className="input-label" id="custom-matching-label">Matching</span>
        <ChipGroup
          options={MATCHING_MODES}
          value={values.matching}
          onChange={(value) => value && set("matching")(value)}
          ariaLabelledBy="custom-matching-label"
        />
        <div className="input-hint">
          {mode?.hint} {values.matching !== "display" && "Students can choose to Hide their Answer from their Group."}
        </div>
      </div>

      {values.matching !== "display" && (
        <div className="form-group">
          <span className="input-label" id="custom-weight-label">Matching Weight</span>
          <ChipGroup
            options={MATCHING_WEIGHTS}
            value={values.weight || "normal"}
            onChange={(value) => value && set("weight")(value)}
            ariaLabelledBy="custom-weight-label"
          />
          <div className="input-hint">
            How much this Detail counts towards the Matching Algorithm when Forming Groups.
          </div>
        </div>
      )}

      {canSave && (
        <CheckboxInput
          name="custom-save"
          label={editingSaved ? "Update my Saved Copy" : "Also Save to my Account"}
          hint={editingSaved ? undefined : "Saved Details can be Added to your Future Sessions."}
          value={save}
          onChange={setSave}
        />
      )}

      {errors.form && <p className="input-error" role="alert">{errors.form}</p>}

      <div className="btn-group mt-sm">
        <Button variant="outline" size="sm" onClick={onCancel} disabled={busy}>Cancel</Button>
        <Button variant="primary" size="sm" onClick={submit} disabled={busy}>
          {busy ? "Saving…" : initial ? "Update Detail" : "Add Detail"}
        </Button>
      </div>
    </div>
  );
}
