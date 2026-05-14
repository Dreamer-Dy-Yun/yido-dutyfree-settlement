function EdiNoteTooltip({ noteTooltip }) {
  if (!noteTooltip.open) return null;

  return (
    <div
      className="edi-note-tooltip"
      style={{ left: noteTooltip.x, top: noteTooltip.y }}
    >
      <div className="edi-note-title">system_note</div>
      <div className="edi-note-body">{noteTooltip.text}</div>
    </div>
  );
}

export default EdiNoteTooltip;
