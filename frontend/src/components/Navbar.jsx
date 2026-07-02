import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { useTutorial } from "../contexts/TutorialContext";

import Button from "./Button";
import Modal from "./Modal";

import QRCode from "/static/Feedback-Form-QR.svg";


function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  const { isAuthenticated, logout } = useAuth();
  const { switchToStudent, switchToStaff, endTutorial } = useTutorial();

  const [showAboutModal, setShowAboutModal] = useState(false);

  const onStudentHome = location.pathname === "/";
  const onStaffPage = location.pathname.startsWith("/staff/");


  const handleStaff = () => {
    switchToStaff();
    navigate("/staff/login");
  }

  const handleStudent = () => {
    switchToStudent();
    navigate("/");
  }

  const staffLogout = () => {
    endTutorial();
    logout();
    handleStudent();
  }


  return (
    <nav className="nav">
      <div className="nav-inner">
        {/* TODO: Update to be Domain Name */}
        <span className="nav-brand">Study Mates</span>
          
        <div className="nav-actions">
          <a className="nav-action" onClick={() => setShowAboutModal(true)}>About Us</a>

          {onStudentHome && (
            <a className="nav-action" onClick={() => handleStaff()}>Staff Login</a>
          )}
          {onStaffPage && (
            <>
              {isAuthenticated ? (
                <a className="nav-action" onClick={() => staffLogout()}>Staff Logout</a>
              ) : (
                <a className="nav-action" onClick={() => handleStudent()}>Back to Student</a>
              )}
            </>
          )}
        </div>
      </div>

      {/* TODO: Improve Handling of Modals */}
      {showAboutModal && (
        <Modal title="Study Mates - About Us [OLD]" onClose={() => setShowAboutModal(false)}>
          {/* TODO: Include Link/URL of Application */}
          <p className="mb-sm">
            <strong>Study Mates</strong> began as a Hackathon prototype last year, created to reduce problems many students in situations and assessments involving group work. Too often, your group is decided by the first table you sit at or the friends you"ve made in previous classes, but you rarely get an opportunity to make more meaningful connections. This can lead to mismatched expectations, clashing schedules, and uneven workloads. We believe group formation should be intentional and you"re own choice, not down to luck. <strong>Study Mates</strong> was built to create fairer, more balanced teams while helping students connect with more people in their class.
            <br/><br/>
            Our platform groups students based on expected assessment GPA, current academic performance, and shared availability, increasing compatibility and accountability from the start. <strong>Study Mates</strong> runs three unique rounds of grouping so you can meet with a large range of students in the classroom. This approach encourages broader networking, diverse perspectives, and stronger academic balance by combining smart matching with structured rotation. 
          </p>
          {/* TODO: Update Forms, Links, and QR */}
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
