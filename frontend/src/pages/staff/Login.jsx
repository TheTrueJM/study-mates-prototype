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
    try {
      const response = await fetch(
        `http://localhost:5000/staff/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username,
            password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.error);
        return;
      }

      navigate("/staff/");
    } catch (error) {
      console.error("Login error:", error);
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
