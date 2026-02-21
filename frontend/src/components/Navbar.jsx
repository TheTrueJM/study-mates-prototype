// Navbar - Top navigation bar shown on every page
// Left: site name (links to home), Right: Staff login button

import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

function Navbar() {
  const { staffAuth, _ } = useAuth();
  const location = useLocation();

  const showBackToStudent = location.pathname === "/staff/login" && !staffAuth;
  const showStaffLogin = location.pathname === "/";

  return (
    <nav className="nav">
      <div className="nav-inner">
        <Link to="/" className="nav-brand">
          Study Mates
        </Link>

        {showBackToStudent && (
          <Link to="/" className="nav-action">
            Back to Student
          </Link>
        )}

        {showStaffLogin && !staffAuth && (
          <Link to="/staff/login" className="nav-action">
            Staff Login
          </Link>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
