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

      <Modal title="About Study Mates" isOpen={showAboutModal} onClose={() => setShowAboutModal(false)}>
        <div className="about-text mb-sm">
          <p>
            <strong>Study Mates</strong> began as a team Hackathon prototype in 2025, built to tackle a problem almost
            every university student runs into: group work. Too often, your group is decided by whoever sits at your
            table or the friends you've made in previous classes, rather than people whose goals, schedules, and ways
            of working match your own. That leads to mismatched expectations, clashing timetables, and uneven workloads.
            We believe forming a group should be intentional, and a chance to meet more of your class, not down to luck.
          </p>
          <p>
            Since then, we've kept developing it into a tool that tutors can run in any class. Students join anonymously
            with a code, with no accounts or personal details needed, and can share details like the grade they're
            aiming for, when they're available, and how they like to meet and communicate. <strong>Study Mates</strong>
            then matches everyone into balanced groups over several rounds, starting each round with quick introductions
            and discussion prompts, while avoiding rematches so you meet as many classmates as possible.
          </p>
          <p>
            By the end of the session, you'll have met a diverse range of students in your class. You can look back on
            who you met, and (when possible) shortlist the people you'd like to team up with, so finding great teammates
            for your next group assessment is easy.
          </p>
        </div>
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
