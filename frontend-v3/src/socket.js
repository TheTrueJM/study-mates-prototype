import { io } from "socket.io-client";


let socket = null;
let currentNamespace = null;

export function getSocket(namespace = "/") {
  if (!socket) {
    const user_id = localStorage.getItem("uuid");
    const code = localStorage.getItem("tutorialCode");

    currentNamespace = namespace;
    socket = io("/socket.io" + currentNamespace, {
      auth: { user_id, code },
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      timeout: 20000
    });
  }

  console.log("Socket: ", socket);

  return socket;
}

export function disconnectSocket() {
  if (socket) {
    if (currentNamespace === "/") socket.emit("leave_tutorial");
    else if (currentNamespace === "/staff") socket.emit("end_tutorial");

    socket.disconnect();
    socket = null;
    currentNamespace = null;
  }
}