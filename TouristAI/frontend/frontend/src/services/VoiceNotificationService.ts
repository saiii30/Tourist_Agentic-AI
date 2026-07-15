class VoiceNotificationService {
  private static instance: VoiceNotificationService;
  private speechQueue: Array<{ text: string; callback?: () => void }> = [];
  private isSpeaking: boolean = false;

  private constructor() {}

  public static getInstance(): VoiceNotificationService {
    if (!VoiceNotificationService.instance) {
      VoiceNotificationService.instance = new VoiceNotificationService();
    }
    return VoiceNotificationService.instance;
  }

  /**
   * Speak a text string. Handles queueing to prevent overlapping speech.
   */
  public speak(text: string, callback?: () => void): void {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      console.warn("Speech Synthesis is not supported in this browser.");
      if (callback) callback();
      return;
    }

    this.speechQueue.push({ text, callback });
    this.processQueue();
  }

  private processQueue(): void {
    if (this.isSpeaking || this.speechQueue.length === 0) return;

    this.isSpeaking = true;
    const { text, callback } = this.speechQueue.shift()!;

    // Clean up basic markdown and structure for clear pronunciation
    const cleanText = text
      .replace(/[*#_~`\[\]()]/g, "")
      .replace(/[-+•]\s+/g, "")
      .replace(/:\s*(\n|$)/g, ". ")
      .replace(/\n+/g, ". ");

    // Create browser utterance
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = "en-IN"; // English (India) accent as standard, or default to en-US if not found
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => {
      this.isSpeaking = false;
      if (callback) callback();
      // Process next item in queue
      this.processQueue();
    };

    utterance.onerror = (e) => {
      console.error("Speech Synthesis Error:", e);
      this.isSpeaking = false;
      if (callback) callback();
      this.processQueue();
    };

    window.speechSynthesis.speak(utterance);
  }

  public pause(): void {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.pause();
    }
  }

  public resume(): void {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.resume();
    }
  }

  /**
   * Cancel all speech and clear queue
   */
  public stop(): void {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      this.speechQueue = [];
      this.isSpeaking = false;
    }
  }
}

export default VoiceNotificationService;
export { VoiceNotificationService };
