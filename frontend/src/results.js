// Each Student's Results of their Past Sessions (who they Met, and any Mutual Shortlists), kept on their Device
// so they can find their Classmates after the Session Closes (the server deletes everything once it does).

const RESULTS_KEY = "study-mates:results";
const MAX_SESSIONS = 10;


export function loadResults() {
  try {
    const results = JSON.parse(localStorage.getItem(RESULTS_KEY) || "[]");
    return Array.isArray(results) ? results : [];
  } catch {
    return [];
  }
}

function storeResults(results) {
  try {
    localStorage.setItem(RESULTS_KEY, JSON.stringify(results.slice(0, MAX_SESSIONS)));
  } catch {
    // Storage Unavailable, the Results just won't be Kept
  }
}

// A Student's Anonymous Name is unique within a Session, so identifies their Results (codes can be reused)
export const resultsKey = (code, studentName) => `${code}:${studentName}`;


/** Saves the Latest Results of a Session from a Student Update (once they've Met someone), returning its Key */
export function saveResults(update) {
  const history = update.history || [];
  if (!history.length || !update.tutorial_code || !update.username) return null;

  const key = resultsKey(update.tutorial_code, update.username);
  const results = loadResults();
  const previous = results.find((session) => session.key === key);

  // Keep Everyone Met, and once Mutual, always Mutual (e.g. if the other Student Leaves afterwards)
  const people = new Map((previous?.people || []).map((person) => [person.id, person]));
  history.forEach((person) => {
    const before = people.get(person.id);
    people.set(person.id, { ...before, ...person, mutual: !!(before?.mutual || person.mutual) });
  });

  const session = {
    key,
    code: update.tutorial_code,
    tutorialName: update.tutorial_name || update.tutorial_code,
    studentName: update.username,
    shortlisting: !!update.shortlisting,
    startedAt: previous?.startedAt ?? Date.now(),
    updatedAt: Date.now(),
    people: [...people.values()].sort((a, b) => (b.round ?? 0) - (a.round ?? 0) || a.name.localeCompare(b.name)),
  };

  storeResults([session, ...results.filter((s) => s.key !== key)].sort((a, b) => b.updatedAt - a.updatedAt));
  return key;
}

export function removeResults(key) {
  storeResults(loadResults().filter((session) => session.key !== key));
}

export function clearResults() {
  storeResults([]);
}
