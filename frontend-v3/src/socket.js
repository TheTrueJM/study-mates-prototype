import { io } from "socket.io-client";


const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';


let socket = null;
let currentNamespace = null;

export function getSocket(namespace = "/") {
  if (!socket) {
    const user_id = localStorage.getItem("uuid");
    const code = localStorage.getItem("tutorialCode");

    currentNamespace = namespace;
    socket = io(BACKEND_URL + currentNamespace, {
      auth: { user_id, code },
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      timeout: 20000
    });
  }

  return socket;
}

export function disconnectSocket() {
  if (socket) {
    if (currentNamespace === "/") socket.emit("leave_tutorial");
    else if (currentNamespace === "/staff") socket.emit("end_tutorial");

    socket.disconnect();
    delete socket;
    currentNamespace = null;
  }
}