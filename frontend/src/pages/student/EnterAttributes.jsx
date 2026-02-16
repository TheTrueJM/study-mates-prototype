// EnterAttributes - Student inputs GPA info and availability times

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../../components/Card';
import Input from '../../components/Input';
import Button from '../../components/Button';

const TIME_SLOTS = ["Morning", "Afternoon", "Evening"];
const DAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

function EnterAttributes() {
  const [gradeExpectation, setGradeExpectation] = useState("");
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

  const handleConfirm = () => {
    // Build availability codes according to backend enum format
    const DAY_CODES = ['MON','TUE','WED','THU','FRI','SAT','SUN'];
    const PERIOD_MAP = { Morning: 'M', Afternoon: 'A', Evening: 'N' };

    const params = new URLSearchParams();
    params.append('currentGPA', currentGPA || '0');
    params.append('goalGPA', gradeExpectation || '4.0');

    availableDays.forEach((slot, dayIndex) => {
      slot.times.forEach((time) => {
        const code = `${DAY_CODES[dayIndex]}${PERIOD_MAP[time]}`;
        params.append('availability', code);
      });
    });

    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

    fetch(`${BACKEND_URL}/details`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params,
      credentials: 'include',
    }).then(() => {
      navigate('/waiting');
    }).catch(err => console.error(err));
  };

  return (
    <div className="container container-md mt-lg">
      <Card title="Tutorial Session ABCD-1234">
        {/* GPA inputs */}
        <Input
          label="Goal GPA for Unit"
          type="number"
          value={gradeExpectation}
          onChange={setGradeExpectation}
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

                {TIME_SLOTS.map((time) => (
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
            Confirm Attributes
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default EnterAttributes;
