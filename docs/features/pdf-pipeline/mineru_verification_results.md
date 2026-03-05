# MinerU Verification Results

This document contains the manual verification findings of the MinerU output against the targets defined in `scripts/targets.json`.

## `rc_microservices.pdf` Targets

### 1. Pages 37-38: Single block merging
- **Target description**: Paragraph starting with "My definition of" ends on 38th page with "shown in figure 1.3", should be one block.
- **Finding**: The paragraph starting with "My definition of" is **not** merged. It ends abruptly at the bottom of page 38 and the rest of the text spills onto page 39. MinerU extracts these as two entirely separate paragraph blocks.

### 2. Page 38: Figure 1.3
- **Target description**: Figure 1.3 should be saved and linked, also there should be note to the picture.
- **Finding**: Figure 1.3 is **not** present in the page 38 extraction. MinerU's pagination logic pushes it entirely onto page 39. On page 39, while the image file is extracted, its `path_or_ref` is empty in the JSON, so it isn't properly linked in the output markdown.

### 3. Page 39: Figure 1.5
- **Target description**: Figure 1.5 with code.
- **Finding**: Figure 1.5 is **not** present on page 39 in the extraction output (only Figure 1.3 is). It is not linked, and the code isn't associated with it.

### 4. Page 92: Table 2.3
- **Target description**: Table 2.3
- **Finding**: Table 2.3 is mentioned but missing entirely from page 92's output (it likely falls onto page 93). Table 2.2 is extracted here instead, but MinerU renders it as an image (`table_render`) rather than pure markdown syntax, and it's missing from the generated markdown due to an empty reference.

### 5. Pages 105-106: Listing 3.1
- **Target description**: Code block on two pages (named "Listing 3.1 An excerpt of the gRPC API for the Order Service").
- **Finding**: The "Listing 3.1" code block is **not** merged seamlessly. The code is truncated at the bottom of page 106 and split into a separate block on page 107.

### 6. Page 107: Figure 3.2
- **Target description**: Figure 3.2 with code (endpoints).
- **Finding**: Figure 3.2 is **not extracted** on this page. There are no images placed in the `images/` directory for this extraction.

### 7. Page 164: Figure 4.11
- **Target description**: Figure 4.11 with code and comments.
- **Finding**: Figure 4.11 is extracted into the `images/` folder as a JPEG. However, it is **not linked** in the Markdown (the reference path is empty), and the code/comments are not transcribed alongside it.

## `llm-evals.pdf` Targets

### 8. Page 20: Bullet sections
- **Target description**: Several blocks (sections) with bullets.
- **Finding**: There are sections with bulleted lists, but MinerU represents them as concatenated plain text paragraphs (`type: para`) separated by newline characters. It does not use explicit `List` structure blocks natively.

### 9. Pages 25-26: Sample Prompt note
- **Target description**: Note "Sample Prompt". divided by pages, should be one block in the end. contains bullets.
- **Finding**: The "Sample Prompt" text is **not** merged. It is heavily fragmented into individual paragraph blocks. The bullet points are just separate paragraphs starting with a bullet character (`•`), and the flow is interrupted by page headers at the break.

### 10. Page 25: Sample Prompt figure
- **Target description**: Picture with blocks and note "Sample Prompt".
- **Finding**: The "Sample Prompt" note is extracted as plain text, not categorized as a figure. There is a different figure (Figure 5) extracted as an image file on this page, but it is **not linked correctly** in the Markdown file (the `path_or_ref` is empty).

## Conclusion
While the MinerU CLI runner is implemented correctly according to the design plan, the MinerU engine's native output behaves significantly differently from Marker's. It doesn't natively merge blocks across page boundaries, treats lists as flat paragraphs with bullet characters, often converts tables into images instead of markdown, and occasionally misaligns or omits figure links in its generated JSON/Markdown payloads.