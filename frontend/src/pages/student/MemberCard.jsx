import { useState } from "react";

import { ATTRIBUTES, ATTRIBUTE_ORDER, compareAttributes } from "../../constants/attributes";
import AttributeValue from "../../components/AttributeValue";


const initials = (name = "") =>
  name.split("-").filter(Boolean).slice(0, 2).map((part) => part[0].toUpperCase()).join("");


// A Group Member and the Details they're Sharing (hidden until selected),
// highlighting what they have in Common with the Current Student
export default function MemberCard({ member, isSelf, ownAttributes }) {
  const [expanded, setExpanded] = useState(false);

  const details = member.attributes || {};
  const common = isSelf ? {} : compareAttributes(ownAttributes, details);
  const commonCount = Object.keys(common).length;
  const shown = ATTRIBUTE_ORDER.filter((attribute) => details[attribute] !== undefined);
  const detailsId = `member-${member.name}-details`;

  return (
    <div className={`member-card ${isSelf ? "is-self" : ""}`}>
      <button
        type="button"
        className="member-card-header"
        aria-expanded={expanded}
        aria-controls={detailsId}
        onClick={() => setExpanded(!expanded)}
      >
        <span className="member-avatar" aria-hidden="true">{initials(member.name)}</span>
        <span className="member-name">{member.name}</span>
        {isSelf ? (
          <span className="tag tag-primary">You</span>
        ) : commonCount > 0 ? (
          <span className="tag tag-match">{commonCount} in Common</span>
        ) : null}
        <span className="sr-only">{expanded ? "Hide Details" : "Show Details"}</span>
        <span className={`chevron ${expanded ? "is-open" : ""}`} aria-hidden="true" />
      </button>

      {expanded && (
        <div className="member-details" id={detailsId}>
          {shown.length === 0 ? (
            <p className="text-muted">{isSelf ? "You aren't showing any Details to your Group." : "No Details Shared."}</p>
          ) : (
            <dl className="detail-list">
              {shown.map((attribute) => (
                <div key={attribute} className={`detail-row ${attribute === "availability" ? "detail-row-block" : ""}`}>
                  <dt>
                    {ATTRIBUTES[attribute]?.label ?? attribute}
                    {common[attribute] && <span className="sr-only"> (in common with you)</span>}
                  </dt>
                  <dd><AttributeValue attribute={attribute} value={details[attribute]} common={common[attribute]} /></dd>
                </div>
              ))}
            </dl>
          )}
          {isSelf && <p className="member-note">This is what your Group can see.</p>}
        </div>
      )}
    </div>
  );
}
