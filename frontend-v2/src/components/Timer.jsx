import { useState, useEffect } from "react";

export default function Timer({ timer }) {
    const [timeLeft, setTimeLeft] = useState(timer?.remaining || 0);
    const [phase, setPhase] = useState(timer?.phase || null);

    useEffect(() => {
        if (timer) {
            setTimeLeft(timer.remaining);
            setPhase(timer.phase);
        }
    }, [timer]);

    useEffect(() => {
        let interval = null;
        if (timeLeft > 0) {
            interval = setInterval(() => {
                setTimeLeft(timeLeft - 1);
            }, 1000);
        } else if (interval) {
            clearInterval(interval);
        }

        return () => clearInterval(interval);
    }, [timeLeft]);

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="timer">
            <h3>{phase === "intro" ? "Intro Timer" : "Discussion Timer"}</h3>
            <p>{formatTime(timeLeft)}</p>
        </div>
    );
}