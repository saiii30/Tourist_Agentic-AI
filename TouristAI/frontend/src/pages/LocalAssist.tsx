import { useEffect, useMemo, useState } from "react";
import { ArrowRightLeft, BadgeCheck, Heart, Languages, MessageCircle, Mic, ShieldAlert, Sparkles, Square, Volume2, WifiOff } from "lucide-react";
import { apiUrl } from "../api/config";

type Language = { code: string; name: string; speech: string };
type Phrase = { id: string; category: string; source_text: string; translated_text: string; transliteration?: string; verified?: boolean };
type Translation = { original: string; translated: string; source: string; target: string; provider: string; transliteration?: string };
type OfflinePhrase = { id: string; category: string; en: string; ta: string; hi: string };

const DEFAULT_LANGUAGES: Language[] = [
  { code: "en", name: "English", speech: "en-IN" },
  { code: "ta", name: "Tamil", speech: "ta-IN" },
  { code: "hi", name: "Hindi", speech: "hi-IN" },
  { code: "te", name: "Telugu", speech: "te-IN" },
  { code: "ml", name: "Malayalam", speech: "ml-IN" },
  { code: "kn", name: "Kannada", speech: "kn-IN" },
  { code: "mr", name: "Marathi", speech: "mr-IN" },
  { code: "bn", name: "Bengali", speech: "bn-IN" },
];

const categoryEmoji: Record<string, string> = {
  Taxi: "🚕", "Bus/Train": "🚆", Restaurant: "🍽️", Hotel: "🏨", Shopping: "🛍️", Emergency: "🚨", Medical: "🩺", Directions: "🧭",
};

const OFFLINE_PHRASES: OfflinePhrase[] = [
  { id: "taxi-station", category: "Taxi", en: "Please take me to the railway station.", ta: "தயவுசெய்து என்னை ரயில் நிலையத்திற்கு அழைத்துச் செல்லுங்கள்.", hi: "कृपया मुझे रेलवे स्टेशन ले चलिए।" },
  { id: "taxi-fare", category: "Taxi", en: "How much will the fare be?", ta: "கட்டணம் எவ்வளவு ஆகும்?", hi: "किराया कितना होगा?" },
  { id: "food-veg", category: "Restaurant", en: "I would like vegetarian food.", ta: "எனக்கு சைவ உணவு வேண்டும்.", hi: "मुझे शाकाहारी खाना चाहिए।" },
  { id: "hotel-checkin", category: "Hotel", en: "I have a reservation. I would like to check in.", ta: "எனக்கு முன்பதிவு உள்ளது. நான் செக்-இன் செய்ய விரும்புகிறேன்.", hi: "मेरी बुकिंग है। मैं चेक-इन करना चाहता/चाहती हूँ।" },
  { id: "shopping-price", category: "Shopping", en: "How much does this cost?", ta: "இது எவ்வளவு விலை?", hi: "इसकी कीमत कितनी है?" },
  { id: "emergency-hospital", category: "Emergency", en: "I need a hospital. Please call an ambulance.", ta: "எனக்கு மருத்துவமனை தேவை. தயவுசெய்து ஆம்புலன்ஸை அழைக்கவும்.", hi: "मुझे अस्पताल जाना है। कृपया एम्बुलेंस बुलाइए।" },
  { id: "direction-help", category: "Directions", en: "Can you show me this place on the map?", ta: "இந்த இடத்தை வரைபடத்தில் காட்ட முடியுமா?", hi: "क्या आप मुझे यह जगह नक्शे पर दिखा सकते हैं?" },
];

const offlinePhrasebook = (source: string, target: string): Phrase[] => {
  const sourceCode = source === "ta" || source === "hi" ? source : "en";
  const targetCode = target === "ta" || target === "hi" ? target : "en";
  return OFFLINE_PHRASES.map((phrase) => ({
    id: phrase.id,
    category: phrase.category,
    source_text: phrase[sourceCode],
    translated_text: phrase[targetCode],
  }));
};

export default function LocalAssist() {
  const [languages, setLanguages] = useState(DEFAULT_LANGUAGES);
  const [source, setSource] = useState("en");
  const [target, setTarget] = useState("ta");
  const [text, setText] = useState("");
  const [result, setResult] = useState("");
  const [transliteration, setTransliteration] = useState("");
  const [provider, setProvider] = useState("");
  const [warning, setWarning] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [phrases, setPhrases] = useState<Phrase[]>([]);
  const [category, setCategory] = useState("All");
  const [history, setHistory] = useState<Translation[]>([]);
  const [conversationMode, setConversationMode] = useState(false);
  const [favorites, setFavorites] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem("local-assist-favorites") || "[]"); } catch { return []; }
  });
  const [offline, setOffline] = useState(() => !navigator.onLine);

  const sourceLanguage = languages.find((item) => item.code === source) || DEFAULT_LANGUAGES[0];
  const targetLanguage = languages.find((item) => item.code === target) || DEFAULT_LANGUAGES[1];
  const categories = useMemo(() => ["All", "Favorites", ...Array.from(new Set(phrases.map((p) => p.category)))], [phrases]);
  const shownPhrases = category === "All" ? phrases : category === "Favorites" ? phrases.filter((phrase) => favorites.includes(phrase.id)) : phrases.filter((phrase) => phrase.category === category);

  useEffect(() => {
    const online = () => setOffline(false);
    const disconnected = () => setOffline(true);
    window.addEventListener("online", online);
    window.addEventListener("offline", disconnected);
    return () => { window.removeEventListener("online", online); window.removeEventListener("offline", disconnected); };
  }, []);

  useEffect(() => {
    fetch(apiUrl("/api/local-assist/languages"))
      .then((response) => response.ok ? response.json() : Promise.reject())
      .then((data) => data.languages?.length && setLanguages(data.languages))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    const cacheKey = `local-assist-phrases:${source}:${target}`;
    try {
      const cached = JSON.parse(localStorage.getItem(cacheKey) || "[]");
      setPhrases(cached.length ? cached : offlinePhrasebook(source, target));
    } catch { setPhrases(offlinePhrasebook(source, target)); }
    fetch(apiUrl(`/api/local-assist/phrasebook?source_language=${source}&target_language=${target}`))
      .then((response) => response.ok ? response.json() : Promise.reject())
      .then((data) => {
        if (data.phrases?.length) {
          setPhrases(data.phrases);
          localStorage.setItem(cacheKey, JSON.stringify(data.phrases));
        }
      })
      .catch(() => undefined);
  }, [source, target]);

  const swapLanguages = () => {
    setSource(target);
    setTarget(source === "auto" ? "en" : source);
    setText(result);
    setResult(text);
    setTransliteration("");
    setWarning("");
  };

  const translate = async (input = text) => {
    if (!input.trim()) return;
    setLoading(true);
    setWarning("");
    try {
      const response = await fetch(apiUrl("/api/local-assist/translate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input.trim(), source_language: source, target_language: target }),
      });
      if (!response.ok) throw new Error("Translation service returned an error.");
      const data = await response.json();
      setResult(data.translated_text || "");
      setTransliteration(data.transliteration || "");
      setProvider(data.provider || "");
      setWarning(data.warning || "");
      if (data.translated_text) {
        setPhrases((items) => {
          const next = items.map((phrase) => phrase.source_text === input ? { ...phrase, translated_text: data.translated_text, transliteration: data.transliteration } : phrase);
          localStorage.setItem(`local-assist-phrases:${source}:${target}`, JSON.stringify(next));
          return next;
        });
        setHistory((items) => [{ original: input, translated: data.translated_text, transliteration: data.transliteration, source: data.detected_language || source, target, provider: data.provider }, ...items].slice(0, 6));
      }
    } catch {
      setResult("");
      setWarning("Local Assist cannot reach the server. The phrasebook remains available.");
    } finally {
      setLoading(false);
    }
  };

  const speak = (value: string, languageCode: string) => {
    if (!value || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(value);
    utterance.lang = languages.find((item) => item.code === languageCode)?.speech || languageCode;
    window.speechSynthesis.speak(utterance);
  };

  const listen = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setWarning("Voice input is not supported by this browser. You can still type your message.");
      return;
    }
    if (listening) return;
    const recognition = new SpeechRecognition();
    recognition.lang = sourceLanguage.speech;
    recognition.interimResults = false;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => {
      setListening(false);
      setWarning("I could not hear that clearly. Please try again or type the message.");
    };
    recognition.onresult = (event: any) => setText(event.results[0][0].transcript);
    recognition.start();
  };

  const usePhrase = (phrase: Phrase) => {
    setText(phrase.source_text);
    setResult(phrase.translated_text);
    setTransliteration(phrase.transliteration || "");
    setProvider(phrase.verified ? "verified_phrasebook" : "");
    setWarning("");
    if (phrase.translated_text) setHistory((items) => [{ original: phrase.source_text, translated: phrase.translated_text, source, target, provider: phrase.verified ? "verified_phrasebook" : "cached_translation" }, ...items].slice(0, 6));
    if (!phrase.translated_text) void translate(phrase.source_text);
  };

  const translateLocalReply = async (input: string) => {
    const travelerLanguage = source === "auto" ? "en" : source;
    setText(input);
    setLoading(true);
    setWarning("");
    try {
      const response = await fetch(apiUrl("/api/local-assist/translate"), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input, source_language: target, target_language: travelerLanguage }),
      });
      if (!response.ok) throw new Error();
      const data = await response.json();
      setResult(data.translated_text || "");
      setTransliteration(data.transliteration || "");
      setProvider(data.provider || "");
    } catch { setWarning("The local reply could not be translated. Try again when online."); }
    finally { setLoading(false); }
  };

  const toggleFavorite = (id: string) => {
    setFavorites((items) => {
      const next = items.includes(id) ? items.filter((item) => item !== id) : [...items, id];
      localStorage.setItem("local-assist-favorites", JSON.stringify(next));
      return next;
    });
  };

  const listenAs = (language: Language, onResult: (value: string) => void) => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return setWarning("Voice input is not supported by this browser.");
    const recognition = new SpeechRecognition();
    recognition.lang = language.speech;
    recognition.interimResults = false;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => { setListening(false); setWarning("I could not hear that clearly. Please try again."); };
    recognition.onresult = (event: any) => onResult(event.results[0][0].transcript);
    recognition.start();
  };

  return (
    <div className="min-h-full bg-slate-50 px-4 py-6 dark:bg-[#0b0f19] sm:px-7 lg:px-10">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-xs font-extrabold uppercase tracking-[0.18em] text-teal-600 dark:text-teal-400"><Languages className="h-4 w-4" /> Local Language Assistant</div>
            <h1 className="font-heading text-3xl font-bold text-slate-900 dark:text-white">Speak locally, travel confidently</h1>
            <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">Translate a conversation or use verified travel phrases. Names, numbers and booking references are kept unchanged.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {offline && <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-bold text-amber-700 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-300"><WifiOff className="h-4 w-4" /> Offline phrases active</div>}
            <a href="tel:112" className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-bold text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300"><ShieldAlert className="h-4 w-4" /> Call emergency 112</a>
          </div>
        </div>

        <div className="mb-4 flex w-fit rounded-xl border border-slate-200 bg-white p-1 dark:border-slate-800 dark:bg-[#111827]">
          <button type="button" onClick={() => setConversationMode(false)} className={`rounded-lg px-4 py-2 text-xs font-bold ${!conversationMode ? "bg-teal-600 text-white" : "text-slate-500"}`}><Languages className="mr-1.5 inline h-4 w-4" /> Translator</button>
          <button type="button" onClick={() => setConversationMode(true)} className={`rounded-lg px-4 py-2 text-xs font-bold ${conversationMode ? "bg-teal-600 text-white" : "text-slate-500"}`}><MessageCircle className="mr-1.5 inline h-4 w-4" /> Conversation</button>
        </div>

        {conversationMode && <section className="mb-5 rounded-3xl border border-teal-200 bg-gradient-to-br from-teal-50 to-sky-50 p-5 dark:border-teal-900 dark:from-teal-950/30 dark:to-sky-950/20">
          <div className="grid gap-3 sm:grid-cols-2">
            <button type="button" disabled={listening} onClick={() => listenAs(sourceLanguage, (value) => { setText(value); void translate(value); })} className="flex min-h-28 flex-col items-center justify-center rounded-2xl bg-white p-5 font-bold text-slate-800 shadow-sm transition hover:-translate-y-0.5 disabled:opacity-50 dark:bg-slate-900 dark:text-white"><Mic className="mb-2 h-8 w-8 text-teal-600" />Traveler speaks {sourceLanguage.name}</button>
            <button type="button" disabled={listening} onClick={() => listenAs(targetLanguage, (value) => void translateLocalReply(value))} className="flex min-h-28 flex-col items-center justify-center rounded-2xl bg-white p-5 font-bold text-slate-800 shadow-sm transition hover:-translate-y-0.5 disabled:opacity-50 dark:bg-slate-900 dark:text-white"><Mic className="mb-2 h-8 w-8 text-sky-600" />Local person speaks {targetLanguage.name}</button>
          </div>
          <p className="mt-3 text-center text-xs font-medium text-slate-500">Take turns speaking. Translation and audio playback appear below.</p>
        </section>}

        <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-[#111827]">
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 border-b border-slate-100 p-4 dark:border-slate-800 sm:px-6">
            <label className="text-xs font-bold text-slate-500">Traveler language<select value={source} onChange={(e) => setSource(e.target.value)} className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-bold text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-white"><option value="auto">Auto detect</option>{languages.map((language) => <option key={language.code} value={language.code}>{language.name}</option>)}</select></label>
            <button type="button" onClick={swapLanguages} className="mt-5 rounded-full border border-slate-200 p-2.5 text-slate-500 transition hover:border-teal-400 hover:text-teal-600 dark:border-slate-700" aria-label="Swap languages"><ArrowRightLeft className="h-4 w-4" /></button>
            <label className="text-xs font-bold text-slate-500">Local language<select value={target} onChange={(e) => setTarget(e.target.value)} className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-bold text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-white">{languages.map((language) => <option key={language.code} value={language.code}>{language.name}</option>)}</select></label>
          </div>

          <div className="grid md:grid-cols-2">
            <div className="border-b border-slate-100 p-5 dark:border-slate-800 md:border-b-0 md:border-r sm:p-6">
              <div className="mb-3 flex items-center justify-between"><span className="text-xs font-extrabold uppercase tracking-wider text-slate-400">Speak or type in {sourceLanguage.name}</span><button type="button" onClick={listen} className={`flex items-center gap-2 rounded-full px-3 py-2 text-xs font-bold ${listening ? "bg-red-100 text-red-600" : "bg-teal-50 text-teal-600 dark:bg-teal-950/40 dark:text-teal-300"}`} title="Speech to text">{listening ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />} {listening ? "Stop" : "Speak"}</button></div>
              <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Type what you want to say…" className="h-36 w-full resize-none bg-transparent text-lg font-medium text-slate-800 outline-none placeholder:text-slate-300 dark:text-white dark:placeholder:text-slate-600" maxLength={1000} />
              <div className="flex items-center justify-between"><span className="text-[11px] text-slate-400">{text.length}/1000</span><button type="button" disabled={!text.trim() || loading} onClick={() => void translate()} className="flex items-center gap-2 rounded-xl bg-teal-600 px-5 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"><Sparkles className="h-4 w-4" /> {loading ? "Translating…" : "Translate"}</button></div>
            </div>
            <div className="bg-slate-50/60 p-5 dark:bg-slate-950/30 sm:p-6">
              <div className="mb-3 flex items-center justify-between"><span className="text-xs font-extrabold uppercase tracking-wider text-slate-400">Show or play in {targetLanguage.name}</span><button type="button" disabled={!result} onClick={() => speak(result, target)} className="flex items-center gap-2 rounded-full bg-sky-50 px-3 py-2 text-xs font-bold text-sky-600 disabled:opacity-40 dark:bg-sky-950/40 dark:text-sky-300" title="Text to speech"><Volume2 className="h-4 w-4" /> Play aloud</button></div>
              <div className="min-h-36 whitespace-pre-wrap text-xl font-semibold leading-relaxed text-slate-800 dark:text-white">{result || <span className="font-normal text-slate-300 dark:text-slate-600">Translation will appear here.</span>}</div>
              {transliteration && transliteration !== result && <div className="mt-3 rounded-xl border border-sky-100 bg-white/80 p-3 dark:border-sky-900 dark:bg-slate-900/70"><p className="text-[10px] font-extrabold uppercase tracking-wider text-sky-600">Pronunciation</p><p className="mt-1 text-sm font-medium italic text-slate-600 dark:text-slate-300">{transliteration}</p></div>}
              {provider && <p className="mt-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">{provider === "verified_phrasebook" ? "Verified offline phrase" : provider === "groq" ? "AI translation · verify critical details" : "No translation needed"}</p>}
              {warning && <p className="mt-3 rounded-xl bg-amber-50 p-3 text-xs font-semibold text-amber-800 dark:bg-amber-950/30 dark:text-amber-300">{warning}</p>}
            </div>
          </div>
        </section>

        <section className="mt-7">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-heading text-xl font-bold text-slate-900 dark:text-white">Quick phrasebook</h2><p className="text-xs text-slate-500">Tap a phrase, then play it aloud.</p></div><div className="flex max-w-full gap-2 overflow-x-auto pb-1">{categories.map((item) => <button key={item} type="button" onClick={() => setCategory(item)} className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-bold ${category === item ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900" : "border border-slate-200 bg-white text-slate-500 dark:border-slate-800 dark:bg-slate-900"}`}>{item}</button>)}</div></div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{shownPhrases.map((phrase) => { const safety = phrase.category === "Emergency" || phrase.category === "Medical"; return <div key={phrase.id} className={`relative rounded-2xl border bg-white p-4 transition hover:-translate-y-0.5 hover:shadow-md dark:bg-[#111827] ${safety ? "border-red-200 dark:border-red-900" : "border-slate-200 hover:border-teal-300 dark:border-slate-800"}`}><button type="button" onClick={() => toggleFavorite(phrase.id)} className={`absolute right-3 top-3 rounded-full p-1.5 ${favorites.includes(phrase.id) ? "bg-rose-50 text-rose-500" : "text-slate-300 hover:bg-slate-50"}`} aria-label="Toggle favourite"><Heart className={`h-4 w-4 ${favorites.includes(phrase.id) ? "fill-current" : ""}`} /></button><button type="button" onClick={() => usePhrase(phrase)} className="w-full pr-8 text-left"><span className={`text-xs font-extrabold uppercase tracking-wider ${safety ? "text-red-600" : "text-teal-600 dark:text-teal-400"}`}>{categoryEmoji[phrase.category]} {phrase.category}</span>{phrase.verified && <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[9px] font-extrabold text-emerald-700"><BadgeCheck className="h-3 w-3" /> Verified</span>}<p className="mt-2 text-sm font-semibold text-slate-700 dark:text-slate-200">{phrase.source_text}</p><p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{phrase.translated_text || (offline ? "Online translation required" : "Tap to translate")}</p><span className="mt-3 flex items-center gap-1 text-[11px] font-bold text-sky-600"><Volume2 className="h-3.5 w-3.5" /> Tap to use</span></button></div>; })}</div>
          {shownPhrases.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">No favourite phrases yet. Tap the heart on a phrase to save it offline.</div>}
          <p className="mt-4 rounded-xl bg-amber-50 p-3 text-xs font-semibold text-amber-800 dark:bg-amber-950/30 dark:text-amber-300">For medical, allergy, payment or emergency information, show the translated text and ask the other person to confirm it. Call 112 for emergencies in India.</p>
        </section>

        {history.length > 0 && <section className="mt-7 pb-8"><h2 className="mb-3 font-heading text-xl font-bold text-slate-900 dark:text-white">Recent conversation</h2><div className="space-y-2">{history.map((item, index) => <div key={`${item.original}-${index}`} className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-[#111827]"><div className="min-w-0 flex-1"><p className="truncate text-xs text-slate-400">{item.original}</p><p className="truncate text-sm font-semibold text-slate-700 dark:text-slate-200">{item.translated}</p></div><button type="button" onClick={() => speak(item.translated, item.target)} className="rounded-full p-2 text-sky-600 hover:bg-sky-50 dark:hover:bg-sky-950/30"><Volume2 className="h-4 w-4" /></button></div>)}</div></section>}
      </div>
    </div>
  );
}
