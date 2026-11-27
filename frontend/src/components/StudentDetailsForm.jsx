import { useEffect, useRef, useState } from "react";

import { sortAttributes } from "../constants/attributes";
import { useAttributeCatalog } from "../hooks/useAttributeCatalog";

import Button from "./Button";
import ChipGroup from "./ChipGroup";
import Switch from "./Switch";
import SeatingField from "./SeatingField";
import CommunicationIcon from "./CommunicationIcon";
import { AvailabilityGrid } from "./AvailabilityGrid";


const SAVE_DELAY = 400;

const emptyValue = (meta) => (meta?.type === "single" ? null : []);


/**
 * Lets a Student provide (or skip) each Detail enabled for the Tutorial, and choose which
 * are visible to their Group. Changes are saved automatically shortly after each edit.
 * With `seating` ({ staySeated, table, onUpdate }), Students can first ask to stay at their Table.
 */
export default function StudentDetailsForm({
  availableAttributes = [], initialAttributes, initialShared, onSave, onDone, doneLabel = "Done", seating = null,
}) {
  const catalog = useAttributeCatalog();
  const [values, setValues] = useState(() => initialAttributes || {});
  const [shared, setShared] = useState(() => initialShared || []);
  const [status, setStatus] = useState("idle"); // idle | pending | saving | saved | error
  const [finishing, setFinishing] = useState(false);

  const pending = useRef(null);
  const saveTimer = useRef(null);
  const onSaveRef = useRef(onSave);
  const attributesRef = useRef(availableAttributes);

  useEffect(() => {
    onSaveRef.current = onSave;
    attributesRef.current = availableAttributes;
  }, [onSave, availableAttributes]);

  const buildPayload = (nextValues, nextShared) => {
    const payload = { shared_attributes: nextShared };
    attributesRef.current.forEach((attribute) => {
      payload[attribute] = nextValues[attribute];
    });
    return payload;
  };

  const flush = async () => {
    clearTimeout(saveTimer.current);
    saveTimer.current = null;

    const payload = pending.current;
    if (!payload) return { ok: true };
    pending.current = null;

    setStatus("saving");
    const response = await onSaveRef.current(payload);
    if (!pending.current) {
      // Keep a Failed Change queued so it is retried on the Next Save
      if (!response.ok) pending.current = payload;
      setStatus(response.ok ? "saved" : "error");
    }
    return response;
  };

  const queueSave = (nextValues, nextShared) => {
    pending.current = buildPayload(nextValues, nextShared);
    setStatus("pending");
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(flush, SAVE_DELAY);
  };

  // Send any Unsaved Change if the Form Closes
  useEffect(() => () => {
    clearTimeout(saveTimer.current);
    if (pending.current) onSaveRef.current(pending.current);
  }, []);


  const setValue = (attribute, value) => {
    const nextValues = { ...values, [attribute]: value };
    setValues(nextValues);
    queueSave(nextValues, shared);
  };

  const setVisible = (attribute, visible) => {
    const nextShared = visible ? [...shared, attribute] : shared.filter((a) => a !== attribute);
    setShared(nextShared);
    queueSave(values, nextShared);
  };

  const handleDone = async () => {
    setFinishing(true);
    const response = await flush();
    if (response.ok) await onDone?.();
    setFinishing(false);
  };


  const attributes = sortAttributes(availableAttributes, catalog);

  const statusText = {
    pending: "Saving…",
    saving: "Saving…",
    saved: "All Changes Saved",
    error: "Some Changes couldn't be Saved",
  }[status];

  return (
    <div className="details-form">
      {seating && <SeatingField {...seating} />}

      {attributes.map((attribute) => {
        const meta = catalog.meta[attribute];
        if (!meta) return null;
        const labelId = `detail-${attribute}-label`;
        const visible = shared.includes(attribute);
        const value = values[attribute] ?? emptyValue(meta);

        return (
          <section key={attribute} className="detail-field" aria-labelledby={labelId}>
            <div className="detail-field-header">
              <div>
                <h3 className="detail-field-title" id={labelId}>{meta.label}</h3>
                <p className="detail-field-question">{meta.question}</p>
              </div>

              {meta.shareable ? (
                <Switch
                  label={`Show my ${meta.label.toLowerCase()} to my Group`}
                  onLabel="Visible to Group"
                  offLabel="Hidden"
                  checked={visible}
                  onChange={(checked) => setVisible(attribute, checked)}
                />
              ) : (
                <span className="visibility-note">Visible to Group</span>
              )}
            </div>

            {meta.type === "availability" ? (
              <AvailabilityGrid
                value={value}
                onChange={(value) => setValue(attribute, value)}
                ariaLabelledBy={labelId}
              />
            ) : (
              <ChipGroup
                options={meta.options}
                value={value}
                onChange={(value) => setValue(attribute, value)}
                multiple={meta.type === "multiple"}
                noneLabel={meta.type === "single" ? (meta.noneLabel || "Skip") : undefined}
                ariaLabelledBy={labelId}
                renderIcon={attribute === "communication" ? (method) => <CommunicationIcon method={method} /> : undefined}
              />
            )}

            {meta.type === "multiple" && value?.length > 0 && (
              <button type="button" className="btn-text mt-xs" onClick={() => setValue(attribute, [])}>
                Clear Selection
              </button>
            )}

            {meta.shareable && !visible && (
              <p className="detail-field-note">Still used to help Match You, but your Group won't see it.</p>
            )}
          </section>
        );
      })}

      <div className="details-form-footer">
        <span className={`save-status save-status-${status}`} aria-live="polite">{statusText}</span>
        <Button variant="primary" fullWidth onClick={handleDone} disabled={finishing}>
          {finishing ? "Saving…" : doneLabel}
        </Button>
      </div>
    </div>
  );
}
