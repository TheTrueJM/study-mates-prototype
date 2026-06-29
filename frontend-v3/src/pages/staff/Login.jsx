import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Card from "../../components/Card";
import Button from '../../components/Button';
import TextInput from "../../components/TextInput";

import { useAuth } from "../../contexts/AuthContext";


export default function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [feedback, setFeedback] = useState("");
  const [feedbackType, setFeedbackType] = useState("");

  const { login } = useAuth();

  const LOGIN_URL = "/staff/login";


  const loginUser = (event) => {
    event.preventDefault();

    fetch(LOGIN_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    })
      .then(async response => {
        const data = await response.json();
        if (!response.ok || data.error) {
          throw new Error(`Error: ${data.message || "HTTP " + response.status}`);
        }
        return data;
      })
      .then(data => {
        login(data.token);
        setFeedback("Account login successful. Redirecting...");
        setFeedbackType("success");
        setTimeout(() => navigate("/staff/"), 2500);
      })
      .catch(error => {
        setFeedback(error.message);
        setFeedbackType("error");
      });
  };

  
  return (
    <div className="container container-sm mt-lg">
      <Card title="Staff Login">
        <div className="flex-col gap-md" style={{ display: 'flex' }}>
          {/* Staff Username Input */}
          <TextInput
            name="username"
            label="Enter Username"
            onChange={setUsername}
            placeholder="Username..."
          />

          {/* Staff Password Input */}
          <TextInput
            name="password"
            label="Enter Password"
            type="password"
            onChange={setPassword}
            placeholder="Password..."
            password={true}
          />

          <Button variant="primary" fullWidth onClick={loginUser}>
            Login
          </Button>
        </div>
      </Card>
    </div>

    // <div className="text-center">
    //   <div className={`feedback ${feedbackType}`}>{feedback}</div>
    //   <div className="formButtons grid-cols-2">
    //     <Link className="formButton buttonOutline col-span-2 sm:col-span-1" to="/register">Go to Register</Link>
    //     <button type="submit" className="formButton buttonAction col-span-2 sm:col-span-1">Login</button>
    //   </div>
    // </div>
  );
}