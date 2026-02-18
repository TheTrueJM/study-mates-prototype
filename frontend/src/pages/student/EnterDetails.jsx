// EnterDetails - Student inputs GPA info and availability times

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
    // Build availability codes according to format
    const availability = [];
    availableDays.forEach((slot, dayIndex) => {
      slot.times.forEach((time) => {
        const code = `${DAYS[dayIndex].slice(0,3)}${time[0]}`;
        availability.push(code);
      });
    });

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
      navigate("/join");
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="container container-md mt-lg">
      <Card title="Tutorial Session ABCD-1234">
        {/* GPA inputs */}
        <Input
          label="Goal GPA for Unit"
          type="number"
          value={goalGPA}
          onChange={setGoalGPA}
          placeholder="e.g. 4.0"
        />

        <Input
          label="Current or Most Recent GPA"
          type="number"
          value={currentGPA}
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
