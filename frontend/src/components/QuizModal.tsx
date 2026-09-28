import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProducts, type ProductSummary } from "../api";
import { useQuiz } from "../quizContext";
import { QUIZ_QUESTIONS, recommendProducts, type QuizProfile } from "../quizData";
import Confetti from "./Confetti";
import "./QuizModal.css";

type Step = number | "results";

export default function QuizModal() {
  const { isOpen, closeQuiz } = useQuiz();
  const [step, setStep] = useState<Step>(0);
  const [profile, setProfile] = useState<QuizProfile>({});
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    // Reset to a fresh quiz each time it's opened.
    setStep(0);
    setProfile({});
    setError(null);
    fetchProducts()
      .then(setProducts)
      .catch(() => setError("Couldn't load products for your results. Try again in a bit."));
  }, [isOpen]);

  if (!isOpen) return null;

  const answer = (optionIndex: number) => {
    const question = QUIZ_QUESTIONS[step as number];
    const option = question.options[optionIndex];
    setProfile((prev) => ({
      ...prev,
      ...(option.category !== undefined ? { category: option.category } : {}),
      ...(option.color !== undefined ? { color: option.color } : {}),
      ...(option.priceBand !== undefined ? { priceBand: option.priceBand } : {}),
      ...(option.repStyle !== undefined ? { repStyle: option.repStyle } : {}),
    }));
    const next = (step as number) + 1;
    setStep(next >= QUIZ_QUESTIONS.length ? "results" : next);
  };

  const retake = () => {
    setStep(0);
    setProfile({});
  };

  const results = step === "results" ? recommendProducts(products, profile) : [];

  return (
    <div className="quiz-overlay" onClick={closeQuiz}>
      <div className="quiz-modal" onClick={(e) => e.stopPropagation()}>
        <button className="quiz-close" onClick={closeQuiz} aria-label="Close quiz">
          ×
        </button>

        {step !== "results" && (
          <>
            <div className="quiz-eyebrow">Find Your Yale Fit</div>
            <div className="quiz-progress">
              Question {(step as number) + 1} of {QUIZ_QUESTIONS.length}
            </div>
            <h2 className="quiz-prompt">{QUIZ_QUESTIONS[step as number].prompt}</h2>
            <div className="quiz-options">
              {QUIZ_QUESTIONS[step as number].options.map((opt, i) => (
                <button key={opt.label} className="quiz-option" onClick={() => answer(i)}>
                  {opt.label}
                </button>
              ))}
            </div>
          </>
        )}

        {step === "results" && (
          <div className="quiz-results">
            <Confetti />
            <div className="quiz-eyebrow">Find Your Yale Fit</div>
            <h2 className="quiz-prompt">Here's your fit! 🎉</h2>
            {error && <p className="quiz-error">{error}</p>}
            {!error && results.length === 0 && <p>Loading your picks...</p>}
            <div className="quiz-result-grid">
              {results.map((p) => (
                <Link key={p.product_id} to={`/products/${p.product_id}`} className="quiz-result-card" onClick={closeQuiz}>
                  <img src={p.image_url} alt={p.name} />
                  <div className="quiz-result-name">{p.name}</div>
                  <div className="quiz-result-price">${p.price.toFixed(2)}</div>
                </Link>
              ))}
            </div>
            <button className="quiz-retake" onClick={retake}>
              Retake the quiz
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
