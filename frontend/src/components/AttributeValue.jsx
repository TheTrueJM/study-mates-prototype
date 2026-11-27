import { COMMUNICATION_OPTIONS, formatAttribute, isProvided } from "../constants/attributes";

import CommunicationIcon from "./CommunicationIcon";
import { AvailabilityPreview } from "./AvailabilityGrid";


/**
 * Displays one of a Student's Details:
 *   - Availability as a Weekly Grid
 *   - Communication Methods as Chips with Icons
 *   - Everything else as Text
 *   - `common` highlights what is Shared
 */
export default function AttributeValue({ attribute, value, common }) {
  if (!isProvided(value)) {
    return <span className="text-muted">Not Provided</span>;
  }

  if (attribute === "availability") {
    return <AvailabilityPreview value={value} shared={Array.isArray(common) ? common : []} />;
  }

  if (attribute === "communication") {
    return (
      <span className="value-chips">
        {value.map((method) => (
          <span
            key={method}
            className={`value-chip ${Array.isArray(common) && common.includes(method) ? "is-common" : ""}`}
          >
            <CommunicationIcon method={method} />
            {COMMUNICATION_OPTIONS.find((option) => option.value === method)?.label ?? method}
          </span>
        ))}
      </span>
    );
  }

  // Custom Details with Multiple Choices
  if (Array.isArray(value)) {
    return (
      <span className="value-chips">
        {value.map((choice) => (
          <span key={choice} className={`value-chip ${Array.isArray(common) && common.includes(choice) ? "is-common" : ""}`}>
            {choice}
          </span>
        ))}
      </span>
    );
  }

  return <span className={common ? "value-common" : undefined}>{formatAttribute(attribute, value)}</span>;
}
