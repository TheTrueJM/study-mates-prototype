import { io } from "socket.io-client";


// Independent socket instances for each namespace
let studentSocket = null;
let staffSocket = null;


export function getStudentSocket() {
  if (!studentSocket) {
    studentSocket = io("/", {
      path: "/socket.io",
      auth: { user_id: null, code: null },
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      timeout: 20000
    });
    console.log("Student Socket Created:", studentSocket);
  }
  return studentSocket;
}

export function getStaffSocket() {
  if (!staffSocket) {
    staffSocket = io("/staff", {
      path: "/socket.io",
      auth: { user_id: null, code: null },
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      timeout: 20000
    });
    console.log("Staff Socket Created:", staffSocket);
  }
  return staffSocket;
}

export function getSocket(namespace = "/") {
  if (namespace === "/staff") {
    return getStaffSocket();
  }
  return getStudentSocket();
}


export function setSocketAuth(namespace, authParams) {
  const socket = namespace === "/staff" ? staffSocket : studentSocket;
  if (socket) {
    socket.auth = { ...authParams };
    console.log(`Auth updated for ${namespace} socket:`, socket.auth);
  }
}


export function disconnectSocket(namespace = "/") {
  if (namespace === "/staff" && staffSocket) {
    staffSocket.disconnect();
    staffSocket = null;
    console.log("Staff Socket Disconnected");
  } else if (namespace === "/" && studentSocket) {
    studentSocket.disconnect();
    studentSocket = null;
    console.log("Student Socket Disconnected");
  }
}

export function disconnectAllSockets() {
  if (studentSocket) {
    studentSocket.disconnect();
    studentSocket = null;
  }
  if (staffSocket) {
    staffSocket.disconnect();
    staffSocket = null;
  }
  console.log("All Sockets Disconnected");
}