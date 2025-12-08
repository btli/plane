import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from "react";
// plane imports
import { useTranslation } from "@plane/i18n";
import { cn, convertHTMLToMarkdown, convertMarkdownToHTML } from "@plane/utils";
import type { TCustomComponentsMetaData } from "@plane/utils";

type TMarkdownEditorProps = {
  id: string;
  initialValue: string;
  onChange?: (html: string) => void;
  editable?: boolean;
  placeholder?: string;
  containerClassName?: string;
  getEditorMetaData: (htmlContent: string) => TCustomComponentsMetaData;
};

export type MarkdownEditorRefApi = {
  getMarkdown: () => string;
  setMarkdown: (markdown: string) => void;
  getHTML: () => string;
  setHTML: (html: string) => void;
  focus: () => void;
  blur: () => void;
};

export const MarkdownEditor = forwardRef<MarkdownEditorRefApi, TMarkdownEditorProps>(
  function MarkdownEditor(props, ref) {
    const { id, initialValue, onChange, editable = true, placeholder, containerClassName, getEditorMetaData } = props;
    const { t } = useTranslation();
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Convert initial HTML to markdown for display
    const getInitialMarkdown = useCallback(() => {
      if (!initialValue || initialValue === "<p></p>") return "";
      const metaData = getEditorMetaData(initialValue);
      return convertHTMLToMarkdown({
        description_html: initialValue,
        metaData,
      });
    }, [initialValue, getEditorMetaData]);

    const [markdown, setMarkdown] = useState(getInitialMarkdown);

    // Update markdown when initialValue changes
    useEffect(() => {
      setMarkdown(getInitialMarkdown());
    }, [getInitialMarkdown]);

    // Handle markdown change
    const handleMarkdownChange = useCallback(
      (newMarkdown: string) => {
        setMarkdown(newMarkdown);
        if (onChange) {
          const html = convertMarkdownToHTML({ markdown: newMarkdown });
          onChange(html);
        }
      },
      [onChange]
    );

    // Expose methods via ref
    useImperativeHandle(
      ref,
      () => ({
        getMarkdown: () => markdown,
        setMarkdown: (md: string) => {
          setMarkdown(md);
        },
        getHTML: () => {
          return convertMarkdownToHTML({ markdown });
        },
        setHTML: (html: string) => {
          const metaData = getEditorMetaData(html);
          const md = convertHTMLToMarkdown({
            description_html: html,
            metaData,
          });
          setMarkdown(md);
        },
        focus: () => textareaRef.current?.focus(),
        blur: () => textareaRef.current?.blur(),
      }),
      [markdown, getEditorMetaData]
    );

    // Auto-resize textarea
    const handleTextareaResize = useCallback(() => {
      const textarea = textareaRef.current;
      if (textarea) {
        textarea.style.height = "auto";
        textarea.style.height = `${textarea.scrollHeight}px`;
      }
    }, []);

    useEffect(() => {
      handleTextareaResize();
    }, [markdown, handleTextareaResize]);

    return (
      <div className={cn("relative", containerClassName)}>
        <textarea
          ref={textareaRef}
          id={id}
          value={markdown}
          onChange={(e) => handleMarkdownChange(e.target.value)}
          onInput={handleTextareaResize}
          disabled={!editable}
          placeholder={placeholder ?? t("editor.markdown.placeholder")}
          className={cn(
            "w-full min-h-[100px] resize-none bg-transparent outline-none",
            "font-mono text-sm text-custom-text-100",
            "placeholder:text-custom-text-400",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "border-none focus:ring-0"
          )}
          spellCheck={false}
        />
      </div>
    );
  }
);

MarkdownEditor.displayName = "MarkdownEditor";
