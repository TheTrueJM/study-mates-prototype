import { useState } from "react";

import { isProvided, sortAttributes } from "../../constants/attributes";
import { useAttributeCatalog } from "../../hooks/useAttributeCatalog";

import Button from "../../components/Button";
import AttributeValue from "../../components/AttributeValue";
import StudentDetailsForm from "../../components/StudentDetailsForm";
import SeatingField from "../../components/SeatingField";

import { PreviousPeople } from "./GroupLayout";


export default function LobbyLayout({
  username, studentCount, attributes, sharedAttributes, attributesComplete, availableAttributes = [],
  editing, onEdit, onSave, onDone, history = [], shortlisting = false, onShortlist, seating = null,
}) {
  const [showDetails, setShowDetails] = useState(false);
  const catalog = useAttributeCatalog();

  const hasDetails = availableAttributes.length > 0;
  const shownAttributes = sortAttributes(availableAttributes, catalog);
  const isVisible = (attribute) => !catalog.meta[attribute]?.shareable || sharedAttributes.includes(attribute);
  const providedCount = shownAttributes.filter((attribute) => isProvided(attributes[attribute])).length;
  const visibleCount = shownAttributes
    .filter((attribute) => isProvided(attributes[attribute]) && isVisible(attribute)).length;

  if (hasDetails && editing) {
    return (
      <>
        <div className="welcome">
          <span className="eyebrow">Your Anonymous Name</span>
          <span className="welcome-name">{username}</span>
          <p className="welcome-text">
            Add a few Details to help Match you with Classmates. <strong>Everything is Optional</strong>, and you choose what your Group can see.
          </p>
        </div>

        <StudentDetailsForm
          availableAttributes={availableAttributes}
          initialAttributes={attributes}
          initialShared={sharedAttributes}
          onSave={onSave}
          onDone={onDone}
          doneLabel={attributesComplete ? "Done" : "I'm Ready"}
          seating={seating}
        />
      </>
    );
  }

  return (
    <div className="stack">
      <div className="waiting">
        <span className="eyebrow">Your Anonymous Name</span>
        <span className="welcome-name">{username}</span>

        <h2 className="waiting-title">You're All Set!</h2>
        <div className="loading-dots" aria-hidden="true">
          <div className="dot" />
          <div className="dot" />
          <div className="dot" />
        </div>
        <p className="text-muted">
          Waiting for your Tutor to Form Groups.
          {studentCount > 0 && ` ${studentCount} Student${studentCount === 1 ? " has" : "s have"} Joined so far.`}
        </p>
        {!hasDetails && (
          <p className="text-muted mt-xs">Your Tutor isn't asking for any Details in this Session.</p>
        )}
      </div>

      {seating && !hasDetails && <SeatingField {...seating} />}

      {hasDetails && (
        <section className="summary-card">
          <div className="summary-header">
            <button
              type="button"
              className="summary-toggle"
              aria-expanded={showDetails}
              aria-controls="your-details"
              onClick={() => setShowDetails(!showDetails)}
            >
              <span className={`chevron ${showDetails ? "is-open" : ""}`} aria-hidden="true" />
              <span className="summary-toggle-text">
                <span className="summary-title">Your Details</span>
                <span className="summary-meta">
                  {providedCount} of {shownAttributes.length} Provided · {visibleCount} Visible to your Group
                </span>
              </span>
            </button>
            <Button variant="outline" size="sm" onClick={onEdit}>Edit</Button>
          </div>

          {showDetails && (
            <div id="your-details" className="summary-body">
              <dl className="detail-list">
                {shownAttributes.map((attribute) => {
                  const provided = isProvided(attributes[attribute]);
                  const visible = isVisible(attribute);

                  return (
                    <div
                      key={attribute}
                      className={`detail-row ${attribute === "availability" && provided ? "detail-row-block" : ""}`}
                    >
                      <dt>
                        {catalog.meta[attribute]?.label ?? attribute}
                        {provided && (
                          <span className={`tag ${visible ? "tag-primary" : ""}`}>{visible ? "Visible" : "Hidden"}</span>
                        )}
                      </dt>
                      <dd><AttributeValue attribute={attribute} value={attributes[attribute]} /></dd>
                    </div>
                  );
                })}
                {seating?.staySeated && (
                  <div className="detail-row">
                    <dt>Seating <span className="tag">Only your Tutor</span></dt>
                    <dd>{seating.table ? `Staying at Table ${seating.table}` : "Staying at your Table (Table Number needed)"}</dd>
                  </div>
                )}
              </dl>
              <p className="member-note">You can Change these at any time, including during Group Rounds.</p>
            </div>
          )}
        </section>
      )}

      <PreviousPeople history={history} shortlisting={shortlisting} onShortlist={onShortlist} />
    </div>
  );
}
