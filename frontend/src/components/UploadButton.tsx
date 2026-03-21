import React from "react";
import { Paperclip } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UploadButtonProps {
  onUpload?: (file: File) => void;
  disabled?: boolean;
}

const UploadButton: React.FC<UploadButtonProps> = ({ onUpload, disabled }) => {
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUpload) {
      onUpload(file);
    }
  };

  return (
    <div className="relative">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept="application/pdf"
      />
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={handleClick}
        disabled={disabled}
        className="text-muted-foreground hover:text-white transition-colors"
      >
        <Paperclip className="h-5 w-5" />
      </Button>
    </div>
  );
};

export default UploadButton;
