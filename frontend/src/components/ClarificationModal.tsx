// src/components/ClarificationModal.tsx
import { useState } from "react";

interface Props {
  question: string;
  onSubmit: (answer: string) => void;
  onCancel: () => void;
}

export default function ClarificationModal({ question, onSubmit, onCancel }: Props) {
  const [answer, setAnswer] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(answer.trim());
    setAnswer("");
  };

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 shadow-lg">
        <h2 className="text-lg font-medium mb-4 text-primary-600">We need a little more info</h2>
        <p className="mb-4">{question}</p>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="text"
            className="input-primary w-full"
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            required
          />
          <div className="flex justify-end space-x-3">
            <button type="button" onClick={onCancel} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Submit
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
