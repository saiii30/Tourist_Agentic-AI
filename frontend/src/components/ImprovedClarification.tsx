// src/components/ImprovedClarification.tsx
import { useState } from "react";

/**
 * A lightweight chat‑style questionnaire that asks a series of questions
 * one after another without closing the modal between each step.
 *
 * `questions` – array of strings the agent wants answered.
 * `onComplete` – called with an object mapping each question to the user's answer.
 */
interface Props {
  questions: string[];
  onComplete: (answers: Record<string, string>) => void;
  onCancel?: () => void;
}

export default function ImprovedClarification({ questions, onComplete, onCancel }: Props) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [temp, setTemp] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = questions[currentIdx];
    const newAnswers = { ...answers, [q]: temp.trim() };
    setAnswers(newAnswers);
    setTemp("");
    if (currentIdx + 1 < questions.length) {
      setCurrentIdx(currentIdx + 1);
    } else {
      onComplete(newAnswers);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 shadow-lg">
        <h2 className="text-lg font-medium mb-4 text-primary-600">We need a little more info</h2>
        <p className="mb-3">{questions[currentIdx]}</p>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="text"
            className="input-primary w-full"
            value={temp}
            onChange={(e) => setTemp(e.target.value)}
            required
          />
          <div className="flex justify-end space-x-3">
            {onCancel && (
              <button type="button" onClick={onCancel} className="btn-secondary">
                Cancel
              </button>
            )}
            <button type="submit" className="btn-primary">
              {currentIdx + 1 < questions.length ? "Next" : "Submit"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
