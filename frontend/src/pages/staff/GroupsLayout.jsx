import Button from "../../components/Button";

import GroupGrid from "./GroupGrid";


export default function GroupsLayout({ students = {}, groups = {}, onGrouping, onDiscussion, busy = "" }) {
  const groupCount = Object.keys(groups).length;
  const studentCount = Object.values(groups).reduce((total, members) => total + members.length, 0);

  return (
    <>
      <div className="section-header">
        <h2 className="section-title">Group Formation Results</h2>
        <span className="text-muted">{groupCount} Groups · {studentCount} Students</span>
      </div>
      <p className="text-muted mb-md">Direct each Group to a Table. Once everyone is Seated, begin the Discussion.</p>

      {groupCount === 0 ? (
        <div className="empty-state mb-lg">No Groups Formed Yet. Select "Reform groups" to create them.</div>
      ) : (
        <div className="mb-lg">
          <GroupGrid groups={groups} students={students} />
        </div>
      )}

      {/* Action buttons */}
      <div className="btn-group">
        <Button variant="outline" onClick={onGrouping} disabled={!!busy}>
          {busy === "grouping" ? "Reforming…" : "Reform Groups"}
        </Button>
        <Button variant="secondary" onClick={onDiscussion} disabled={!!busy || groupCount === 0}>
          {busy === "discussion" ? "Starting…" : "Begin Discussion"}
        </Button>
      </div>
    </>
  );
}
