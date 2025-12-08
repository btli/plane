import React, { forwardRef, useCallback, useImperativeHandle, useRef, useState } from "react";
import { FileCode, Type } from "lucide-react";
// plane imports
import type { EditorRefApi, TFileHandler } from "@plane/editor";
import { useTranslation } from "@plane/i18n";
import type { TSearchEntityRequestPayload, TSearchResponse } from "@plane/types";
import { Tooltip } from "@plane/propel/tooltip";
import { cn, convertMarkdownToHTML } from "@plane/utils";
// components
import { MarkdownEditor, type MarkdownEditorRefApi } from "@/components/editor/markdown-editor";
// hooks
import { useParseEditorContent } from "@/hooks/use-parse-editor-content";
// local imports
import { RichTextEditor } from "./editor";

type RichTextEditorWithMarkdownProps = {
  workspaceSlug: string;
  workspaceId: string;
  projectId?: string;
  issueSequenceId?: number;
  id: string;
  initialValue: string;
  placeholder?: string | ((isFocused: boolean, value: string) => string);
  containerClassName?: string;
  onChange?: (json: object, html: string) => void;
  dragDropEnabled?: boolean;
  value?: string | null;
} & (
  | {
      editable: false;
    }
  | {
      editable: true;
      searchMentionCallback: (payload: TSearchEntityRequestPayload) => Promise<TSearchResponse>;
      uploadFile: TFileHandler["upload"];
      duplicateFile: TFileHandler["duplicate"];
    }
);

export const RichTextEditorWithMarkdown = forwardRef<EditorRefApi, RichTextEditorWithMarkdownProps>(
  function RichTextEditorWithMarkdown(props, ref) {
    const { t } = useTranslation();
    const { workspaceSlug, workspaceId, projectId, id, initialValue, editable, containerClassName, onChange, ...rest } =
      props;

    // State for markdown mode
    const [isMarkdownMode, setIsMarkdownMode] = useState(false);
    const [markdownContent, setMarkdownContent] = useState("");
    const markdownEditorRef = useRef<MarkdownEditorRefApi>(null);
    const richTextEditorRef = useRef<EditorRefApi>(null);

    // Parse content hook
    const { getEditorMetaData } = useParseEditorContent({
      projectId,
      workspaceSlug,
    });

    // Toggle markdown mode
    const toggleMarkdownMode = useCallback(() => {
      if (isMarkdownMode) {
        // Switching from markdown to rich text - convert markdown to HTML
        const html = convertMarkdownToHTML({ markdown: markdownContent });
        richTextEditorRef.current?.setEditorValue(html, true);
        setIsMarkdownMode(false);
      } else {
        // Switching from rich text to markdown - get markdown from editor
        const markdown = richTextEditorRef.current?.getMarkDown() ?? "";
        setMarkdownContent(markdown);
        setIsMarkdownMode(true);
      }
    }, [isMarkdownMode, markdownContent]);

    // Handle markdown content change
    const handleMarkdownChange = useCallback(
      (html: string) => {
        if (onChange) {
          onChange({}, html);
        }
      },
      [onChange]
    );

    // Keyboard shortcut handler
    const handleKeyDown = useCallback(
      (e: React.KeyboardEvent) => {
        if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === "m") {
          e.preventDefault();
          toggleMarkdownMode();
        }
      },
      [toggleMarkdownMode]
    );

    // Forward ref to the appropriate editor
    useImperativeHandle(ref, () => {
      if (isMarkdownMode && markdownEditorRef.current) {
        return {
          getMarkDown: () => markdownEditorRef.current?.getMarkdown() ?? "",
          setMarkdown: (md: string) => markdownEditorRef.current?.setMarkdown(md),
          getHTML: () => markdownEditorRef.current?.getHTML() ?? "",
          setEditorValue: (html: string) => markdownEditorRef.current?.setHTML(html),
          focus: () => markdownEditorRef.current?.focus(),
          blur: () => markdownEditorRef.current?.blur(),
        } as unknown as EditorRefApi;
      }
      return richTextEditorRef.current as EditorRefApi;
    }, [isMarkdownMode]);

    if (!editable) {
      // Read-only mode - use standard RichTextEditor
      return (
        <RichTextEditor
          ref={richTextEditorRef}
          workspaceSlug={workspaceSlug}
          workspaceId={workspaceId}
          projectId={projectId}
          id={id}
          initialValue={initialValue}
          editable={false}
          containerClassName={containerClassName}
          {...rest}
        />
      );
    }

    return (
      <div className="relative" onKeyDown={handleKeyDown} role="textbox" tabIndex={-1}>
        {/* Mode toggle button */}
        <div className="absolute top-2 right-2 z-10">
          <Tooltip
            tooltipContent={
              <p className="flex flex-col gap-1 text-center text-xs">
                <span className="font-medium">
                  {isMarkdownMode ? t("editor.switch_to_rich_text") : t("editor.switch_to_markdown")}
                </span>
                <kbd className="text-custom-text-400">Cmd + Shift + M</kbd>
              </p>
            }
          >
            <button
              type="button"
              onClick={toggleMarkdownMode}
              className={cn(
                "grid place-items-center aspect-square rounded-sm p-1.5",
                "text-custom-text-400 hover:bg-custom-background-80 hover:text-custom-text-100",
                "transition-colors",
                {
                  "bg-custom-primary-100/10 text-custom-primary-100": isMarkdownMode,
                }
              )}
            >
              {isMarkdownMode ? <Type className="h-4 w-4" /> : <FileCode className="h-4 w-4" />}
            </button>
          </Tooltip>
        </div>

        {/* Editor content */}
        {isMarkdownMode ? (
          <div className={cn("relative", containerClassName)}>
            <MarkdownEditor
              ref={markdownEditorRef}
              id={id}
              initialValue={initialValue}
              onChange={handleMarkdownChange}
              editable={editable}
              placeholder={t("editor.markdown.placeholder")}
              getEditorMetaData={getEditorMetaData}
              containerClassName="min-h-[150px] pl-3 pb-3"
            />
            <div className="absolute bottom-1 left-3 text-xs text-custom-text-400">{t("editor.markdown.hint")}</div>
          </div>
        ) : (
          <RichTextEditor
            ref={richTextEditorRef}
            workspaceSlug={workspaceSlug}
            workspaceId={workspaceId}
            projectId={projectId}
            id={id}
            initialValue={initialValue}
            editable={true}
            containerClassName={containerClassName}
            onChange={onChange}
            searchMentionCallback={props.searchMentionCallback}
            uploadFile={props.uploadFile}
            duplicateFile={props.duplicateFile}
            {...rest}
          />
        )}
      </div>
    );
  }
);

RichTextEditorWithMarkdown.displayName = "RichTextEditorWithMarkdown";
