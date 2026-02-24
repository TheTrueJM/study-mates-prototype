// EnterDetails - Student inputs GPA info and availability times

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import Card from '../../components/Card';
import Input from '../../components/Input';
import Button from '../../components/Button';

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const TIMES = ["Morning", "Afternoon", "Evening"];

function EnterDetails() {
  const [goalGPA, setGoalGPA] = useState("");
  const [currentGPA, setCurrentGPA] = useState("");
  const [noGPAYet, setNoGPAYet] = useState(false);
  const [availableDays, setAvailableDays] = useState(
    DAYS.map((day) => ({ day, times: [] }))
  );
  const navigate = useNavigate();
  const { setStudent } = useAuth();

  // Toggle a time slot on/off for a given day
  const toggleTime = (dayIndex, time) => {
    const newDays = [...availableDays];
    const current = newDays[dayIndex].times;

    newDays[dayIndex] = {
      ...newDays[dayIndex],
      times: current.includes(time)
        ? current.filter((t) => t !== time)
        : [...current, time],
    };
    setAvailableDays(newDays);
  };

  const handleConfirm = async () => {
    if (isNaN(parseFloat(goalGPA)) || parseFloat(goalGPA) < 0 || parseFloat(goalGPA) > 7.0) {
      alert("Please enter a valid goal GPA.");
      return;
    }

    if ((isNaN(parseFloat(currentGPA)) && !noGPAYet) || parseFloat(currentGPA) < 0 || parseFloat(currentGPA) > 7.0) {
      alert("Please enter a valid current GPA or select no GPA.");
      return;
    }

    // Build availability codes according to format
    const availability = [];
    availableDays.forEach((slot, dayIndex) => {
      slot.times.forEach((time) => {
        const code = `${DAYS[dayIndex].slice(0,3)}${time[0]}`;
        availability.push(code);
      });
    });

    if (availability.length === 0) {
      const proceed = window.confirm("You did not select any available times. Submit anyway?");
      if (!proceed) return;
    }

    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

    const apiPost = (endpoint, payload) =>
      fetch(`${BACKEND_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      }).then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || res.statusText);
        return data;
      });

    try {
      await apiPost("/details", {
        currentGPA: noGPAYet ? 4.5 : currentGPA,
        goalGPA,
        availability
      });
      
      // Update frontend state
      setStudent({
        currentGPA: noGPAYet ? 4.5 : parseFloat(currentGPA),
        goalGPA: parseFloat(goalGPA),
        availability
      });
      
      navigate("/join");
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="container container-md mt-lg">
      <Card title="Tutorial Session">
        {/* GPA inputs */}
        <Input
          label="Goal GPA for this Unit"
          type="number"
          value={goalGPA}
          min={0}
          max={7}
          step={0.1}
          onChange={setGoalGPA}
          placeholder="e.g. 4.0"
        />

        <Input
          label="Current or Recent GPA"
          type="number"
          value={currentGPA}
          min={0}
          max={7}
          step={0.1}
          onChange={setCurrentGPA}
          placeholder="e.g. 4.0"
          disabled={noGPAYet}
        />

        <div className="checkbox-group">
          <input
            type="checkbox"
            id="noGPAYet"
            checked={noGPAYet}
            onChange={(e) => setNoGPAYet(e.target.checked)}
          />
          <label htmlFor="noGPAYet">Don't have a GPA yet?</label>
        </div>

        {/* Availability time selection grid */}
        <div className="mt-md">
          <label className="input-label">Availability Times</label>

          <div className="flex-col gap-xs" style={{ display: "flex" }}>
            {availableDays.map((slot, dayIndex) => (
              <div key={dayIndex} className="availability-row">
                <span className="day-label">{slot.day}</span>

                {TIMES.map((time) => (
                  <button
                    key={time}
                    className={`btn-toggle ${
                      slot.times.includes(time) ? "active" : ""
                    }`}
                    onClick={() => toggleTime(dayIndex, time)}
                  >
                    {time}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div className="mt-md">
          <Button variant="primary" fullWidth onClick={handleConfirm}>
            Confirm Details
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default EnterDetails;
