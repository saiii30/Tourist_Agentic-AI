export function extractRequestedCity(question: string): string | null {
  const patterns = [
    /places?\s+(?:to\s+visit\s+)?(?:near|in)\s+([a-zA-Z\s-]+)/i,
    /(?:plan|trip|travel)\s+(?:to|for|in)\s+([a-zA-Z\s-]+)/i,
    /(?:visit|explore)\s+([a-zA-Z\s-]+)/i,
  ];

  for (const pattern of patterns) {
    const match = question.match(pattern);

    if (match?.[1]) {
      return match[1]
        .replace(/\b(for|with|for a|for an|for the)\b.*$/i, "")
        .trim()
        .replace(/\s+/g, " ");
    }
  }

  return null;
}