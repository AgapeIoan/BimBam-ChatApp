declare module "emoji-picker-react" {
  import type { FC } from "react";
  export type EmojiClickData = Record<string, any>;
  interface EmojiPickerProps {
    onEmojiClick?: (emojiData: EmojiClickData, event?: MouseEvent) => void;
    [key: string]: any;
  }
  const EmojiPicker: FC<EmojiPickerProps>;
  export default EmojiPicker;
}
