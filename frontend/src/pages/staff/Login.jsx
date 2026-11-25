import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Card from "../../components/Card";
import Button from "../../components/Button";
import TextInput from "../../components/TextInput";

import { useAuth } from "../../contexts/AuthContext";


// Staff choose to continue as a Guest or Sign In to an Account, before landing on the Tutorial Setup Page
export default function Login() {
  const navigate = useNavigate();
  const { isAuthenticated, continueAsGuest, signIn } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [guestError, setGuestError] = useState("");
  const [busy, setBusy] = useState(""); // "" | guest | account

  useEffect(() => {
    if (isAuthenticated) navigate("/staff/", { replace: true });
  }, [isAuthenticated, navigate]);


  const handleGuest = async () => {
    setBusy("guest");
    setGuestError("");
    const response = await continueAsGuest();
    setBusy("");
    if (!response.ok) setGuestError(response.message);
  };

  const handleSignIn = async (event) => {
    event.preventDefault();

    if (!username.trim() || !password) {
      setError("Enter your Username and Password.");
      return;
    }

    setBusy("account");
    setError("");
    const response = await signIn(username.trim(), password);
    setBusy("");
    if (!response.ok) setError(response.message);
  };


  return (
    <div className="container container-sm page">
      <Card title="Staff Access" subtitle="Run a Study Mates Session for your Tutorial.">
        <section className="access-option">
          <h2 className="access-option-title">Continue as a Guest</h2>
          <p className="text-muted">Start a Session straight away. No Account Needed.</p>
          {guestError && <p className="input-error" role="alert">{guestError}</p>}
          <Button variant="primary" fullWidth onClick={handleGuest} disabled={!!busy}>
            {busy === "guest" ? "Starting…" : "Continue as Guest"}
          </Button>
        </section>

        <div className="access-divider" role="separator"><span>or</span></div>

        <form className="access-option" onSubmit={handleSignIn} noValidate>
          <h2 className="access-option-title">Sign In to your Account</h2>

          <TextInput
            name="username"
            label="Username"
            value={username}
            onChange={(value) => {
              setUsername(value);
              setError("");
            }}
            autoComplete="username"
            autoCapitalize="none"
          />

          <TextInput
            name="password"
            label="Password"
            value={password}
            onChange={(value) => {
              setPassword(value);
              setError("");
            }}
            password={true}
            autoComplete="current-password"
          />

          {error && <p className="input-error mb-sm" role="alert">{error}</p>}

          <Button type="submit" variant="outline" fullWidth disabled={!!busy}>
            {busy === "account" ? "Signing In…" : "Sign In"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
