import { useEffect, useId, useRef, useState } from "react";

import Button from "./Button";
import Switch from "./Switch";


// Mirrors MIN_TABLE and MAX_TABLE in backend/app/sockets/seating.py
const MIN_TABLE = 1;
const MAX_TABLE = 99;


/**
 * Lets a Student ask to stay at their Table for the Activity (no reason needed), after confirming what it means,
 * then enter their Table Number once their Tutor shares them. Only the Student and their Tutor see this.
 */
export default function SeatingField({ staySeated = false, table = null, onUpdate }) {
  const id = useId();
  const [confirming, setConfirming] = useState(false);
  const [tableInput, setTableInput] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const confirmRef = useRef(null);
  const tableRef = useRef(null);
  const focusTable = useRef(false);

  // Move Focus to what Appears next, so Screen Reader and Keyboard Users follow along
  useEffect(() => {
    if (confirming) confirmRef.current?.focus();
  }, [confirming]);

  // (the Server's Update and its Acknowledgement can arrive in either order, so this waits for both)
  useEffect(() => {
    if (staySeated && table === null && !confirming && focusTable.current) {
      focusTable.current = false;
      tableRef.current?.focus();
    }
  }, [staySeated, table, confirming]);


  const update = async (nextStaySeated, nextTable = null) => {
    setSaving(true);
    const response = await onUpdate(nextStaySeated, nextTable);
    setSaving(false);
    return response;
  };

  const handleToggle = async (checked) => {
    setError("");
    if (checked) {
      setConfirming(true);
    } else {
      setConfirming(false);
      setTableInput("");
      await update(false);
    }
  };

  const handleConfirm = async () => {
    focusTable.current = true;
    const response = await update(true);
    focusTable.current = response.ok;
    if (response.ok) setConfirming(false);
  };

  const handleSetTable = async (event) => {
    event.preventDefault();
    const number = Number(tableInput);
    if (!Number.isInteger(number) || number < MIN_TABLE || number > MAX_TABLE) {
      setError(`Enter a Table Number between ${MIN_TABLE} and ${MAX_TABLE}.`);
      return;
    }

    setError("");
    const response = await update(true, number);
    if (response.ok) setTableInput("");
  };

  // Clearing the Table lets the Tutor know the Table Numbers are needed again
  const handleChangeTable = async () => {
    const previous = table;
    focusTable.current = true;
    const response = await update(true, null);
    if (response.ok) setTableInput(String(previous ?? ""));
    else focusTable.current = false;
  };


  const labelId = `${id}-label`;
  const tableId = `${id}-table`;

  return (
    <section className="detail-field seating-field" aria-labelledby={labelId}>
      <div className="detail-field-header">
        <div>
          <h3 className="detail-field-title" id={labelId}>Seating</h3>
          <p className="detail-field-question">Do you need to stay at your Table for this Activity?</p>
        </div>
        <Switch
          label="I need to stay at my Table"
          onLabel={confirming ? "Confirm Below" : "Staying at my Table"}
          offLabel="No"
          checked={staySeated || confirming}
          onChange={handleToggle}
          disabled={saving}
        />
      </div>

      <p className="detail-field-note">
        For example, due to a Disability, Injury, Health Condition, or another Access Need. You don't need to explain why.
        Only you and your Tutor can see this.
      </p>

      {confirming && (
        <div className="seating-panel" role="group" aria-labelledby={`${id}-confirm`}>
          <h4 className="seating-panel-title" id={`${id}-confirm`} tabIndex={-1} ref={confirmRef}>
            Stay at your Table?
          </h4>
          <ul className="seating-points">
            <li>Your Group is Formed at your Table every Round, so <strong>your Classmates come to you</strong>.</li>
            <li>You're Matched with Classmates in exactly the same way as everyone else.</li>
            <li>Your Group isn't told why, and only your Tutor can see that you're staying at your Table.</li>
            <li>Next, you'll enter your Table Number. Your Tutor will be let know that someone needs the Table Numbers (not who).</li>
          </ul>
          <div className="btn-group">
            <Button variant="outline" size="sm" onClick={() => setConfirming(false)} disabled={saving}>Not Now</Button>
            <Button size="sm" onClick={handleConfirm} disabled={saving}>
              {saving ? "Saving…" : "Stay at my Table"}
            </Button>
          </div>
        </div>
      )}

      {staySeated && !confirming && (table === null ? (
        <form className="seating-panel" onSubmit={handleSetTable} noValidate>
          <label className="input-label" htmlFor={tableId}>Which Table are you sitting at?</label>
          <div className="seating-table-row">
            <input
              ref={tableRef}
              id={tableId}
              type="number"
              inputMode="numeric"
              className={`input seating-table-input ${error ? "input-invalid" : ""}`}
              min={MIN_TABLE}
              max={MAX_TABLE}
              placeholder="e.g. 5"
              value={tableInput}
              onChange={(event) => setTableInput(event.target.value)}
              aria-invalid={!!error}
              aria-describedby={`${tableId}-hint`}
            />
            <Button type="submit" size="sm" disabled={saving || tableInput === ""}>
              {saving ? "Saving…" : "Set Table"}
            </Button>
          </div>
          <p className={error ? "input-error" : "input-hint"} id={`${tableId}-hint`} role={error ? "alert" : undefined}>
            {error || "Not sure? Ask your Tutor which Number your Table is. They've been let know that someone needs the Table Numbers."}
          </p>
        </form>
      ) : (
        <div className="seating-panel seating-set" aria-live="polite">
          <p>
            <strong>You're staying at Table {table}.</strong> Your Group will be Formed here, so you won't need to move.
          </p>
          <button type="button" className="btn-text" onClick={handleChangeTable} disabled={saving}>Change Table</button>
        </div>
      ))}
    </section>
  );
}
