import { useState } from "react";

import { compareAttributes } from "../../constants/attributes";
import { useAttributeCatalog } from "../../hooks/useAttributeCatalog";
import AttributeValue from "../../components/AttributeValue";
import { ShortlistButton } from "../../components/PeopleMet";


const initials = (name = "") =>
  name.split("-").filter(Boolean).slice(0, 2).map((part) => part[0].toUpperCase()).join("");


// A Group Member and the Details they're Sharing (hidden until selected),
// highlighting what they have in Common with the Current Student
export default function MemberCard({ member, isSelf, ownAttributes, shortlisting = false, onShortlist }) {
  const [expanded, setExpanded] = useState(false);
  const catalog = useAttributeCatalog();

  const details = member.attributes || {};
  const common = isSelf ? {} : compareAttributes(ownAttributes, details, catalog);
  const commonCount = Object.keys(common).length;
  const shown = catalog.order.filter((attribute) => details[attribute] !== undefined);
  const detailsId = `member-${member.name}-details`;

  return (
    <div className={`member-card ${isSelf ? "is-self" : ""}`}>
      <div className="member-card-top">
        <button
          type="button"
          className="member-card-header"
          aria-expanded={expanded}
          aria-controls={detailsId}
          onClick={() => setExpanded(!expanded)}
        >
          <span className="member-avatar" aria-hidden="true">{initials(member.name)}</span>
          <span className="member-name">
            {member.name}
            {!isSelf && member.met > 0 && (
              <span className="member-met">Met {member.met === 1 ? "Once" : `${member.met} Times`} Before</span>
            )}
          </span>
          {isSelf ? (
            <span className="tag tag-primary">You</span>
          ) : commonCount > 0 ? (
            <span className="tag tag-match">{commonCount} in Common</span>
          ) : null}
          <span className="sr-only">{expanded ? "Hide Details" : "Show Details"}</span>
          <span className={`chevron ${expanded ? "is-open" : ""}`} aria-hidden="true" />
        </button>
        {shortlisting && !isSelf && member.id && onShortlist && (
          <ShortlistButton person={member} onToggle={onShortlist} />
        )}
      </div>

      {expanded && (
        <div className="member-details" id={detailsId}>
          {shown.length === 0 ? (
            <p className="text-muted">{isSelf ? "You aren't showing any Details to your Group." : "No Details Shared."}</p>
          ) : (
            <dl className="detail-list">
              {shown.map((attribute) => (
                <div key={attribute} className={`detail-row ${attribute === "availability" ? "detail-row-block" : ""}`}>
                  <dt>
                    {catalog.meta[attribute]?.label ?? attribute}
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
