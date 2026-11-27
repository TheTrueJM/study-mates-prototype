import { useState } from "react";

import { SEAT_FLASH_DURATION } from "../../constants/settings";


/**
 * A Student's Name and whether they've Disconnected, with Buttons to Move them to another Group or Remove them.
 * Selecting their Name shows their Status, including the Table they're staying at (every Name can be Selected,
 * so a Projected Screen doesn't single anyone out). A Table they've just set is briefly shown beside their Name.
 */
export default function StudentLabel({ id, student, onRemove, onMove, moving = false }) {
  const [open, setOpen] = useState(false);

  if (!student) return <span className="student-label">Unknown</span>;

  const name = student.name || "Unknown";
  const infoId = `student-info-${id}`;

  return (
    <>
      <span className="student-label">
        <button
          type="button"
          className="student-name"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          aria-controls={infoId}
        >
          {name}
        </button>
        {student.flash && student.seatTable != null && (
          <span className="seat-flash" role="status" style={{ animationDuration: `${SEAT_FLASH_DURATION}ms` }}>
            Table {student.seatTable}
          </span>
        )}
        {!student.connected && <span className="student-offline">Offline</span>}
      </span>
      {onMove && (
        <button
          type="button"
          className={`student-action student-move ${moving ? "is-active" : ""}`}
          onClick={() => onMove(id)}
          aria-label={`Move ${name}`}
          aria-expanded={moving}
          title="Move to Another Group"
        >
          &#8644;
        </button>
      )}
      {onRemove && (
        <button
          type="button"
          className="student-action student-remove"
          onClick={() => onRemove(id)}
          aria-label={`Remove ${name}`}
          title="Remove from Session"
        >
          &times;
        </button>
      )}

      {open && (
        <ul className="student-info" id={infoId} aria-label={`About ${name}`}>
          <li>{student.connected ? "Online" : "Offline"}</li>
          <li>{student.attributes_complete ? "Details Ready" : "Still adding Details"}</li>
          {student.seatTable != null && <li className="student-info-seat">Staying at Table {student.seatTable}</li>}
          {student.needsTable && <li className="student-info-seat">Staying at their Table, waiting for the Table Numbers</li>}
        </ul>
      )}
    </>
  );
}
