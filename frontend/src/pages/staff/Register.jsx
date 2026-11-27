import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Card from "../../components/Card";
import Button from "../../components/Button";
import TextInput from "../../components/TextInput";
import { MAX_USERNAME_LENGTH, MIN_PASSWORD_LENGTH, validateAccount } from "../../constants/accounts";

import { useAuth } from "../../contexts/AuthContext";


// Staff create an Account, which signs them in and lands them on the Tutorial Setup Page
export default function Register() {
  const navigate = useNavigate();
  const { isAuthenticated, signUp } = useAuth();

  const [values, setValues] = useState({ username: "", password: "", confirmPassword: "" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (isAuthenticated) navigate("/staff/", { replace: true });
  }, [isAuthenticated, navigate]);


  const set = (key) => (value) => {
    setValues((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: undefined }));
    setFormError("");
  };

  const handleSignUp = async (event) => {
    event.preventDefault();
    setFormError("");

    const { account, errors: validationErrors } = validateAccount(values);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length) return;

    setBusy(true);
    const response = await signUp(account.username, account.password);
    setBusy(false);
    if (!response.ok) setFormError(response.message);
  };


  return (
    <div className="container container-sm page">
      <Card title="Staff Sign Up" subtitle="Create an Account to run Study Mates Sessions.">
        <form className="access-option" onSubmit={handleSignUp} noValidate>
          <TextInput
            name="username"
            label="Username"
            value={values.username}
            onChange={set("username")}
            error={errors.username}
            hint="Only used to Sign In. Students can't see it."
            maxLength={MAX_USERNAME_LENGTH}
            autoComplete="username"
            autoCapitalize="none"
          />

          <TextInput
            name="password"
            label="Password"
            value={values.password}
            onChange={set("password")}
            error={errors.password}
            hint={`At least ${MIN_PASSWORD_LENGTH} Characters. Keep it Safe, as it can't be recovered.`}
            password={true}
            autoComplete="new-password"
          />

          <TextInput
            name="confirm-password"
            label="Confirm Password"
            value={values.confirmPassword}
            onChange={set("confirmPassword")}
            error={errors.confirmPassword}
            password={true}
            autoComplete="new-password"
          />

          {formError && <p className="input-error mb-sm" role="alert">{formError}</p>}

          <Button type="submit" variant="primary" fullWidth disabled={busy}>
            {busy ? "Signing Up…" : "Sign Up"}
          </Button>
        </form>

        <p className="access-switch">
          Already have an Account? <Link to="/staff/login">Sign In</Link>
        </p>
      </Card>
    </div>
  );
}
