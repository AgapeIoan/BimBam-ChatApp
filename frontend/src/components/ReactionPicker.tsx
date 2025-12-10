import { useEffect, useRef } from 'react';
import EmojiPicker from 'emoji-picker-react';
import type { EmojiClickData } from 'emoji-picker-react';

interface ReactionPickerProps {
  onSelect: (emoji: string) => void;
  onClose?: () => void;
  className?: string;
}

export function ReactionPicker({ onSelect, onClose, className }: ReactionPickerProps) {
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose?.();
    }

    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  useEffect(() => {
    // focus first button when opened
    const el = rootRef.current?.querySelector('button');
    (el as HTMLElement | null)?.focus();
  }, []);

  return (
    <div ref={rootRef} className={`inline-flex items-center ${className || ''}`} role="dialog" aria-label="Reaction picker">
      <div className="rounded shadow bg-white">
        <EmojiPicker
          onEmojiClick={(data: EmojiClickData) => {
            const emoji = (data as any).emoji || (data as any).unified || '';
            // prefer native emoji if present
            const chosen = (data as any).emoji || (data as any).native || emoji;
            onSelect(chosen as string);
            onClose?.();
          }}
        />
      </div>
    </div>
  );
}

export default ReactionPicker;
