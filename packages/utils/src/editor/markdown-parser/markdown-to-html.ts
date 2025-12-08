// Converts Markdown to HTML using the unified ecosystem
// - Parses markdown using remark-parse with GFM support
// - Converts to HTML using remark-rehype
// - Handles raw HTML in markdown via rehype-raw
// - Stringifies to HTML using rehype-stringify

import rehypeRaw from "rehype-raw";
import rehypeStringify from "rehype-stringify";
import remarkGfm from "remark-gfm";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import { unified } from "unified";

type TConvertMarkdownToHTMLArgs = {
  markdown: string;
};

/**
 * Converts markdown text to HTML
 * Supports GFM (GitHub Flavored Markdown) including:
 * - Tables
 * - Task lists
 * - Strikethrough
 * - Autolinks
 * - Footnotes
 *
 * Also supports raw HTML embedded in markdown.
 *
 * @param args - The arguments containing the markdown string
 * @returns HTML string
 */
export function convertMarkdownToHTML(args: TConvertMarkdownToHTMLArgs): string {
  const { markdown } = args;

  if (!markdown || markdown.trim() === "") {
    return "<p></p>";
  }

  const result = unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeRaw)
    .use(rehypeStringify)
    .processSync(markdown);

  const html = String(result.value ?? result);

  // Ensure we return valid HTML - wrap in paragraph if needed
  if (!html || html.trim() === "") {
    return "<p></p>";
  }

  return html;
}

/**
 * Async version of convertMarkdownToHTML for larger documents
 * @param args - The arguments containing the markdown string
 * @returns Promise resolving to HTML string
 */
export async function convertMarkdownToHTMLAsync(args: TConvertMarkdownToHTMLArgs): Promise<string> {
  const { markdown } = args;

  if (!markdown || markdown.trim() === "") {
    return "<p></p>";
  }

  const result = await unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeRaw)
    .use(rehypeStringify)
    .process(markdown);

  const html = String(result.value ?? result);

  if (!html || html.trim() === "") {
    return "<p></p>";
  }

  return html;
}
