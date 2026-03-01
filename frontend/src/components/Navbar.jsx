// Navbar - Top navigation bar shown on every page
// Left: site name (links to home), Right: Staff login button

import { useState } from 'react';
import { Link, useLocation } from "react-router-dom";
import Button from './Button';
import Modal from './Modal';
import { useAuth } from "../hooks/useAuth";
import QRCode from '../static/Feedback-Form-QR.svg';

function Navbar() {
  const { staffAuth, _ } = useAuth();
  const location = useLocation();

  const [showAboutModal, setShowAboutModal] = useState(false);


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
          <a className="nav-action" onClick={() => setShowAboutModal(true)}>About Us</a>

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

      {showAboutModal && (
        <Modal title="Study Mates - About Us" onClose={() => setShowAboutModal(false)}>
          <p className="mb-sm">
            <strong>Study Mates</strong> began as a Hackathon prototype last year, created to reduce problems many students in situations and assessments involving group work. Too often, your group is decided by the first table you sit at or the friends you've made in previous classes, but you rarely get an opportunity to make more meaningful connections. This can lead to mismatched expectations, clashing schedules, and uneven workloads. We believe group formation should be intentional and you're own choice, not down to luck. <strong>Study Mates</strong> was built to create fairer, more balanced teams while helping students connect with more people in their class.
            <br/><br/>
            Our platform groups students based on expected assessment GPA, current academic performance, and shared availability, increasing compatibility and accountability from the start. <strong>Study Mates</strong> runs three unique rounds of grouping so you can meet with a large range of students in the classroom. This approach encourages broader networking, diverse perspectives, and stronger academic balance by combining smart matching with structured rotation. 
          </p>
          <div className="divider flex gap-md justify-center">
            <div className="qr-code-container">
              <img src={QRCode} alt="Tutorial QR Code" className="qr-image" />
            </div>
            <a href="https://forms.office.com/r/4x1A33ZKUX" target="_blank" rel="noopener noreferrer" className="self-center">
              <Button> Share Feedback </Button>
            </a>
          </div>
        </Modal>
      )}
    </nav>
  );
}

export default Navbar;
