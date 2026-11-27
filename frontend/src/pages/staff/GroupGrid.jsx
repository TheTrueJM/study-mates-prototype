import { useEffect, useState } from "react";

import ConfirmDialog from "../../components/ConfirmDialog";

import StudentLabel from "./StudentLabel";


/**
 * The Groups and their Members. With `onMove`, each Member can be Moved to another Group (or alone into a
 * New Group, within the Group Limit) from a small row of Options below them, so the Groups stay in view.
 * Students staying at their Table are only Moved once the Staff Member confirms (e.g. their Table Number was wrong).
 */
export default function GroupGrid({ groups = {}, students = {}, maxGroups = null, onRemove, onMove }) {
  const [moving, setMoving] = useState(null); // Student ID
  const [confirming, setConfirming] = useState(null); // ID of a Student staying at their Table
  const [forced, setForced] = useState(null); // ID of a Student staying at their Table, confirmed to be Moved
  const [busy, setBusy] = useState(false);

  const groupIds = Object.keys(groups);
  const atLimit = !!maxGroups && groupIds.length >= maxGroups;

  // Stop Moving if the Student is no longer Grouped (e.g. they Left or Groups were Reformed)
  const stillGrouped = moving && Object.values(groups).some((members) => members.includes(moving));
  useEffect(() => {
    if (moving && !stillGrouped) setMoving(null);
  }, [moving, stillGrouped]);

  useEffect(() => {
    if (!moving) return undefined;
    const handleKey = (event) => {
      if (event.key !== "Escape") return;
      setMoving(null);
      setForced(null);
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [moving]);

  const move = async (studentId, group) => {
    setBusy(true);
    const response = await onMove(studentId, group, forced === studentId);
    setBusy(false);
    if (response?.ok) stopMoving();
  };

  // Confirming a Student staying at their Table only allows Moving them this once
  const stopMoving = () => {
    setMoving(null);
    setForced(null);
  };

  const toggleMoving = (studentId) => {
    if (moving === studentId) {
      stopMoving();
    } else if (students[studentId]?.seatTable != null && forced !== studentId) {
      setConfirming(studentId);
    } else {
      setMoving(studentId);
    }
  };

  const confirmMove = () => {
    setForced(confirming);
    setMoving(confirming);
    setConfirming(null);
  };

  return (
    <div className="group-grid">
      {Object.entries(groups).map(([id, members]) => (
        <div key={id} className="group-card">
          <div className="group-card-header">
            <span>Group {id}</span>
            <span className="group-card-count" aria-label={`${members.length} students`}>{members.length}</span>
          </div>
          <ul className="group-card-body">
            {members.map((member) => (
              <li key={member} className={`group-member ${students[member]?.connected ? "" : "is-disconnected"}`}>
                <StudentLabel
                  id={member}
                  student={students[member]}
                  onRemove={onRemove}
                  onMove={onMove && toggleMoving}
                  moving={moving === member}
                />

                {moving === member && (
                  <div className="move-options" role="group" aria-label={`Move ${students[member]?.name ?? "Student"} to`}>
                    <span className="move-options-label">Move to</span>
                    {groupIds.filter((groupId) => groupId !== id).map((groupId) => (
                      <button
                        key={groupId}
                        type="button"
                        className="move-option"
                        onClick={() => move(member, Number(groupId))}
                        disabled={busy}
                        aria-label={`Group ${groupId} (${groups[groupId].length} Students)`}
                      >
                        Group {groupId} <span className="move-option-count">({groups[groupId].length})</span>
                      </button>
                    ))}
                    <button
                      type="button"
                      className="move-option"
                      onClick={() => move(member, "new")}
                      disabled={busy || atLimit || members.length === 1}
                      title={atLimit ? `The Limit of ${maxGroups} Groups has been Reached` : undefined}
                    >
                      + New Group
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      ))}

      <ConfirmDialog
        isOpen={!!confirming}
        title="Move a Student staying at their Table?"
        message={
          `${students[confirming]?.name ?? "This Student"} has asked to stay at Table ${students[confirming]?.seatTable}, `
          + "so their Group is Formed there. Only Move them if their Table Number was wrong (such as to the Group "
          + "for the Table they're actually at). They'll then stay at their New Group's Table."
        }
        confirmLabel="Choose a Group"
        onConfirm={confirmMove}
        onCancel={() => setConfirming(null)}
      />
    </div>
  );
}
