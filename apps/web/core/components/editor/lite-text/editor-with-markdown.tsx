import React, { useCallback, useRef, useState } from "react";
import { FileCode, Type } from "lucide-react";
// plane constants
import type { EIssueCommentAccessSpecifier } from "@plane/constants";
// plane imports
import type { EditorRefApi, TDisplayConfig, TFileHandler } from "@plane/editor";
import { useTranslation } from "@plane/i18n";
import { Tooltip } from "@plane/propel/tooltip";
import { cn, convertMarkdownToHTML } from "@plane/utils";
// components
import { MarkdownEditor, type MarkdownEditorRefApi } from "@/components/editor/markdown-editor";
// hooks
import { useParseEditorContent } from "@/hooks/use-parse-editor-content";
// local imports
import { LiteTextEditor } from "./editor";

type LiteTextEditorWithMarkdownProps = {
  workspaceSlug: string;
  workspaceId: string;
  projectId?: string;
  accessSpecifier?: EIssueCommentAccessSpecifier;
  handleAccessChange?: (accessKey: EIssueCommentAccessSpecifier) => void;
  showAccessSpecifier?: boolean;
  showSubmitButton?: boolean;
  isSubmitting?: boolean;
  showToolbarInitially?: boolean;
  variant?: "full" | "lite" | "none";
  issue_id?: string;
  parentClassName?: string;
  editorClassName?: string;
  id: string;
  initialValue: string;
  placeholder?: string;
  containerClassName?: string;
  onChange?: (json: object, html: string) => void;
  onEnterKeyPress?: (e?: React.KeyboardEvent | React.MouseEvent) => void;
  displayConfig?: TDisplayConfig;
} & (
  | {
      editable: false;
    }
  | {
      editable: true;
      uploadFile: TFileHandler["upload"];
      duplicateFile: TFileHandler["duplicate"];
    }
);

export const LiteTextEditorWithMarkdown = React.forwardRef<EditorRefApi, LiteTextEditorWithMarkdownProps>(
  function LiteTextEditorWithMarkdown(props, ref) {
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

    // Forward ref to the appropriate editor
    React.useImperativeHandle(ref, () => {
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
      // Read-only mode - use standard LiteTextEditor
      return (
        <LiteTextEditor
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
      <div className="relative">
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
          <div className={cn("border border-custom-border-200 rounded p-3", containerClassName)}>
            <MarkdownEditor
              ref={markdownEditorRef}
              id={id}
              initialValue={initialValue}
              onChange={handleMarkdownChange}
              editable={editable}
              placeholder={t("editor.markdown.placeholder")}
              getEditorMetaData={getEditorMetaData}
              containerClassName="min-h-[100px]"
            />
            <div className="mt-2 text-xs text-custom-text-400">{t("editor.markdown.hint")}</div>
          </div>
        ) : (
          <LiteTextEditor
            ref={richTextEditorRef}
            workspaceSlug={workspaceSlug}
            workspaceId={workspaceId}
            projectId={projectId}
            id={id}
            initialValue={initialValue}
            editable={true}
            containerClassName={containerClassName}
            onChange={onChange}
            uploadFile={props.uploadFile}
            duplicateFile={props.duplicateFile}
            {...rest}
          />
        )}
      </div>
    );
  }
);

LiteTextEditorWithMarkdown.displayName = "LiteTextEditorWithMarkdown";
