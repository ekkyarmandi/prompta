
// Simple token estimation function
// This provides a rough estimate based on common tokenization patterns
export const estimateTokenCount = (text: string): number => {
  if (!text || text.trim().length === 0) return 0;
  
  // Remove extra whitespace and normalize
  const normalizedText = text.trim().replace(/\s+/g, ' ');
  
  // Split by whitespace to get words
  const words = normalizedText.split(' ');
  
  // Estimate tokens based on word count and character patterns
  let tokenCount = 0;
  
  for (const word of words) {
    if (word.length === 0) continue;
    
    // Simple heuristic: most words are 1 token, longer words might be 2+
    if (word.length <= 4) {
      tokenCount += 1;
    } else if (word.length <= 8) {
      tokenCount += Math.ceil(word.length / 4);
    } else {
      tokenCount += Math.ceil(word.length / 3);
    }
    
    // Account for punctuation and special characters
    const specialChars = (word.match(/[^\w\s]/g) || []).length;
    tokenCount += Math.ceil(specialChars / 2);
  }
  
  return Math.max(1, tokenCount);
};

export const formatTokenCount = (count: number): string => {
  if (count < 1000) {
    return count.toString();
  } else if (count < 1000000) {
    return `${(count / 1000).toFixed(1)}K`;
  } else {
    return `${(count / 1000000).toFixed(1)}M`;
  }
};
