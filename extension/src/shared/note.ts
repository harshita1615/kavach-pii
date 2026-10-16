/**
 * The note appended to a masked message, telling the AI that the bracketed
 * placeholders stand for real values it can't see. Without it, chatbots tend
 * to read [PAN_1] as an empty template field.
 *
 * The note's examples use [PAN_n], never a real-looking [PAN_1]: a real one
 * would be treated as already taken when masking and could be confused with
 * the user's data.
 */

/** Append the note unless the message already has it. */
export function withNote(message: string, note: string): string {
  if (!note || hasNote(message, note)) return message;
  return `${message.trimEnd()}\n\n${note}`;
}

export function hasNote(message: string, note: string): boolean {
  // Compare a prefix: editors may reflow whitespace in the rest of the note.
  return message.includes(note.slice(0, 24));
}
