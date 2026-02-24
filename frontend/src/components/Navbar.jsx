// Navbar - Top navigation bar shown on every page
// Left: site name (links to home), Right: Staff login button

import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

function Navbar() {
  const { staffAuth, _ } = useAuth();
  const location = useLocation();


  const showStaffLogin = location.pathname === "/";
  const showBackToStudent = location.pathname === "/staff/login";

  const backToStaff = location.pathname.startsWith("/staff/");
  const onTutorial = location.pathname.startsWith("/staff/tutorial/") || location.pathname.startsWith("/tutorial/");

  return (
    <nav className="nav">
      
      <div className="nav-inner">
        {onTutorial ? (
          <span className="nav-brand">Study Mates</span> // Not clickable
          ) : (
          <Link to={backToStaff ? "/staff/" : "/"} className="nav-brand">
          Study Mates
          </Link>
        )}
          
        <div className="nav-actions">
          <a
            href="https://forms.office.com/r/4x1A33ZKUX"
            target="_blank"
            rel="noopener noreferrer"
            className="nav-action"
          >
            Give Feedback
          </a>

          {showStaffLogin && (
            <Link to="/staff/login" className="nav-action">
              Staff Login
            </Link>
          )}
          {showBackToStudent && (
            <Link to="/" className="nav-action">
              Back to Student
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
