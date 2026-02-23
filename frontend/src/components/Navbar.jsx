// Navbar - Top navigation bar shown on every page
// Left: site name (links to home), Right: Staff login button

import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

function Navbar() {
  const { staffAuth, _ } = useAuth();
  const location = useLocation();


  const showStaffLogin = location.pathname === "/";
  const showBackToStudent = location.pathname === "/staff/login";

  const backToStaff = location.pathname === "/staff/"; 
  const onTutorial = location.pathname.startsWith("/staff/tutorial");
  return (
    <nav className="nav">
      

      <div className="nav-inner">
        {onTutorial ? (
          <span className="nav-brand">Study Mates</span> // Not clickable
          ) : (
          <Link to={backToStaff ? "/staff/login" : "/"} className="nav-brand">
          Study Mates
          </Link> )}
          

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
    </nav>
  );
}

export default Navbar;
