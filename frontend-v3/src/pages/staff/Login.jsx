import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";


export default function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [feedback, setFeedback] = useState("");
  const [feedbackType, setFeedbackType] = useState("");

  const { login } = useAuth();

  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';
  const LOGIN_URL = `${BACKEND_URL}/user/login`;


  const loginUser = (event) => {
    event.preventDefault();

    fetch(LOGIN_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: email, password: password }),
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

          <Button variant="primary" fullWidth onClick={loginUser}>
            Login
          </Button>
        </div>
      </div>
    </div>
    // <main className="h-full">
    //   <FloatSection title={"Account Login"}>
    //     <form className="h-full flex flex-col justify-between" onSubmit={loginUser}>
    //       <div className="formInputs mb-5">
    //         <TextInput type="email" name="email" label="Email Address" value={email} setValue={setEmail} autoComplete="email" required={true} />
    //         <TextInput type="password" name="password" label="Password" value={password} setValue={setPassword} autoComplete="password" required={true} />
    //       </div>

    //       <div className="text-center">
    //         <div className={`feedback ${feedbackType}`}>{feedback}</div>
    //         <div className="formButtons grid-cols-2">
    //           <Link className="formButton buttonOutline col-span-2 sm:col-span-1" to="/register">Go to Register</Link>
    //           <button type="submit" className="formButton buttonAction col-span-2 sm:col-span-1">Login</button>
    //         </div>
    //       </div>
    //     </form>
    //   </FloatSection>
    // </main>
  );
}