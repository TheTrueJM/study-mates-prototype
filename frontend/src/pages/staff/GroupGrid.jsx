import { useEffect, useState } from "react";

import StudentLabel from "./StudentLabel";


/**
 * The Groups and their Members. With `onMove`, each Member can be Moved to another Group (or alone into a
 * New Group, within the Group Limit) from a small row of Options below them, so the Groups stay in view.
 */
export default function GroupGrid({ groups = {}, students = {}, maxGroups = null, onRemove, onMove }) {
  const [moving, setMoving] = useState(null); // Student ID
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
    const handleKey = (event) => event.key === "Escape" && setMoving(null);
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [moving]);

  const move = async (studentId, group) => {
    setBusy(true);
    const response = await onMove(studentId, group);
    setBusy(false);
    if (response?.ok) setMoving(null);
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
                  onMove={onMove && ((studentId) => setMoving(moving === studentId ? null : studentId))}
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
    </div>
  );
}
