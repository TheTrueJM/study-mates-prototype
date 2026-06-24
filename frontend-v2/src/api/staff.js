import axios from "axios";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

let staffToken = localStorage.getItem("staff_token");

export function getStaffToken() {
    return staffToken;
}

export function setStaffToken(token) {
    staffToken = token;
    localStorage.setItem("staff_token", token);
}

export function clearStaffToken() {
    staffToken = null;
    localStorage.removeItem("staff_token");
}

export async function login(username, password) {
    const response = await axios.post(`${BACKEND_URL}/api/staff/login`, {
        username,
        password
    });
    setStaffToken(response.data.token);
    return response.data;
}

export async function createTutorial(data) {
    const response = await axios.post(`${BACKEND_URL}/api/staff/create-tutorial`, data, {
        headers: { Authorization: `Bearer ${staffToken}` }
    });
    return response.data;
}

export async function endTutorial(code) {
    await axios.post(`${BACKEND_URL}/api/staff/end-tutorial`, { code }, {
        headers: { Authorization: `Bearer ${staffToken}` }
    });
}