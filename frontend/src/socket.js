import { io } from "socket.io-client";


// In Development requests go through the Vite proxy (same origin);
// Production builds connect directly to the configured backend
export const BACKEND_URL = import.meta.env.DEV ? "" : (import.meta.env.VITE_BACKEND_URL || "");

export const STUDENT_NAMESPACE = "/";
export const STAFF_NAMESPACE = "/staff";

const ACK_TIMEOUT = 8000;


// Identity is kept per Browser Tab (sessionStorage), so a Page Refresh or Reconnection resumes
// the Same Session, while Closing the Tab forgets it
const storageKey = (namespace, key) =>
  `study-mates:${namespace === STAFF_NAMESPACE ? "staff" : "student"}:${key}`;

export function getStored(namespace, key) {
  try {
    return sessionStorage.getItem(storageKey(namespace, key));
  } catch {
    return null;
  }
}

export function setStored(namespace, key, value) {
  try {
    if (value) sessionStorage.setItem(storageKey(namespace, key), value);
    else sessionStorage.removeItem(storageKey(namespace, key));
  } catch {
    // Storage Unavailable, the Session just won't Survive a Refresh
  }
}


// Staff Sign In (Guest or Account) is kept across Tabs and
// Browser Restarts until it Expires or they Sign Out
const STAFF_TOKEN_KEY = "study-mates:staff:token";

export function getStaffToken() {
  try {
    return localStorage.getItem(STAFF_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStaffToken(token) {
  try {
    if (token) localStorage.setItem(STAFF_TOKEN_KEY, token);
    else localStorage.removeItem(STAFF_TOKEN_KEY);
  } catch {
    // Storage Unavailable, the Sign In just won't Survive a Refresh
  }
}


const sockets = {};

/** Returns the Socket for a Namespace (created once, not connected until `connect()` is called) */
export function getSocket(namespace) {
  if (!sockets[namespace]) {
    sockets[namespace] = io(`${BACKEND_URL}${namespace}`, {
      path: "/socket.io",
      autoConnect: false,
      // Evaluated on every (re)connection so the Latest Identity is always sent:
      //   Staff are identified by their Access Token
      //   Students are identified by the Anonymous ID the server gave them
      auth: (callback) => callback(
        namespace === STAFF_NAMESPACE ? { token: getStaffToken() } : { uuid: getStored(namespace, "uuid") }
      ),
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
    });
  }
  return sockets[namespace];
}

/** Emits an Event and Resolves with the Server's Acknowledgement */
export function emitWithAck(namespace, event, payload) {
  const socket = getSocket(namespace);
  const args = payload === undefined ? [] : [payload];

  return new Promise((resolve) => {
    socket.timeout(ACK_TIMEOUT).emit(event, ...args, (error, response) => {
      if (error) {
        resolve({ ok: false, message: "The server didn't respond. Check your connection and try again." });
      } else {
        resolve(response && typeof response === "object" ? response : { ok: false, message: "Something went wrong." });
      }
    });
  });
}
