import { io } from "socket.io-client";

const sockets = {};

export function getSocket(namespace = "/") {
  if (sockets[namespace]) {
    return sockets[namespace];
  }

  const uuid = localStorage.getItem("uuid");
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';
  const url = namespace === "/" ? `${BACKEND_URL}` : `${BACKEND_URL}${namespace}`;

  const socket = io(url, {
    auth: { uuid },
    withCredentials: true,
    transports: ["websocket"],
    path: '/socket.io',
  });

  socket.on("connect", () => {
    console.log(socket)
    console.info("socket connected", namespace, socket.id);
  });

  socket.on("connect_error", (err) => {
    console.error("socket connect_error", namespace, err);
  });

  socket.on("session", (data) => {
    if (data && data.uuid) {
      localStorage.setItem("uuid", data.uuid);
    }
  });

  sockets[namespace] = socket;
  return socket;
}

export function getStaffSocket() {
  return getSocket('/staff');
}

export function disconnectSocket(namespace = "/") {
  const s = sockets[namespace];
  if (s) {
    try { s.disconnect(); } catch (e) {}
    delete sockets[namespace];
  }
}
