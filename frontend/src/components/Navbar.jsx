import { startTransition, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { useTutorial } from "../contexts/TutorialContext";

import Modal from "./Modal";
import ConfirmDialog from "./ConfirmDialog";

import QRCode from "/static/Feedback-Form-QR.svg";


function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  const { isAuthenticated, isGuest, username, logout } = useAuth();
  const { namespace, tutorialCode, endTutorial } = useTutorial();

  const [showAboutModal, setShowAboutModal] = useState(false);
  const [confirmLogout, setConfirmLogout] = useState(false);

  const onStudentHome = location.pathname === "/" || location.pathname === "/join";
  const onStaffPage = location.pathname.startsWith("/staff");
  const hasActiveSession = namespace === "/staff" && !!tutorialCode;


  const staffLogout = async () => {
    if (hasActiveSession) await endTutorial();
    setConfirmLogout(false);
    // Navigation is applied as a transition, so signing out is too, letting both happen together
    // (otherwise the protected staff page would redirect to the staff access page first)
    navigate("/");
    startTransition(logout);
  };

  const handleLogout = () => {
    if (hasActiveSession) setConfirmLogout(true);
    else staffLogout();
  };


  return (
    <nav className="nav">
      <div className="nav-inner">
        {/* TODO: Update to be Domain Name */}
        <span className="nav-brand">Study Mates</span>

        <div className="nav-actions">
          <button type="button" className="nav-action" onClick={() => setShowAboutModal(true)}>About</button>

          {onStudentHome && (
            <button
              type="button"
              className="nav-action"
              onClick={() => navigate(isAuthenticated ? "/staff/" : "/staff/login")}
            >
              Staff
            </button>
          )}
          {onStaffPage && (
            isAuthenticated ? (
              <>
                {(isGuest || username) && (
                  <span className="nav-identity" title={isGuest ? "Using Study Mates as a Guest" : `Signed in as ${username}`}>
                    {isGuest ? "Guest" : username}
                  </span>
                )}
                <button type="button" className="nav-action" onClick={handleLogout}>Sign Out</button>
              </>
            ) : (
              <button type="button" className="nav-action" onClick={() => navigate("/")}>Student Home</button>
            )
          )}
        </div>
      </div>

      {/* TODO: Improve Handling of Modals */}
      <Modal title="Study Mates - About Us [OLD]" isOpen={showAboutModal} onClose={() => setShowAboutModal(false)}>
        {/* TODO: Include Link/URL of Application */}
        <p className="mb-sm">
          <strong>Study Mates</strong> began as a Hackathon prototype last year, created to reduce problems many students face in situations and assessments involving group work. Too often, your group is decided by the first table you sit at or the friends you've made in previous classes, but you rarely get an opportunity to make more meaningful connections. This can lead to mismatched expectations, clashing schedules, and uneven workloads. We believe group formation should be intentional and your own choice, not down to luck. <strong>Study Mates</strong> was built to create fairer, more balanced teams while helping students connect with more people in their class.
          <br/><br/>
          Our platform groups students based on expected assessment GPA, current academic performance, shared availability, and how they prefer to meet and communicate, increasing compatibility and accountability from the start. <strong>Study Mates</strong> runs three unique rounds of grouping so you can meet with a large range of students in the classroom. This approach encourages broader networking, diverse perspectives, and stronger academic balance by combining smart matching with structured rotation.
        </p>
        {/* TODO: Update Forms, Links, and QR */}
        <div className="divider flex gap-md justify-center items-center flex-wrap">
          <div className="qr-code-container">
            <img src={QRCode} alt="Feedback Form QR Code" className="qr-image" />
          </div>
          <a href="https://forms.office.com/r/4x1A33ZKUX" target="_blank" rel="noopener noreferrer" className="btn btn-primary">
            Share Feedback
          </a>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={confirmLogout}
        title="Sign Out and End Session?"
        message="Signing out will end your Running Tutorial Session and remove all Students from it."
        confirmLabel="End Session and Sign Out"
        danger
        onConfirm={staffLogout}
        onCancel={() => setConfirmLogout(false)}
      />
    </nav>
  );
}

export default Navbar;
