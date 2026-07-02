import { io } from "socket.io-client";


const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';


const sockets = {};


export function getSocket(namespace = "/") {
  if (!sockets[namespace]) {
    const user_id = localStorage.getItem("uuid");
    const code = localStorage.getItem("tutorialCode");

    sockets[namespace] = io(BACKEND_URL + namespace, {
      auth: { user_id, code },
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      timeout: 20000
    });
  }

  return sockets[namespace];
}

export function getStaffSocket() {
  return getSocket('/staff');
}


export function disconnectSocket(namespace = "/") {
  socket = sockets[namespace];
  if (socket) {
    if (namespace == "/") socket.emit("leave_tutorial");
    else if (namespace == "/staff") socket.emit("end_tutorial");

    socket.disconnect();
    delete sockets[namespace];
  }
}

export function disconnectStaffSocket() {
  return disconnectSocket('/staff');
}