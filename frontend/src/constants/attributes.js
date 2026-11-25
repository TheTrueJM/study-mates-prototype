// Student Detail (attribute) definitions shared across Staff and Student Pages.
// NOTE Keep values in sync with backend/app/enums.py

export const DAYS = [
  { code: "MON", short: "Mon", label: "Monday" },
  { code: "TUE", short: "Tue", label: "Tuesday" },
  { code: "WED", short: "Wed", label: "Wednesday" },
  { code: "THU", short: "Thu", label: "Thursday" },
  { code: "FRI", short: "Fri", label: "Friday" },
  { code: "SAT", short: "Sat", label: "Saturday" },
  { code: "SUN", short: "Sun", label: "Sunday" },
];

export const TIMES = [
  { code: "M", short: "Mor", label: "Morning" },
  { code: "A", short: "Aft", label: "Afternoon" },
  { code: "E", short: "Eve", label: "Evening" },
];

export const GRADE_OPTIONS = [
  { value: 7, label: "High Distinction", sublabel: "7" },
  { value: 6, label: "Distinction", sublabel: "6" },
  { value: 5, label: "Credit", sublabel: "5" },
  { value: 4, label: "Pass", sublabel: "4" },
];

export const MEETING_MODE_OPTIONS = [
  { value: "physical", label: "In-Person" },
  { value: "virtual", label: "Online" },
  { value: "either", label: "Either Works" },
];

export const COMMUNICATION_OPTIONS = [
  { value: "email", label: "Email" },
  { value: "sms", label: "Text / SMS" },
  { value: "teams", label: "Teams" },
  { value: "slack", label: "Slack" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "discord", label: "Discord" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "messenger", label: "Messenger" },
  { value: "instagram", label: "Instagram" },
  { value: "snapchat", label: "Snapchat" },
  { value: "signal", label: "Signal" },
  { value: "telegram", label: "Telegram" },
  { value: "others", label: "Other" },
];

export const YEAR_OPTIONS = [
  { value: 1, label: "1st" },
  { value: 2, label: "2nd" },
  { value: 3, label: "3rd" },
  { value: 4, label: "4th" },
  { value: 5, label: "5th+" },
];

export const SEMESTER_OPTIONS = [
  { value: 1, label: "Semester 1" },
  { value: 2, label: "Semester 2" },
];

// Display Order of Attributes throughout the Application
export const ATTRIBUTE_ORDER = [
  "goal_grade", "current_gpa", "availability", "meeting_mode", "communication", "year", "semester",
];

// Enabled by Default when a Staff Member sets up a Tutorial
export const DEFAULT_AVAILABLE_ATTRIBUTES = [
  "goal_grade", "current_gpa", "availability", "meeting_mode", "communication",
];

/**
 * - type: Input Type used in the Student Details Dorm
 * - shareable: Student chooses whether their Group can See It (matching attributes),
 *   otherwise it is Display-Only and Always Visible when provided
 */
export const ATTRIBUTES = {
  goal_grade: {
    label: "Goal grade",
    question: "What Grade are you aiming for in this Unit?",
    staffHint: "The Grade Students are aiming for in this Unit.",
    type: "single",
    options: GRADE_OPTIONS,
    shareable: true,
  },
  current_gpa: {
    label: "Current GPA",
    question: "Which Grade is your Current GPA closest to?",
    staffHint: "The Grade each Student's Current GPA is closest to.",
    type: "single",
    options: GRADE_OPTIONS,
    noneLabel: "No GPA Yet / Prefer not to Say",
    shareable: true,
  },
  availability: {
    label: "Availability",
    question: "When are you usually Available to Meet or Work on the Assessment?",
    staffHint: "Days and Times Students are available to Meet and Work.",
    type: "availability",
    shareable: true,
  },
  meeting_mode: {
    label: "Meeting mode",
    question: "How do you prefer to Meet with your Group?",
    staffHint: "Whether Students prefer Meeting In-Person or Online.",
    type: "single",
    options: MEETING_MODE_OPTIONS,
    shareable: true,
  },
  communication: {
    label: "Communication",
    question: "Which Apps/Methods are you happy to use to Communicate? Pick as many as you like.",
    staffHint: "Apps and Methods Students are happy to use to Communicate.",
    type: "multiple",
    options: COMMUNICATION_OPTIONS,
    shareable: true,
  },
  year: {
    label: "Year of Study",
    question: "Which Year of your Degree are you in?",
    staffHint: "Shown to Group Members Only (not used for matching).",
    type: "single",
    options: YEAR_OPTIONS,
    shareable: false,
  },
  semester: {
    label: "Semester of Study",
    question: "Which Semester of your Degree Year are you in?",
    staffHint: "Shown to Group Members Only (not used for matching).",
    type: "single",
    options: SEMESTER_OPTIONS,
    shareable: false,
  },
};

export const isMatchingAttribute = (attribute) => !!ATTRIBUTES[attribute]?.shareable;

export const sortAttributes = (attributes = []) =>
  ATTRIBUTE_ORDER.filter((attribute) => attributes.includes(attribute));

export const isProvided = (value) =>
  value !== null && value !== undefined && value !== "" && !(Array.isArray(value) && value.length === 0);

const optionLabel = (options, value) => options.find((option) => option.value === value)?.label;

/** Formats a Single-Value or Multi-Value Attribute for Display (availability is rendered as a grid) */
export function formatAttribute(attribute, value) {
  if (!isProvided(value)) return "Not Provided";

  switch (attribute) {
    case "goal_grade":
    case "current_gpa": {
      const option = GRADE_OPTIONS.find((o) => o.value === value);
      return option ? `${option.label} (${option.sublabel})` : String(value);
    }
    case "meeting_mode":
      return optionLabel(MEETING_MODE_OPTIONS, value) ?? String(value);
    case "communication":
      return value.map((method) => optionLabel(COMMUNICATION_OPTIONS, method) ?? method).join(", ");
    case "availability":
      return formatAvailability(value);
    case "year":
      return value >= 5 ? "Year 5+" : `Year ${value}`;
    case "semester":
      return `Semester ${value}`;
    default:
      return Array.isArray(value) ? value.join(", ") : String(value);
  }
}

/** e.g. ["MONM", "MONA", "WEDE"] -> "Mon morning & afternoon, Wed evening" */
export function formatAvailability(codes = []) {
  return DAYS
    .map((day) => {
      const times = TIMES.filter((time) => codes.includes(day.code + time.code)).map((t) => t.label.toLowerCase());
      if (!times.length) return null;
      return `${day.short} ${times.length === 3 ? "all day" : times.join(" & ")}`;
    })
    .filter(Boolean)
    .join(", ");
}

/** Values Another Student has in Common with the Current Student, per Attribute */
export function compareAttributes(own = {}, other = {}) {
  const common = {};

  for (const attribute of ["goal_grade", "current_gpa", "year", "semester"]) {
    if (isProvided(own[attribute]) && own[attribute] === other[attribute]) common[attribute] = true;
  }

  if (isProvided(own.meeting_mode) && isProvided(other.meeting_mode)) {
    const compatible = own.meeting_mode === other.meeting_mode
      || own.meeting_mode === "either" || other.meeting_mode === "either";
    if (compatible) common.meeting_mode = true;
  }

  for (const attribute of ["availability", "communication"]) {
    const shared = (other[attribute] || []).filter((value) => (own[attribute] || []).includes(value));
    if (shared.length) common[attribute] = shared;
  }

  return common;
}
