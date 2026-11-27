import { Link } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";


function NotFound() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="container container-md page">
      <div className="card text-center">
        <h1 style={{ fontSize: "4rem", margin: "0.5rem 0", color: "var(--color-primary)" }}>404</h1>
        <h2 style={{ margin: "1rem 0" }}>Page Not Found</h2>
        <p className="text-muted mb-lg">
          Sorry, the page you're looking for does not exist.
        </p>
        <Link to={isAuthenticated ? "/staff/" : "/"} className="btn btn-primary">
          Return Home
        </Link>
      </div>
    </div>
  );
}

export default NotFound;
