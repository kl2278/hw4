import { useEffect, useState } from "react";
import { useQuiz } from "../quizContext";
import "./QuizTeaser.css";

const SESSION_KEY = "campus-customs-quiz-teaser-shown";
const DELAY_MS = 6000;

export default function QuizTeaser() {
  const { openQuiz } = useQuiz();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (sessionStorage.getItem(SESSION_KEY)) return;
    const timer = setTimeout(() => {
      sessionStorage.setItem(SESSION_KEY, "1");
      setVisible(true);
    }, DELAY_MS);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className="quiz-teaser">
      <button className="quiz-teaser-close" onClick={() => setVisible(false)} aria-label="Dismiss">
        ×
      </button>
      <p className="quiz-teaser-text">Not sure what to get? Take the 30-second quiz!</p>
      <button
        className="quiz-teaser-cta"
        onClick={() => {
          setVisible(false);
          openQuiz();
        }}
      >
        Find Your Yale Fit →
      </button>
    </div>
  );
}
