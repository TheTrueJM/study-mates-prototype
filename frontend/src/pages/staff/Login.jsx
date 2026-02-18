// Login - Staff enters their username and password to authetnicate

import { useState } from 'react';
import { useNavigate } from "react-router-dom";
import Input from '../../components/Input';
import Button from '../../components/Button';

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();  

  const handleLogin= async () => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

    const apiPost = (endpoint, payload) =>
      fetch(`${BACKEND_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      }).then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || res.statusText);
        return data;
      });

    try {
      await apiPost("/staff/login", { username, password });
      navigate("/staff/");
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="container container-sm mt-lg">
      <div className="card">
        <h1 className="card-header">Staff Login</h1>

        <div className="flex-col gap-md" style={{ display: 'flex' }}>
          {/* Staff username input */}
          <Input
            label="Enter Username"
            onChange={setUsername}
            placeholder="Username..."
          />

          {/* Password username input */}
          <Input
            label="Enter Password"
            type="password"
            onChange={setPassword}
            placeholder="Password..."
          />

          <Button variant="primary" fullWidth onClick={handleLogin}>
            Login
          </Button>
        </div>
      </div>
    </div>
  );
}

export default Login;
