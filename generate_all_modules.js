const pptxgen = require("pptxgenjs");
const path = require("path");

// ──────────────────────────────────────────────
// THEME: Colorful Academic
// ──────────────────────────────────────────────
const C = {
  navy: "1E3A5F", teal: "0D9488", orange: "F97316", purple: "8B5CF6",
  lightBg: "F8FAFC", white: "FFFFFF", textDark: "1E293B", textMuted: "64748B",
  textLight: "94A3B8", borderLight: "E2E8F0", green: "059669", red: "DC2626", cyan: "06B6D4",
};
const FT = "Georgia", FB = "Calibri";
const sh = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.08 });

// Shape constants from pptxgenjs
const _p = new pptxgen();
const RECT = _p.shapes.RECTANGLE;
const OVAL = _p.shapes.OVAL;

// ──────────────────────────────────────────────
// HELPER FUNCTIONS
// ──────────────────────────────────────────────
function addTitleAgenda(slide, moduleName, subtitle, moduleLabel, agendaItems, notes) {
  slide.addShape(RECT, { x: 0, y: 0, w: 4.5, h: 5.625, fill: { color: C.navy } });
  slide.addShape(RECT, { x: 4.5, y: 0, w: 0.08, h: 5.625, fill: { color: C.teal } });
  slide.addText(moduleLabel, { x: 0.5, y: 1.2, w: 3.5, h: 0.4, fontSize: 12, bold: true, color: C.teal, charSpacing: 4, fontFace: FB, margin: 0 });
  slide.addText(moduleName, { x: 0.5, y: 1.7, w: 3.5, h: 1.4, fontSize: 30, bold: true, color: C.white, fontFace: FT, margin: 0 });
  slide.addText(subtitle, { x: 0.5, y: 3.2, w: 3.5, h: 0.4, fontSize: 13, color: C.textLight, fontFace: FB, margin: 0 });
  slide.addText([
    { text: "Applied AI Course", options: { breakLine: true, fontSize: 11, color: C.textLight } },
    { text: "Part 1: Foundations", options: { breakLine: true, fontSize: 11, color: C.textLight } },
    { text: "2026", options: { fontSize: 11, color: C.teal } },
  ], { x: 0.5, y: 4.0, w: 3.5, h: 1.0, fontFace: FB, margin: 0 });
  slide.background = { color: C.lightBg };
  slide.addText("AGENDA", { x: 5.0, y: 0.8, w: 4.5, h: 0.5, fontSize: 14, bold: true, color: C.teal, charSpacing: 4, fontFace: FB, margin: 0 });
  agendaItems.forEach((item, i) => {
    slide.addText(item.num, { x: 5.0, y: 1.5 + i * 0.62, w: 0.6, h: 0.4, fontSize: 20, bold: true, color: item.color, fontFace: FT, margin: 0 });
    slide.addText(item.text, { x: 5.7, y: 1.55 + i * 0.62, w: 3.8, h: 0.4, fontSize: 14, color: C.textDark, fontFace: FB, margin: 0 });
  });
  slide.addNotes(notes);
}

function addKPICards(slide, title, subtitle, stats, notes) {
  slide.background = { color: C.lightBg };
  slide.addText(title, { x: 0.5, y: 0.4, w: 9, h: 0.6, fontSize: 28, bold: true, color: C.navy, fontFace: FT, margin: 0 });
  if (subtitle) slide.addText(subtitle, { x: 0.5, y: 1.0, w: 9, h: 0.35, fontSize: 13, color: C.textMuted, fontFace: FB, margin: 0 });
  stats.forEach((s, i) => {
    const col = i % 2, row = Math.floor(i / 2), x = 0.5 + col * 4.6, y = 1.5 + row * 1.9;
    slide.addShape(RECT, { x, y, w: 4.3, h: 1.7, fill: { color: C.white }, shadow: sh() });
    slide.addShape(RECT, { x, y, w: 0.08, h: 1.7, fill: { color: s.accent } });
    slide.addText(s.value, { x: x + 0.3, y: y + 0.15, w: 1.5, h: 0.6, fontSize: 26, bold: true, color: C.navy, fontFace: FT, margin: 0 });
    slide.addText(s.label, { x: x + 1.8, y: y + 0.2, w: 2.3, h: 0.4, fontSize: 14, bold: true, color: C.textDark, fontFace: FB, margin: 0 });
    slide.addText(s.desc, { x: x + 0.3, y: y + 0.9, w: 3.8, h: 0.6, fontSize: 11, color: C.textMuted, fontFace: FB, margin: 0 });
  });
  slide.addNotes(notes);
}

function addTwoCol(slide, title, leftTitle, leftItems, rightTitle, rightItems, leftColor, rightColor, notes) {
  slide.background = { color: C.lightBg };
  slide.addText(title, { x: 0.5, y: 0.4, w: 9, h: 0.6, fontSize: 26, bold: true, color: C.navy, fontFace: FT, margin: 0 });
  // Left
  slide.addShape(RECT, { x: 0.5, y: 1.2, w: 4.3, h: 4.0, fill: { color: leftColor === C.teal ? "F0FDFA" : "FEF2F2" }, shadow: sh() });
  slide.addShape(RECT, { x: 0.5, y: 1.2, w: 4.3, h: 0.5, fill: { color: leftColor } });
  slide.addText(leftTitle, { x: 0.5, y: 1.25, w: 4.3, h: 0.5, fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FB });
  const leftText = leftItems.map(i => ({ text: i.text, options: { bold: !!i.bold, breakLine: true, fontSize: i.bold ? 13 : 11, color: i.bold ? C.textDark : C.textMuted } }));
  slide.addText(leftText, { x: 0.7, y: 1.9, w: 3.9, h: 3.0, fontFace: FB, valign: "top", margin: 0 });
  // Right
  slide.addShape(RECT, { x: 5.2, y: 1.2, w: 4.3, h: 4.0, fill: { color: rightColor === C.orange ? "FFF7ED" : "F0FDFA" }, shadow: sh() });
  slide.addShape(RECT, { x: 5.2, y: 1.2, w: 4.3, h: 0.5, fill: { color: rightColor } });
  slide.addText(rightTitle, { x: 5.2, y: 1.25, w: 4.3, h: 0.5, fontSize: 14, bold: true, color: C.white, align: "center", fontFace: FB });
  const rightText = rightItems.map(i => ({ text: i.text, options: { bold: !!i.bold, breakLine: true, fontSize: i.bold ? 13 : 11, color: i.bold ? C.textDark : C.textMuted } }));
  slide.addText(rightText, { x: 5.4, y: 1.9, w: 3.9, h: 3.0, fontFace: FB, valign: "top", margin: 0 });
  slide.addNotes(notes);
}

function addFeatureGrid(slide, title, features, notes) {
  slide.background = { color: C.lightBg };
  slide.addText(title, { x: 0.5, y: 0.4, w: 9, h: 0.6, fontSize: 28, bold: true, color: C.navy, fontFace: FT, margin: 0 });
  features.forEach((f, i) => {
    const col = i % 2, row = Math.floor(i / 2), x = 0.5 + col * 4.6, y = 1.2 + row * 2.1;
    slide.addShape(RECT, { x, y, w: 4.3, h: 1.9, fill: { color: C.white }, shadow: sh() });
    slide.addShape(OVAL, { x: x + 0.2, y: y + 0.2, w: 0.55, h: 0.55, fill: { color: f.color, transparency: 15 } });
    slide.addText(f.icon, { x: x + 0.2, y: y + 0.22, w: 0.55, h: 0.55, fontSize: 18, bold: true, color: C.white, align: "center", valign: "middle", fontFace: FT });
    slide.addText(f.title, { x: x + 0.9, y: y + 0.25, w: 3.2, h: 0.4, fontSize: 15, bold: true, color: C.navy, fontFace: FB, margin: 0 });
    slide.addText(f.desc, { x: x + 0.2, y: y + 0.9, w: 3.9, h: 0.8, fontSize: 11, color: C.textMuted, fontFace: FB, margin: 0 });
  });
  slide.addNotes(notes);
}

function addSectionDivider(slide, sectionNum, title, subtitle, bgColor, notes) {
  slide.background = { color: bgColor };
  slide.addText(sectionNum, { x: 0, y: 2.2, w: 10, h: 0.5, fontSize: 18, color: bgColor === C.navy ? C.teal : (bgColor === C.purple ? "D8B4FE" : "FED7AA"), align: "center", fontFace: FB, margin: 0 });
  slide.addText(title, { x: 0, y: 2.7, w: 10, h: 1.0, fontSize: 42, bold: true, color: C.white, align: "center", fontFace: FT, margin: 0 });
  slide.addText(subtitle, { x: 0, y: 3.8, w: 10, h: 0.5, fontSize: 16, color: bgColor === C.navy ? C.textLight : (bgColor === C.purple ? "D8B4FE" : "FED7AA"), align: "center", fontFace: FB, margin: 0 });
  slide.addNotes(notes);
}

function addTimeline(slide, title, phases, details, notes) {
  slide.background = { color: C.navy };
  slide.addText(title, { x: 0.5, y: 0.4, w: 9, h: 0.6, fontSize: 28, bold: true, color: C.white, fontFace: FT, margin: 0 });
  slide.addShape(RECT, { x: 0.8, y: 2.5, w: 8.4, h: 0.06, fill: { color: C.teal } });
  phases.forEach((p, i) => {
    const x = 0.5 + i * (8.4 / phases.length);
    slide.addShape(OVAL, { x: x + 0.2, y: 2.1, w: 0.9, h: 0.9, fill: { color: p.color } });
    slide.addText(p.num, { x: x + 0.2, y: 2.15, w: 0.9, h: 0.85, fontSize: 22, bold: true, color: C.white, align: "center", valign: "middle", fontFace: FT });
    slide.addText(p.title, { x: x - 0.2, y: 3.2, w: 1.8, h: 0.4, fontSize: 13, bold: true, color: C.white, align: "center", fontFace: FB });
    slide.addText(p.desc, { x: x - 0.2, y: 3.55, w: 1.8, h: 0.4, fontSize: 10, color: C.textLight, align: "center", fontFace: FB });
    if (details && details[i]) {
      slide.addShape(RECT, { x: x - 0.1, y: 4.2, w: 1.6, h: 0.9, fill: { color: "2D4A6F" } });
      slide.addText(details[i], { x: x, y: 4.3, w: 1.4, h: 0.7, fontSize: 9, color: C.borderLight, align: "center", valign: "middle", fontFace: FB });
    }
  });
  slide.addNotes(notes);
}

function addTakeaways(slide, title, takeaways, notes) {
  slide.background = { color: C.lightBg };
  slide.addText(title, { x: 0.5, y: 0.4, w: 9, h: 0.6, fontSize: 28, bold: true, color: C.navy, fontFace: FT, margin: 0 });
  takeaways.forEach((t, i) => {
    const y = 1.2 + i * 0.7;
    slide.addShape(OVAL, { x: 0.5, y: y + 0.05, w: 0.45, h: 0.45, fill: { color: t.color } });
    slide.addText(t.num, { x: 0.5, y: y + 0.07, w: 0.45, h: 0.45, fontSize: 16, bold: true, color: C.white, align: "center", valign: "middle", fontFace: FT });
    slide.addText(t.text, { x: 1.2, y: y + 0.05, w: 8.3, h: 0.45, fontSize: 13, color: C.textDark, fontFace: FB, valign: "middle", margin: 0 });
  });
  slide.addNotes(notes);
}

function addThankYou(slide, nextModule, notes) {
  slide.background = { color: C.navy };
  slide.addShape(RECT, { x: 3, y: 2.2, w: 4, h: 0.04, fill: { color: C.teal } });
  slide.addText("Thank You", { x: 0, y: 2.5, w: 10, h: 0.9, fontSize: 42, bold: true, color: C.white, align: "center", fontFace: FT, margin: 0 });
  slide.addText("Questions & Discussion", { x: 0, y: 3.4, w: 10, h: 0.5, fontSize: 20, color: C.teal, align: "center", fontFace: FB, margin: 0 });
  slide.addShape(RECT, { x: 3, y: 4.1, w: 4, h: 0.04, fill: { color: C.teal } });
  slide.addText(`Next: ${nextModule}`, { x: 0, y: 4.4, w: 10, h: 0.4, fontSize: 14, color: C.textLight, align: "center", fontFace: FB, margin: 0 });
  slide.addText("Applied AI Course  |  Part 1: Foundations", { x: 0, y: 4.8, w: 10, h: 0.4, fontSize: 12, color: C.textLight, align: "center", fontFace: FB, margin: 0 });
  slide.addNotes(notes);
}

function addDividerSlide(title, subtitle, accentColor, notes) {
  const slide = pres.addSlide();
  slide.background = { color: accentColor === C.teal ? C.navy : accentColor };
  slide.addText(title, { x: 0, y: 2.5, w: 10, h: 0.9, fontSize: 38, bold: true, color: C.white, align: "center", fontFace: FT, margin: 0 });
  slide.addText(subtitle, { x: 0, y: 3.5, w: 10, h: 0.5, fontSize: 16, color: C.textLight, align: "center", fontFace: FB, margin: 0 });
  slide.addNotes(notes);
}

function addDarkTimeline(pres, title, phases, details, notes) {
  const slide = pres.addSlide();
  addTimeline(slide, title, phases, details, notes);
  return slide;
}

// ──────────────────────────────────────────────
// MODULE DEFINITIONS
// ──────────────────────────────────────────────
const modules = [
  // MODULE 3
  {
    file: "course-content/part-2-retrieval/module-3-rag-vectordb/Module-3-RAG-and-Vector-Databases.pptx",
    label: "MODULE 3", name: "RAG &\nVector Databases", subtitle: "Retrieval-Augmented Generation",
    agenda: [
      { num: "01", text: "What is RAG?", color: C.teal },
      { num: "02", text: "Embeddings & Chunking", color: C.orange },
      { num: "03", text: "Vector Databases", color: C.purple },
      { num: "04", text: "RAG Pipeline E2E", color: "3B82F6" },
      { num: "05", text: "Advanced Retrieval", color: C.teal },
      { num: "06", text: "Evaluation & Production", color: C.orange },
    ],
    notes: "Welcome to Module 3. This module covers RAG (Retrieval-Augmented Generation) and Vector Databases — the pattern that grounds LLM responses in external knowledge to reduce hallucinations and enable domain-specific Q&A.",
    slides: (p) => {
      let s;
      // Slide 2: Why RAG
      s = p.addSlide();
      addKPICards(s, "Why RAG?", "Problems RAG solves over traditional LLMs", [
        { value: "0", label: "Knowledge Cutoff", desc: "Always up-to-date with external data sources", accent: C.teal },
        { value: "↓", label: "Hallucinations", desc: "Grounded in retrieved facts, not fabricated", accent: C.orange },
        { value: "✓", label: "Source Citations", desc: "Can provide references to original documents", accent: C.purple },
        { value: "🔒", label: "Data Privacy", desc: "Keep sensitive data in-house, not in training", accent: "3B82F6" },
      ], "RAG solves five critical problems: knowledge cutoff (always current), hallucinations (grounded in facts), domain specificity (your data), data privacy (stays in-house), and source attribution (citable references). Core components: Document Store, Embedding Model, Vector DB, Retriever, LLM Generator.");

      // Slide 3: Embeddings
      s = p.addSlide();
      addFeatureGrid(s, "Embeddings & Models", [
        { icon: "S", color: C.teal, title: "text-embedding-3-small", desc: "1536 dims, 8191 tokens. General purpose, cost-effective. Best starting point." },
        { icon: "L", color: C.orange, title: "text-embedding-3-large", desc: "3072 dims, 8191 tokens. Higher accuracy for complex retrieval tasks." },
        { icon: "O", color: C.purple, title: "Open Source Options", desc: "BGE-large, E5-large, nomic-embed-text. Self-hosted, no API costs." },
        { icon: "C", color: "3B82F6", title: "Cosine Similarity", desc: "Measures semantic closeness. Similar texts → vectors close in space." },
      ], "Embeddings convert text to dense vectors capturing semantic meaning. OpenAI's text-embedding-3-small (1536 dims) is the best starting point. For higher accuracy, use text-embedding-3-large (3072 dims). Open-source alternatives (BGE, E5, nomic) enable self-hosting. Cosine similarity measures how close two vectors are in semantic space.");

      // Slide 4: Chunking Strategies
      s = p.addSlide();
      addFeatureGrid(s, "Chunking Strategies", [
        { icon: "F", color: C.teal, title: "Fixed-Size", desc: "200-500 tokens, 10-20% overlap. Simple, fast. Best for uniform documents." },
        { icon: "R", color: C.orange, title: "Recursive Character", desc: "Splits on \\n\\n, \\n, ., space. Preserves structure. Best for mixed content." },
        { icon: "S", color: C.purple, title: "Semantic Chunking", desc: "Splits at semantic breakpoints. Best for complex reasoning tasks." },
        { icon: "D", color: "3B82F6", title: "Document-Specific", desc: "Code-aware, markdown-aware. Preserves domain structure." },
      ], "Chunking strategy directly impacts retrieval quality. Fixed-size is simplest. RecursiveCharacterTextSplitter (LangChain) is the default for most use cases — it splits on paragraph, sentence, then word boundaries. Semantic chunking uses embeddings to find natural breakpoints. Document-specific splitters handle code, markdown, and LaTeX. Always include 10-20% overlap between chunks.");

      // Slide 5: Vector DB Comparison
      s = p.addSlide();
      addTwoCol(s, "Vector Database Comparison", "CLOUD / MANAGED",
        [{ text: "Pinecone", bold: true }, { text: "Billions of vectors, serverless" }, { text: "Best for: Production at scale" }, { text: "" }, { text: "Weaviate", bold: true }, { text: "Cloud or self-hosted" }, { text: "Hybrid search (keyword + vector)" }],
        "LOCAL / OPEN SOURCE",
        [{ text: "Chroma", bold: true }, { text: "Local development, lightweight" }, { text: "Best for: Prototyping" }, { text: "" }, { text: "FAISS", bold: true }, { text: "Facebook's library, in-memory" }, { text: "Best for: Research, millions of vectors" }],
        C.teal, C.orange, "Four main vector databases. Pinecone: managed cloud, billions of vectors, serverless. Weaviate: cloud or self-hosted, hybrid search. Chroma: local-first, great for development. FAISS: Facebook's library, in-memory, best for research. For production: Pinecone or Weaviate. For development: Chroma or FAISS.");

      // Slide 6: RAG Pipeline
      s = p.addSlide();
      addTimeline(s, "RAG Pipeline Architecture", [
        { num: "1", title: "Ingest", desc: "Load & chunk docs", color: C.teal },
        { num: "2", title: "Embed", desc: "Vectorize chunks", color: C.orange },
        { num: "3", title: "Store", desc: "Index in vector DB", color: C.purple },
        { num: "4", title: "Retrieve", desc: "Find relevant chunks", color: "3B82F6" },
        { num: "5", title: "Generate", desc: "LLM produces answer", color: C.teal },
      ], ["PDF, HTML, Markdown", "text-embedding-3-small", "Pinecone, Chroma", "Top-k similarity search", "Grounded response"], "The RAG pipeline has five stages: 1) Ingestion — load documents with PyPDFLoader, TextLoader, etc. 2) Embedding — convert chunks to vectors. 3) Storage — index in vector DB. 4) Retrieval — find top-k similar chunks for a query. 5) Generation — LLM produces a grounded response using retrieved context.");

      // Slide 7: Advanced Retrieval
      s = p.addSlide();
      addFeatureGrid(s, "Advanced Retrieval Techniques", [
        { icon: "H", color: C.teal, title: "Hybrid Search", desc: "Combine keyword (BM25) + vector search. Best of both worlds." },
        { icon: "R", color: C.orange, title: "Re-ranking", desc: "Cross-encoder re-ranks initial results. Improves precision." },
        { icon: "M", color: C.purple, title: "Multi-Query", desc: "Generate multiple query variants. Covers different phrasings." },
        { icon: "S", color: "3B82F6", title: "Self-Query", desc: "LLM extracts filters from natural language. Metadata-aware." },
      ], "Advanced retrieval goes beyond simple top-k similarity. Hybrid search combines BM25 keyword matching with vector similarity. Re-ranking uses cross-encoder models to re-score initial results. Multi-query generates query variants to cover different phrasings. Self-query extracts structured filters from natural language (e.g., 'documents from 2024').");

      // Slide 8: Evaluation
      s = p.addSlide();
      addKPICards(s, "RAG Evaluation Metrics", "Measuring retrieval and generation quality", [
        { value: "Faithful", label: "Faithfulness", desc: "Is the answer grounded in retrieved context?", accent: C.teal },
        { value: "Relev.", label: "Relevance", desc: "Are retrieved chunks relevant to the query?", accent: C.orange },
        { value: "Recall", label: "Context Recall", desc: "Did we retrieve all necessary information?", accent: C.purple },
        { value: "Answer", label: "Answer Correctness", desc: "Is the final answer factually correct?", accent: "3B82F6" },
      ], "RAG evaluation uses four key metrics. Faithfulness: is the answer grounded in context (no hallucination)? Relevance: are retrieved chunks actually useful? Context Recall: did we miss any critical information? Answer Correctness: is the final answer factually accurate? Use RAGAS framework for automated evaluation. Always combine automated metrics with human evaluation.");

      // Slide 9: Production Challenges
      s = p.addSlide();
      addTwoCol(s, "Production Challenges & Fixes", "COMMON ISSUES",
        [{ text: "Chunk boundary breaks context", bold: true }, { text: "→ Use overlap + semantic chunking" }, { text: "" }, { text: "Retrieved irrelevant chunks", bold: true }, { text: "→ Re-ranking, hybrid search" }, { text: "" }, { text: "Stale embeddings", bold: true }, { text: "→ Incremental re-indexing pipeline" }],
        "SOLUTIONS",
        [{ text: "Token budget exceeded", bold: true }, { text: "→ Context compression, top-k tuning" }, { text: "" }, { text: "Slow retrieval", bold: true }, { text: "→ ANN indexes (HNSW), caching" }, { text: "" }, { text: "Metadata filtering", bold: true }, { text: "→ Structured metadata at ingestion" }],
        C.teal, C.orange, "Common production issues: chunk boundaries breaking context (fix: overlap + semantic chunking), irrelevant retrieval (fix: re-ranking + hybrid search), stale embeddings (fix: incremental re-indexing), token budget exceeded (fix: compression + top-k tuning), slow retrieval (fix: approximate nearest neighbor indexes like HNSW + caching).");

      // Slide 10: Enterprise Scenario
      s = p.addSlide();
      s.background = { color: C.orange };
      s.addText("ENTERPRISE SCENARIO", { x: 0, y: 2.0, w: 10, h: 0.5, fontSize: 14, color: "FED7AA", charSpacing: 4, align: "center", fontFace: FB, margin: 0 });
      s.addText("Legal Document\nResearch Assistant", { x: 0, y: 2.5, w: 10, h: 1.4, fontSize: 40, bold: true, color: C.white, align: "center", fontFace: FT, margin: 0 });
      s.addText("LexisAI — RAG-powered case law search for 50K+ legal documents", { x: 0, y: 4.1, w: 10, h: 0.5, fontSize: 15, color: "FED7AA", align: "center", fontFace: FB, margin: 0 });
      s.addNotes("Enterprise scenario: LexisAI, a legal tech company, builds a RAG system over 50,000+ case law documents. Lawyers ask natural language questions and get cited answers with source paragraphs. Uses semantic chunking (preserves legal structure), hybrid search (keyword + vector), and re-ranking for precision. Results: 92% relevance score, 3.2s average response time, 60% reduction in research time.");

      // Slide 11: Takeaways
      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "RAG grounds LLM responses in external knowledge, reducing hallucinations and enabling citations", color: C.teal },
        { num: "2", text: "Embeddings convert text to semantic vectors; chunking strategy directly impacts retrieval quality", color: C.orange },
        { num: "3", text: "Vector databases (Pinecone, Chroma, FAISS) enable fast similarity search at scale", color: C.purple },
        { num: "4", text: "Advanced retrieval: hybrid search, re-ranking, multi-query, and self-query improve precision", color: "3B82F6" },
        { num: "5", text: "Evaluate with faithfulness, relevance, context recall, and answer correctness metrics", color: C.teal },
        { num: "6", text: "Production RAG requires incremental indexing, caching, monitoring, and continuous evaluation", color: C.orange },
      ], "Six key takeaways. 1. RAG grounds LLM responses in external knowledge. 2. Embedding and chunking quality drive retrieval. 3. Vector databases enable fast similarity search. 4. Advanced retrieval techniques improve precision. 5. Evaluate systematically with RAGAS metrics. 6. Production needs indexing pipelines, caching, and monitoring.");
    }
  },

  // MODULE 4
  {
    file: "course-content/part-3-agentic-ai/module-4-agentic-systems/Module-4-Agentic-Systems.pptx",
    label: "MODULE 4", name: "Agentic\nSystems", subtitle: "Autonomous AI Agents & Coordination",
    agenda: [
      { num: "01", text: "Introduction to Agentic AI", color: C.teal },
      { num: "02", text: "Agent Design Patterns", color: C.orange },
      { num: "03", text: "Multi-Agent Coordination", color: C.purple },
      { num: "04", text: "A2A Protocol", color: "3B82F6" },
      { num: "05", text: "Building with LangGraph", color: C.teal },
    ],
    notes: "Module 4 covers agentic AI systems — agents that perceive, reason, act, and learn autonomously. We explore design patterns (ReAct, Plan-and-Execute, Reflection), multi-agent coordination (supervisor, hierarchical, debate, swarm), the A2A communication protocol, and building agents with LangGraph.",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addKPICards(s, "What Makes an Agent?", "Core components of an autonomous AI agent", [
        { value: "👁", label: "Perception", desc: "Input processing from environment (queries, APIs, files)", accent: C.teal },
        { value: "🧠", label: "Reasoning", desc: "Decision-making via CoT, ReAct, planning algorithms", accent: C.orange },
        { value: "⚡", label: "Action", desc: "Executing operations via tools (APIs, DB queries, code)", accent: C.purple },
        { value: "🔄", label: "Reflection", desc: "Self-evaluation and error recovery loops", accent: "3B82F6" },
      ], "An AI agent has five core components: Perception (processing inputs), Memory (short/long-term context), Reasoning (decision-making), Action (tool execution), and Reflection (self-evaluation). Agents exist on an autonomy spectrum from Level 0 (simple LLM) to Level 5 (full autonomy).");

      s = p.addSlide();
      addFeatureGrid(s, "Agent Design Patterns", [
        { icon: "R", color: C.teal, title: "ReAct", desc: "Reason → Act → Observe loop. Transparent reasoning. Best for open-ended Q&A." },
        { icon: "P", color: C.orange, title: "Plan-and-Execute", desc: "Plan strategy first, then execute. Verifiable. Best for complex multi-step tasks." },
        { icon: "T", color: C.purple, title: "Tool Use", desc: "Dynamic tool selection. Flexible, composable. Best for task automation." },
        { icon: "F", color: "3B82F6", title: "Reflection", desc: "Generate → Critique → Refine. High quality. Best for content generation." },
      ], "Four main agent patterns. ReAct: interleaves reasoning with actions (Thought-Action-Observation). Plan-and-Execute: separates planning from execution for better control. Tool Use: agents dynamically select and compose tools. Reflection: agents critique and improve their own outputs through self-evaluation loops.");

      s = p.addSlide();
      addFeatureGrid(s, "Multi-Agent Orchestration", [
        { icon: "S", color: C.teal, title: "Supervisor", desc: "Central coordinator delegates to specialized agents. Simple, controlled." },
        { icon: "H", color: C.orange, title: "Hierarchical", desc: "Tree structure with managers and workers. Scalable delegation." },
        { icon: "D", color: C.purple, title: "Debate", desc: "Agents argue different perspectives. Better decisions through adversarial review." },
        { icon: "W", color: "3B82F6", title: "Swarm", desc: "Parallel independent agents, aggregated results. Emergent coordination." },
      ], "Multi-agent systems overcome single-agent limitations through specialization, parallelism, verification, and scalability. Supervisor: central coordinator delegates tasks. Hierarchical: tree structure with managers/worker agents. Debate: proponent/opponent/moderator argue to reach optimal solutions. Swarm: parallel agents with aggregated results.");

      s = p.addSlide();
      addTwoCol(s, "A2A Communication Protocol", "PATTERNS",
        [{ text: "Request-Response", bold: true }, { text: "Synchronous task delegation" }, { text: "Correlation IDs for matching" }, { text: "" }, { text: "Publish-Subscribe", bold: true }, { text: "Event-driven async communication" }, { text: "Topic-based message routing" }],
        "SECURITY",
        [{ text: "Authentication", bold: true }, { text: "Agent identity tokens, mutual TLS" }, { text: "" }, { text: "Authorization", bold: true }, { text: "Role-based access control" }, { text: "" }, { text: "Rate Limiting", bold: true }, { text: "Per-agent quotas, backpressure" }],
        C.teal, C.orange, "The A2A (Agent-to-Agent) protocol defines standardized communication between autonomous agents. Three patterns: Request-Response (synchronous task delegation), Publish-Subscribe (event-driven async), and Streaming (real-time data flow). Security requires authentication (identity tokens), authorization (RBAC), message integrity (HMAC), and rate limiting.");

      s = p.addSlide();
      addTimeline(s, "LangGraph Agent Architecture", [
        { num: "1", title: "State", desc: "TypedDict schema", color: C.teal },
        { num: "2", title: "Nodes", desc: "Processing functions", color: C.orange },
        { num: "3", title: "Edges", desc: "Flow connections", color: C.purple },
        { num: "4", title: "Compile", desc: "Executable graph", color: "3B82F6" },
        { num: "5", title: "Execute", desc: "invoke/stream/run", color: C.teal },
      ], ["Define state schema", "LLM/Tool/Router nodes", "Normal + conditional", "graph.compile()", "With checkpointing"], "LangGraph builds agents as stateful graphs. 1) State: TypedDict schema flowing through every node. 2) Nodes: functions that read state and return updates. 3) Edges: normal (always) or conditional (router function). 4) Compile: creates executable app with optional checkpointing. 5) Execute: invoke() for completion, stream() for step-by-step.");

      s = p.addSlide();
      addFeatureGrid(s, "Multi-Agent Frameworks", [
        { icon: "C", color: C.teal, title: "CrewAI", desc: "Role-based agents with sequential/hierarchical coordination. Research & content." },
        { icon: "A", color: C.orange, title: "AutoGen", desc: "Conversable agents with event-driven chat. Code generation & analysis." },
        { icon: "L", color: C.purple, title: "LangGraph", desc: "Node-based state machines. Complex workflows with cycles and persistence." },
        { icon: "M", color: "3B82F6", title: "MetaGPT", desc: "SOP-driven structured coordination. Software development automation." },
      ], "Four major multi-agent frameworks. CrewAI: role-based agents, sequential/hierarchical coordination. AutoGen: conversable agents with event-driven chat. LangGraph: node-based state machines with cycles and persistence. MetaGPT: SOP-driven structured coordination for software development. LangGraph is the most flexible for complex production workflows.");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "Agents perceive, reason, act, and reflect — existing on a 5-level autonomy spectrum", color: C.teal },
        { num: "2", text: "ReAct, Plan-and-Execute, Tool Use, and Reflection are the four core design patterns", color: C.orange },
        { num: "3", text: "Multi-agent systems use supervisor, hierarchical, debate, and swarm coordination", color: C.purple },
        { num: "4", text: "A2A protocol standardizes inter-agent communication with security guarantees", color: "3B82F6" },
        { num: "5", text: "LangGraph provides stateful graph orchestration with cycles, persistence, and streaming", color: C.teal },
      ], "Five key takeaways on agentic systems.");
    }
  },

  // MODULE 5
  {
    file: "course-content/part-3-agentic-ai/module-5-mcp/Module-5-Model-Context-Protocol.pptx",
    label: "MODULE 5", name: "Model Context\nProtocol (MCP)", subtitle: "Standardized LLM-Tool Integration",
    agenda: [
      { num: "01", text: "MCP Overview & Motivation", color: C.teal },
      { num: "02", text: "Building MCP Servers", color: C.orange },
      { num: "03", text: "Building MCP Clients", color: C.purple },
      { num: "04", text: "Enterprise Integration", color: "3B82F6" },
    ],
    notes: "Module 5 covers the Model Context Protocol (MCP) — Anthropic's open standard for LLM-tool interaction. MCP provides a unified interface for AI models to discover, describe, and invoke external capabilities through three primitives: Resources, Tools, and Prompts.",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addKPICards(s, "Problems MCP Solves", "From fragmented integrations to a unified protocol", [
        { value: "🔧", label: "Tool Fragmentation", desc: "Each app needs custom integrations → MCP standardizes all", accent: C.teal },
        { value: "🔍", label: "Discovery", desc: "Hard-coded tools → Dynamic discovery via protocol", accent: C.orange },
        { value: "🔒", label: "Security", desc: "Ad-hoc permissions → Built-in authorization framework", accent: C.purple },
        { value: "🔗", label: "Interop", desc: "Vendor lock-in → Open, language-agnostic standard", accent: "3B82F6" },
      ], "MCP solves five problems: tool integration fragmentation (standardized protocol), discovery and description (dynamic tool discovery), security (built-in authorization), scalability (decoupled client-server), and interoperability (open standard).");

      s = p.addSlide();
      addFeatureGrid(s, "MCP Three Primitives", [
        { icon: "R", color: C.teal, title: "Resources", desc: "Read-only data sources. Files, databases, APIs. URI-addressable." },
        { icon: "T", color: C.orange, title: "Tools", desc: "Executable functions. JSON Schema for parameters. Actions the LLM can invoke." },
        { icon: "P", color: C.purple, title: "Prompts", desc: "Reusable templates. Parameterized prompt patterns. Consistent behavior." },
        { icon: "J", color: "3B82F6", title: "JSON-RPC 2.0", desc: "All communication uses JSON-RPC 2.0 over stdio, HTTP/SSE, or WebSocket." },
      ], "MCP defines three primitives: Resources (read-only data — files, DBs, APIs, URI-addressable), Tools (executable functions with JSON Schema parameters), and Prompts (reusable parameterized templates). All communication uses JSON-RPC 2.0 over stdio, HTTP/SSE, or WebSocket transports.");

      s = p.addSlide();
      addTwoCol(s, "Server vs. Client", "MCP SERVER",
        [{ text: "Exposes capabilities", bold: true }, { text: "@server.list_tools() — register tools" }, { text: "@server.call_tool() — execute tools" }, { text: "@server.list_resources() — data sources" }, { text: "@server.list_prompts() — templates" }, { text: "" }, { text: "Python or TypeScript SDK" }],
        "MCP CLIENT",
        [{ text: "Discovers & invokes", bold: true }, { text: "session.list_tools() — discover tools" }, { text: "session.call_tool() — invoke tools" }, { text: "session.read_resource() — read data" }, { text: "session.get_prompt() — get templates" }, { text: "" }, { text: "Connects via stdio or HTTP" }],
        C.teal, C.orange, "MCP follows a client-server architecture. The server exposes capabilities (tools, resources, prompts) using decorators. The client discovers these capabilities dynamically and invokes them. Communication uses JSON-RPC 2.0. Servers can be written in Python or TypeScript. Clients connect via stdio (local) or HTTP/SSE (remote).");

      s = p.addSlide();
      addTimeline(s, "Enterprise MCP Architecture", [
        { num: "1", title: "Clients", desc: "AI agents, apps", color: C.teal },
        { num: "2", title: "Gateway", desc: "Auth + routing", color: C.orange },
        { num: "3", title: "Registry", desc: "Server discovery", color: C.purple },
        { num: "4", title: "Servers", desc: "CRM, ERP, DB", color: "3B82F6" },
        { num: "5", title: "Monitor", desc: "Logging + audit", color: C.teal },
      ], ["Claude, ChatGPT, BI", "Rate limiting, RBAC", "Service mesh", "Salesforce, SAP, Snowflake", "Tool call audit trail"], "Enterprise MCP architecture: Clients (AI agents, chat apps, dashboards) connect through a Gateway (auth, rate limiting, routing) to a Server Registry (service discovery). Individual MCP servers wrap enterprise systems (CRM, ERP, data lake). Monitoring tracks all tool calls for audit and debugging.");

      s = p.addSlide();
      addFeatureGrid(s, "Integration Patterns", [
        { icon: "S", color: C.teal, title: "Sidecar", desc: "MCP server runs alongside main app. Local tool access with minimal latency." },
        { icon: "G", color: C.orange, title: "Gateway", desc: "Central MCP server routes to multiple backends. Enterprise integration hub." },
        { icon: "M", color: C.purple, title: "Mesh", desc: "Multiple MCP servers with service discovery. Microservices architecture." },
        { icon: "P", color: "3B82F6", title: "Proxy", desc: "MCP server wraps legacy APIs. Modernize without rewriting." },
      ], "Five integration patterns: Sidecar (local tool access), Gateway (central routing), Mesh (service discovery), Proxy (legacy wrapping), Aggregator (combine data sources). Security: authentication, authorization, input validation, rate limiting, audit logging, read-only defaults, secrets management.");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "MCP is an open standard for LLM-tool interaction with three primitives: Resources, Tools, Prompts", color: C.teal },
        { num: "2", text: "JSON-RPC 2.0 over stdio, HTTP/SSE, or WebSocket — language-agnostic protocol", color: C.orange },
        { num: "3", text: "Server exposes capabilities; Client discovers and invokes dynamically", color: C.purple },
        { num: "4", text: "Enterprise patterns: Sidecar, Gateway, Mesh, Proxy for scalable integration", color: "3B82F6" },
        { num: "5", text: "Security: auth, RBAC, input validation, rate limiting, audit logging", color: C.teal },
      ], "Five key takeaways on MCP.");
    }
  },

  // MODULE 6
  {
    file: "course-content/part-3-agentic-ai/module-6-langgraph/Module-6-LangGraph.pptx",
    label: "MODULE 6", name: "LangGraph\nDeep Dive", subtitle: "Stateful Graph Orchestration for LLMs",
    agenda: [
      { num: "01", text: "LangGraph Overview", color: C.teal },
      { num: "02", text: "Nodes, Edges & State", color: C.orange },
      { num: "03", text: "Cyclic vs. DAG Graphs", color: C.purple },
      { num: "04", text: "Human-in-the-Loop", color: "3B82F6" },
      { num: "05", text: "Checkpointing & Time Travel", color: C.teal },
    ],
    notes: "Module 6 is a deep dive into LangGraph — the library for building stateful, multi-actor applications with LLMs. We cover StateGraph, state management with reducers, node/edge types, cyclic graphs for self-correction, human-in-the-loop patterns, checkpointing, and time travel.",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addTwoCol(s, "LangGraph vs. LangChain Agents", "LANGCHAIN AGENTS",
        [{ text: "Linear ReAct loop", bold: true }, { text: "Implicit state (history)" }, { text: "Fixed tool-calling loop" }, { text: "No checkpointing" }, { text: "Token-level streaming only" }],
        "LANGGRAPH",
        [{ text: "Arbitrary graph (cycles!)", bold: true }, { text: "Explicit TypedDict state" }, { text: "Conditional branching + routing" }, { text: "Built-in persistence" }, { text: "Step/node/event streaming" }],
        C.red, C.teal, "LangGraph extends LangChain with graph-based state management. Key differences: LangChain agents use linear ReAct loops; LangGraph supports arbitrary graphs with cycles. LangChain has implicit state; LangGraph has explicit TypedDict state. LangGraph adds: conditional branching, checkpointing, human-in-the-loop, subgraphs, time travel, and fine-grained streaming.");

      s = p.addSlide();
      addFeatureGrid(s, "State Management with Reducers", [
        { icon: "M", color: C.teal, title: "add_messages", desc: "Appends messages to list. Used for conversation history accumulation." },
        { icon: "+", color: C.orange, title: "operator.add", desc: "Adds numeric values. Used for iteration counters and accumulators." },
        { icon: "∪", color: C.purple, title: "operator.or_", desc: "Merges dictionaries. Used for config and metadata accumulation." },
        { icon: "C", color: "3B82F6", title: "Custom Reducer", desc: "Your own merge logic. Deep merge, deduplication, custom rules." },
      ], "Reducers define how state updates are merged. add_messages appends to lists (conversation history). operator.add adds numeric values (counters). operator.or_ merges dicts. Custom reducers for complex merging. Use Annotated[type, reducer] syntax. Nodes return only changed fields; LangGraph merges with reducers.");

      s = p.addSlide();
      addFeatureGrid(s, "Node Types in LangGraph", [
        { icon: "L", color: C.teal, title: "LLM Node", desc: "Calls an LLM for reasoning/generation. Core intelligence of the agent." },
        { icon: "T", color: C.orange, title: "Tool Node", desc: "Executes external tools. APIs, database queries, file operations." },
        { icon: "V", color: C.purple, title: "Validator Node", desc: "Checks output quality. Scores, critiques, gates downstream flow." },
        { icon: "H", color: "3B82F6", title: "Human Node", desc: "Waits for human input. Approval checkpoints, manual review." },
      ], "Five node types: LLM Node (reasoning/generation), Tool Node (external actions), Router Node (determines next step), Validator Node (quality checks), Human Node (waits for human input). Node contract: receives full state, returns dict of updates only. Can be sync or async.");

      s = p.addSlide();
      addTwoCol(s, "DAG vs. Cyclic Graphs", "DAG (No Loops)",
        [{ text: "Linear pipelines", bold: true }, { text: "Extract → Transform → Load" }, { text: "Simple RAG: Retrieve → Generate" }, { text: "No retry or self-correction" }, { text: "One pass, start to finish" }],
        "CYCLIC (With Loops)",
        [{ text: "Self-correction loops", bold: true }, { text: "Generate → Critique → Revise" }, { text: "Tool retry on failure" }, { text: "Iterative refinement" }, { text: "ReAct-style think-act-observe" }],
        C.teal, C.orange, "DAG graphs have no cycles — execution flows one direction. Good for: linear pipelines, simple RAG, fixed workflows. Cyclic graphs contain loops for: self-correction (generate → critique → revise), tool retry, iterative refinement, ReAct loops. Use cycles when you need retry, self-evaluation, or multi-pass improvement.");

      s = p.addSlide();
      addFeatureGrid(s, "Human-in-the-Loop Patterns", [
        { icon: "B", color: C.teal, title: "interrupt_before", desc: "Pause before sensitive nodes. Review before deployment or data writes." },
        { icon: "A", color: C.orange, title: "interrupt_after", desc: "Pause after content generation. Review drafts before sending." },
        { icon: "I", color: C.purple, title: "interrupt()", desc: "Node-level pause with custom prompt. Dynamic approval requests." },
        { icon: "T", color: "3B82F6", title: "Time Travel", desc: "Replay from any checkpoint. Branch, edit state, and re-run." },
      ], "Three human-in-the-loop mechanisms: interrupt_before (pause before sensitive actions), interrupt_after (pause after generation for review), interrupt() (node-level dynamic pause). Time travel: get_state_history() to view all checkpoints, replay from any point, edit state and branch. Uses MemorySaver (dev) or SQLiteSaver/PostgresSaver (prod).");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "LangGraph adds cycles, persistence, human-in-the-loop, and fine-grained control over LangChain", color: C.teal },
        { num: "2", text: "State is explicit (TypedDict/Pydantic); reducers define how updates are merged", color: C.orange },
        { num: "3", text: "Nodes return only changed fields; edges can be normal or conditional with router functions", color: C.purple },
        { num: "4", text: "Cyclic graphs enable self-correction, retry, and iterative refinement patterns", color: "3B82F6" },
        { num: "5", text: "Checkpointing + time travel enable debugging, replay, and human approval workflows", color: C.teal },
      ], "Five key takeaways on LangGraph.");
    }
  },

  // MODULE 7
  {
    file: "course-content/part-4-production/module-7-architecture/Module-7-Architecture-Design.pptx",
    label: "MODULE 7", name: "Architecture\nDesign", subtitle: "Scaling, Reliability & Cost Trade-offs",
    agenda: [
      { num: "01", text: "Microservices vs Monolith", color: C.teal },
      { num: "02", text: "API Gateway Patterns", color: C.orange },
      { num: "03", text: "Async Processing & Queues", color: C.purple },
      { num: "04", text: "Model Serving Architectures", color: "3B82F6" },
      { num: "05", text: "Scaling & Cost Optimization", color: C.teal },
    ],
    notes: "Module 7 covers production AI architecture: microservices vs monolith, API gateway patterns, async processing, model serving, caching, load balancing, scaling strategies, reliability patterns, and cost optimization.",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addTwoCol(s, "Architecture Choices", "MONOLITH",
        [{ text: "Single deployable artifact", bold: true }, { text: "In-process calls (sub-ms latency)" }, { text: "Low complexity initially" }, { text: "Scale everything together" }, { text: "Best: small teams, <5 models" }],
        "MICROSERVICES",
        [{ text: "Independent service deployment", bold: true }, { text: "Network calls (1-10ms latency)" }, { text: "High complexity (service mesh)" }, { text: "Scale individual components" }, { text: "Best: large teams, 10+ models" }],
        C.teal, C.orange, "Most AI teams start with a modular monolith — single deployable, internally organized modules. Migrate to microservices when: different scaling needs (GPU vs CPU), independent deployment cycles, regulatory isolation, or multi-API serving. Hybrid approach: modular monolith is the sweet spot for most teams.");

      s = p.addSlide();
      addFeatureGrid(s, "API Gateway for AI", [
        { icon: "R", color: C.teal, title: "Model Routing", desc: "Route to different models by task complexity. Simple → GPT-3.5, complex → GPT-4." },
        { icon: "M", color: C.orange, title: "Token Metering", desc: "Track and enforce token budgets per user/org. 1M tokens/day per org." },
        { icon: "A", color: C.purple, title: "A/B Testing", desc: "Split traffic between model versions. 90% v1, 10% v2 for safe rollouts." },
        { icon: "G", color: "3B82F6", title: "Guard Rails", desc: "Input/output validation at the edge. PII detection, content filters." },
      ], "API Gateway is the single entry point for all client requests. For AI: model routing (complexity-based), token metering (budget enforcement), request queuing (spike buffering), A/B testing (safe rollouts), and guard rails (input/output validation). Solutions: Kong, AWS API Gateway, Envoy, LiteLLM.");

      s = p.addSlide();
      addFeatureGrid(s, "Model Serving Architectures", [
        { icon: "V", color: C.teal, title: "vLLM", desc: "High-throughput serving with PagedAttention. OpenAI-compatible API." },
        { icon: "T", color: C.orange, title: "TGI", desc: "HuggingFace's Text Generation Inference. Optimized for HF models." },
        { icon: "O", color: C.purple, title: "ONNX Runtime", desc: "Cross-platform optimized inference. CPU and GPU support." },
        { icon: "T", color: "3B82F6", title: "Triton", desc: "NVIDIA's multi-model serving. Dynamic batching, model ensembles." },
      ], "Model serving options: vLLM (high-throughput, PagedAttention, OpenAI-compatible), TGI (HuggingFace optimized), ONNX Runtime (cross-platform), Triton (NVIDIA multi-model, dynamic batching). Choose based on: model type, latency requirements, throughput needs, and infrastructure constraints.");

      s = p.addSlide();
      addKPICards(s, "Scaling & Cost Optimization", "Key production metrics and strategies", [
        { value: "Auto", label: "Auto-Scaling", desc: "Scale based on queue depth, latency, or GPU utilization", accent: C.teal },
        { value: "$$$", label: "Model Routing", desc: "Route simple queries to cheaper models, complex to premium", accent: C.orange },
        { value: "Cache", label: "Semantic Caching", desc: "Cache similar queries to avoid redundant LLM calls", accent: C.purple },
        { value: "Batch", label: "Request Batching", desc: "Batch multiple requests for GPU efficiency", accent: "3B82F6" },
      ], "Cost optimization strategies: auto-scaling (scale on queue depth/latency/GPU utilization), model routing (simple queries → cheap model, complex → premium), semantic caching (cache similar queries), request batching (GPU efficiency), and multi-region deployment for reliability.");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "Start with modular monolith; migrate to microservices when scaling/isolation demands it", color: C.teal },
        { num: "2", text: "API Gateway handles routing, metering, A/B testing, and guard rails at the edge", color: C.orange },
        { num: "3", text: "Model serving: vLLM for throughput, TGI for HF models, Triton for multi-model", color: C.purple },
        { num: "4", text: "Cost optimization: model routing, semantic caching, batching, and auto-scaling", color: "3B82F6" },
        { num: "5", text: "Reliability: circuit breakers, retries, fallbacks, health checks, and observability", color: C.teal },
      ], "Five key takeaways on architecture design.");
    }
  },

  // MODULE 8
  {
    file: "course-content/part-4-production/module-8-cicd/Module-8-CI-CD-for-AI.pptx",
    label: "MODULE 8", name: "CI/CD for\nAI Systems", subtitle: "Versioning, Testing & Automated Deployment",
    agenda: [
      { num: "01", text: "Versioning Models & Prompts", color: C.teal },
      { num: "02", text: "DVC & Model Registry", color: C.orange },
      { num: "03", text: "Automated Testing for LLMs", color: C.purple },
      { num: "04", text: "Deployment Pipelines", color: "3B82F6" },
      { num: "05", text: "Git Strategies & Best Practices", color: C.teal },
    ],
    notes: "Module 8 covers CI/CD for AI systems: versioning models, prompts, and data with DVC and model registries; automated testing pipelines for LLM applications; deployment strategies with GitHub Actions; and Git workflows adapted for ML projects.",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addKPICards(s, "What to Version in AI", "Beyond code — version everything", [
        { value: "Code", label: "Application Code", desc: "Standard Git versioning for app logic, chains, agents", accent: C.teal },
        { value: "Data", label: "Training Data", desc: "DVC for large datasets, embeddings, RAG corpora", accent: C.orange },
        { value: "Model", label: "Model Weights", desc: "Model registry for fine-tuned adapters and checkpoints", accent: C.purple },
        { value: "Prompt", label: "Prompt Templates", desc: "Version prompt templates alongside code for reproducibility", accent: "3B82F6" },
      ], "AI systems require versioning beyond code. Four things to version: application code (Git), training datasets (DVC), model weights (model registry), and prompt templates (Git alongside code). Without proper versioning, reproducing results and debugging regressions becomes impossible.");

      s = p.addSlide();
      addTwoCol(s, "DVC vs Model Registry", "DVC (Data Version Control)",
        [{ text: "Extends Git for large files", bold: true }, { text: "Stores pointers in Git, data in S3/GCS" }, { text: "Pipeline-based lineage tracking" }, { text: "dvc repro — reproduce pipelines" }, { text: "Best for: data science teams" }],
        "MODEL REGISTRY (MLflow/Azure ML)",
        [{ text: "Centralized model catalog", bold: true }, { text: "Stage management (staging/prod)" }, { text: "Experiment-based lineage" }, { text: "UI + API access for collaboration" }, { text: "Best for: MLOps/production teams" }],
        C.teal, C.orange, "DVC extends Git for large files — stores pointers in Git, actual data in remote storage (S3, GCS, Azure Blob). Pipeline-based lineage. Model Registry (MLflow, Azure ML) provides centralized catalog with stage management (staging → production → archived), experiment lineage, and UI/API access. Use both: DVC for data science, Registry for production promotion.");

      s = p.addSlide();
      addFeatureGrid(s, "Automated Testing for LLMs", [
        { icon: "U", color: C.teal, title: "Unit Tests", desc: "Component-level assertions. Test parsers, validators, tools independently." },
        { icon: "I", color: C.orange, title: "Integration Tests", desc: "End-to-end workflow validation. Mock external services." },
        { icon: "E", color: C.purple, title: "LLM Evaluation", desc: "Quality metrics: faithfulness, relevance, toxicity. RAGAS, DeepEval." },
        { icon: "S", color: "3B82F6", title: "Security Tests", desc: "Prompt injection, data leakage. Promptfoo, manual pen testing." },
      ], "Four testing levels for LLM apps: Unit tests (component assertions), Integration tests (end-to-end with mocked services), LLM evaluation (faithfulness, relevance, toxicity via RAGAS/DeepEval), and Security tests (prompt injection, data leakage via Promptfoo). Run eval suites in CI to catch regressions before deployment.");

      s = p.addSlide();
      addTimeline(s, "CI/CD Pipeline for LLM Apps", [
        { num: "1", title: "Lint & Type", desc: "Code quality", color: C.teal },
        { num: "2", title: "Unit Tests", desc: "Component tests", color: C.orange },
        { num: "3", title: "LLM Eval", desc: "Quality metrics", color: C.purple },
        { num: "4", title: "Build", desc: "Docker image", color: "3B82F6" },
        { num: "5", title: "Deploy", desc: "Canary rollout", color: C.teal },
      ], ["ruff, mypy, eslint", "pytest with mocks", "RAGAS, DeepEval", "Multi-stage Dockerfile", "10% → 50% → 100%"], "CI/CD pipeline: 1) Lint & type check (ruff, mypy). 2) Unit tests (pytest with mocks). 3) LLM evaluation suite (RAGAS, DeepEval — must pass quality thresholds). 4) Build Docker image (multi-stage). 5) Deploy with canary rollout (10% → 50% → 100%). GitHub Actions orchestrates the pipeline.");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "Version code, data, models, and prompts — all four are critical for reproducibility", color: C.teal },
        { num: "2", text: "DVC for data versioning; Model Registry for stage management and promotion", color: C.orange },
        { num: "3", text: "Automated LLM evaluation (RAGAS, DeepEval) in CI catches quality regressions", color: C.purple },
        { num: "4", text: "CI/CD pipeline: lint → test → eval → build → canary deploy", color: "3B82F6" },
        { num: "5", text: "Git strategies: feature branches for experiments, release branches for staging", color: C.teal },
      ], "Five key takeaways on CI/CD for AI.");
    }
  },

  // MODULE 9
  {
    file: "course-content/part-4-production/module-9-monitoring/Module-9-Monitoring-and-Observability.pptx",
    label: "MODULE 9", name: "Monitoring &\nObservability", subtitle: "Three Pillars for LLM Systems",
    agenda: [
      { num: "01", text: "Observability Fundamentals", color: C.teal },
      { num: "02", text: "LLM-Specific Metrics", color: C.orange },
      { num: "03", text: "Drift Detection", color: C.purple },
      { num: "04", text: "Logging & Distributed Tracing", color: "3B82F6" },
    ],
    notes: "Module 9 covers monitoring and observability for LLM systems: the three pillars (logs, metrics, traces), LLM-specific metrics (latency, tokens, cost, quality), drift detection, and distributed tracing with OpenTelemetry.",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addKPICards(s, "Three Pillars of Observability", "Extended for LLM systems", [
        { value: "Logs", label: "Logs", desc: "Prompt/response pairs, token decisions, tool calls, chain steps", accent: C.teal },
        { value: "Metrics", label: "Metrics", desc: "Token usage, latency percentiles, quality scores, cost per request", accent: C.orange },
        { value: "Traces", label: "Traces", desc: "Multi-step chains, agent reasoning loops, RAG retrieval spans", accent: C.purple },
      ], "LLM observability extends the classic three pillars. Logs: detailed prompt/response pairs, tool calls, chain steps. Metrics: token usage, latency P50/P99, cost per request, quality scores. Traces: request lifecycle across multi-step chains, agent loops, RAG retrieval. Traditional ML monitoring isn't enough — LLMs generate free-form text and make autonomous decisions.");

      s = p.addSlide();
      addFeatureGrid(s, "LLM-Specific Metrics", [
        { icon: "L", color: C.teal, title: "Latency P50/P99", desc: "Target: P50 < 1s, P99 < 5s. Alert: P99 > 15s. Critical for UX." },
        { icon: "T", color: C.orange, title: "Token Usage", desc: "Input + output tokens per request. Spike detection for cost control." },
        { icon: "Q", color: C.purple, title: "Quality Scores", desc: "Hallucination rate, relevance, coherence. LLM-as-judge evaluation." },
        { icon: "C", color: "3B82F6", title: "Cost per Request", desc: "USD per inference. Alert: >2x baseline. Track by model, endpoint." },
      ], "LLM-specific metrics: Operational — latency P50/P99, token usage, cost per request, throughput, error rate, timeout rate. Quality — hallucination rate (LLM-as-judge), relevance score (embedding similarity), coherence, toxicity (Perspective API), user satisfaction (thumbs up/down), task completion rate.");

      s = p.addSlide();
      addTwoCol(s, "Drift Detection & Logging", "DRIFT DETECTION",
        [{ text: "Data Drift", bold: true }, { text: "Input distribution changes over time" }, { text: "Monitor embedding cluster shifts" }, { text: "" }, { text: "Concept Drift", bold: true }, { text: "Relationship between input/output changes" }, { text: "Monitor quality metric trends" }],
        "DISTRIBUTED TRACING",
        [{ text: "OpenTelemetry", bold: true }, { text: "Industry-standard tracing framework" }, { text: "Trace LLM chains end-to-end" }, { text: "" }, { text: "LangSmith / LangFuse", bold: true }, { text: "LLM-native tracing platforms" }, { text: "Token-level visibility per step" }],
        C.teal, C.orange, "Drift detection: Data drift (input distribution shifts — monitor embedding clusters), Concept drift (input-output relationship changes — monitor quality trends). Distributed tracing: OpenTelemetry for industry-standard traces, LangSmith/LangFuse for LLM-native tracing with token-level visibility per chain step. Alert on quality degradation before users notice.");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "LLM observability extends logs, metrics, traces with prompt/response, token, and quality data", color: C.teal },
        { num: "2", text: "Key metrics: latency P99, token usage, cost per request, hallucination rate, user satisfaction", color: C.orange },
        { num: "3", text: "Drift detection monitors input distribution and quality metric trends over time", color: C.purple },
        { num: "4", text: "OpenTelemetry + LangSmith/LangFuse provide end-to-end tracing for LLM chains", color: "3B82F6" },
      ], "Four key takeaways on monitoring and observability.");
    }
  },

  // MODULE 10
  {
    file: "course-content/part-4-production/module-10-governance/Module-10-AI-Governance.pptx",
    label: "MODULE 10", name: "AI Governance\n& Compliance", subtitle: "Risks, Guardrails & Regulations",
    agenda: [
      { num: "01", text: "AI Risk Taxonomy", color: C.teal },
      { num: "02", text: "Content Filtering & Guardrails", color: C.orange },
      { num: "03", text: "Responsible AI Principles", color: C.purple },
      { num: "04", text: "Regulatory Compliance", color: "3B82F6" },
    ],
    notes: "Module 10 covers AI governance and compliance: risk taxonomy (hallucination, bias, prompt injection, data leakage), content filtering, guardrails architecture, responsible AI principles, and regulatory compliance (EU AI Act, GDPR, SOC 2).",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addKPICards(s, "AI Risk Taxonomy", "Production AI faces unique risks traditional software does not", [
        { value: "🚨", label: "Hallucination", desc: "Plausible but incorrect output. LLM cites non-existent papers.", accent: C.red },
        { value: "⚡", label: "Prompt Injection", desc: "Malicious input manipulates model behavior. Bypasses filters.", accent: C.orange },
        { value: "🔓", label: "Data Leakage", desc: "Sensitive training data exposed in outputs. PII reproduction.", accent: C.purple },
        { value: "📉", label: "Model Drift", desc: "Performance degrades as data distributions shift over time.", accent: "3B82F6" },
      ], "AI risk taxonomy: Hallucination (incorrect but plausible output), Bias (systematic unfairness), Prompt Injection (malicious input manipulation), Data Leakage (PII exposure), Toxicity (harmful content), Over-reliance (blind trust), Model Drift (performance degradation), Adversarial Attacks (crafted inputs). Each requires specific mitigations.");

      s = p.addSlide();
      addFeatureGrid(s, "Guardrails Architecture", [
        { icon: "I", color: C.teal, title: "Input Guardrails", desc: "Length validation, sanitization, topic filtering, PII detection/redaction." },
        { icon: "O", color: C.orange, title: "Output Guardrails", desc: "Format validation, factuality checks, toxicity screening, compliance tagging." },
        { icon: "C", color: C.purple, title: "Content Filtering", desc: "OpenAI Moderation API, custom classifiers. Pre/post-screening." },
        { icon: "S", color: "3B82F6", title: "Safety Layers", desc: "Multi-layer defense: input filter → LLM → output filter → human review." },
      ], "Guardrails are programmatic constraints enforcing safe AI behavior. Input: length validation, sanitization (strip injection patterns), topic filtering, PII detection. Output: format validation, factuality checks, toxicity screening, compliance tagging. Content filtering: OpenAI Moderation API, custom classifiers. Safety layers: defense in depth — input filter → LLM → output filter → human review for critical decisions.");

      s = p.addSlide();
      addTwoCol(s, "Responsible AI & Compliance", "RESPONSIBLE AI",
        [{ text: "Fairness", bold: true }, { text: "Bias detection, diverse data, audits" }, { text: "" }, { text: "Transparency", bold: true }, { text: "Model cards, decision explainability" }, { text: "" }, { text: "Accountability", bold: true }, { text: "Human oversight, error reporting" }],
        "REGULATIONS",
        [{ text: "EU AI Act", bold: true }, { text: "Risk-based classification, transparency" }, { text: "" }, { text: "GDPR", bold: true }, { text: "Data protection, right to explanation" }, { text: "" }, { text: "SOC 2", bold: true }, { text: "Security, availability, confidentiality" }],
        C.teal, C.orange, "Responsible AI: Fairness (bias detection, audits), Transparency (model cards, explainability), Accountability (human oversight, error reporting), Privacy (data minimization, consent), Safety (content filtering, monitoring). Regulations: EU AI Act (risk-based classification), GDPR (data protection, right to explanation), SOC 2 (security controls), HIPAA (healthcare data), ISO 42001 (AI management systems).");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "AI risks include hallucination, bias, prompt injection, data leakage, and drift", color: C.teal },
        { num: "2", text: "Guardrails: input sanitization, output validation, content filtering, multi-layer defense", color: C.orange },
        { num: "3", text: "Responsible AI: fairness, transparency, accountability, privacy, safety", color: C.purple },
        { num: "4", text: "Compliance: EU AI Act, GDPR, SOC 2, HIPAA — regulations are evolving rapidly", color: "3B82F6" },
      ], "Four key takeaways on AI governance and compliance.");
    }
  },

  // MODULE 11
  {
    file: "course-content/part-5-fine-tuning-deployment/module-11-fine-tuning/Module-11-Fine-Tuning.pptx",
    label: "MODULE 11", name: "Fine-Tuning\nLLMs", subtitle: "LoRA, QLoRA & PEFT Techniques",
    agenda: [
      { num: "01", text: "When to Fine-Tune vs RAG", color: C.teal },
      { num: "02", text: "Data Preparation", color: C.orange },
      { num: "03", text: "LoRA, QLoRA & PEFT", color: C.purple },
      { num: "04", text: "Implementation Walkthrough", color: "3B82F6" },
    ],
    notes: "Module 11 covers fine-tuning LLMs: when to fine-tune vs prompt engineering vs RAG, data preparation (JSONL format, quality checklist), fine-tuning techniques (LoRA, QLoRA, PEFT), and implementation walkthroughs with Hugging Face and OpenAI.",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addTwoCol(s, "Fine-Tune vs Prompt vs RAG", "USE PROMPT ENGINEERING WHEN",
        [{ text: "Quick prototyping", bold: true }, { text: "General tasks" }, { text: "< 50 examples available" }, { text: "No domain-specific tone needed" }],
        "USE FINE-TUNING WHEN",
        [{ text: "Consistent tone/format needed", bold: true }, { text: "Domain-specific vocabulary" }, { text: "500+ high-quality examples" }, { text: "Reduce prompt token costs" }],
        C.teal, C.orange, "Decision framework: Prompt engineering for quick prototyping, general tasks, <50 examples. RAG for dynamic knowledge, FAQs, frequent data changes. Fine-tuning for consistent tone/format, domain vocabulary, 500+ examples, reduced token costs. Try prompt engineering first, then RAG, then fine-tuning as last resort.");

      s = p.addSlide();
      addFeatureGrid(s, "Fine-Tuning Techniques", [
        { icon: "L", color: C.teal, title: "LoRA", desc: "Low-Rank Adaptation. Trains small rank decomposition matrices. 0.1% of params." },
        { icon: "Q", color: C.orange, title: "QLoRA", desc: "Quantized LoRA. 4-bit quantization + LoRA. Trains 65B models on single GPU." },
        { icon: "P", color: C.purple, title: "PEFT", desc: "Parameter-Efficient Fine-Tuning. Umbrella term for LoRA, prefix tuning, adapters." },
        { icon: "F", color: "3B82F6", title: "Full Fine-Tuning", desc: "Updates all parameters. Highest quality but most expensive. Rarely needed." },
      ], "Fine-tuning techniques: LoRA (Low-Rank Adaptation) — trains small decomposition matrices, ~0.1% of parameters. QLoRA — 4-bit quantization + LoRA, trains 65B models on single GPU. PEFT — umbrella for parameter-efficient methods (LoRA, prefix tuning, adapters). Full fine-tuning — updates all params, highest quality but most expensive. LoRA/QLoRA are the standard for most use cases.");

      s = p.addSlide();
      addKPICards(s, "Training Hyperparameters", "Key parameters for fine-tuning success", [
        { value: "1e-4", label: "Learning Rate", desc: "1e-5 to 5e-4. Too high → divergence, too low → slow convergence", accent: C.teal },
        { value: "3", label: "Epochs", desc: "1-5 typically. More epochs → overfitting risk on small datasets", accent: C.orange },
        { value: "16-64", label: "LoRA Rank", desc: "Higher → more capacity, more memory. Start with 16, increase if needed", accent: C.purple },
        { value: "2×", label: "LoRA Alpha", desc: "Typically 2× rank. Scaling factor for LoRA weight updates", accent: "3B82F6" },
      ], "Key hyperparameters: Learning rate (1e-5 to 5e-4), epochs (1-5), batch size (1-16), warmup steps (10% of total), max sequence length (512-4096), weight decay (0.01-0.1), LoRA rank (8-64), LoRA alpha (typically 2× rank). Quality data is the single most important factor — garbage in, garbage out.");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "Try prompt engineering → RAG → fine-tuning. Fine-tuning is last resort for tone/format/domain", color: C.teal },
        { num: "2", text: "Data quality > quantity. 500+ high-quality JSONL examples, consistent format", color: C.orange },
        { num: "3", text: "LoRA/QLoRA are the standard — train 0.1% of parameters, 65B on single GPU", color: C.purple },
        { num: "4", text: "Evaluate with task-specific metrics; compare against base model and prompt engineering baseline", color: "3B82F6" },
      ], "Four key takeaways on fine-tuning.");
    }
  },

  // MODULE 12
  {
    file: "course-content/part-5-fine-tuning-deployment/module-12-deployment/Module-12-Deployment.pptx",
    label: "MODULE 12", name: "Deployment\nStrategies", subtitle: "Containers, Kubernetes & Serverless",
    agenda: [
      { num: "01", text: "Containerization for LLMs", color: C.teal },
      { num: "02", text: "Kubernetes & Orchestration", color: C.orange },
      { num: "03", text: "Serverless Deployment", color: C.purple },
      { num: "04", text: "Model Serving & GPU Optimization", color: "3B82F6" },
      { num: "05", text: "Deployment Patterns", color: C.teal },
    ],
    notes: "Module 12 covers deployment strategies for LLM applications: containerization with Docker, Kubernetes orchestration, serverless deployment, model serving frameworks, GPU optimization, auto-scaling, and deployment patterns (canary, blue-green, rolling).",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addKPICards(s, "Why Containers for LLMs?", "Portable, reproducible, scalable deployment", [
        { value: "📦", label: "Reproducibility", desc: "Identical environments across dev, staging, production", accent: C.teal },
        { value: "🔒", label: "Isolation", desc: "Model deps don't conflict with host or other services", accent: C.orange },
        { value: "☁️", label: "Portability", desc: "Run on any container runtime — Docker, Podman, containerd", accent: C.purple },
        { value: "📈", label: "Scalability", desc: "Orchestrate with Kubernetes, ECS, or Container Apps", accent: "3B82F6" },
      ], "Containerization packages LLM apps with all dependencies into portable units. Benefits: reproducibility (identical environments), isolation (no dependency conflicts), portability (any container runtime), scalability (Kubernetes/ECS orchestration), version control (tag images). Multi-stage builds reduce image size from 12GB to 6GB.");

      s = p.addSlide();
      addFeatureGrid(s, "Deployment Patterns", [
        { icon: "C", color: C.teal, title: "Canary", desc: "Route 5% traffic to new version. Monitor metrics. Gradually increase to 100%." },
        { icon: "B", color: C.orange, title: "Blue-Green", desc: "Two identical environments. Switch traffic instantly. Easy rollback." },
        { icon: "R", color: C.purple, title: "Rolling", desc: "Replace pods one by one. Zero downtime. Default Kubernetes strategy." },
        { icon: "A", color: "3B82F6", title: "A/B Testing", desc: "Split traffic by user segment. Compare metrics. Data-driven decisions." },
      ], "Deployment patterns: Canary (5% → 25% → 50% → 100%, monitor at each step), Blue-Green (two environments, instant switch, easy rollback), Rolling (replace pods one by one, zero downtime), A/B Testing (split by user segment, compare metrics). For LLM apps: canary is safest — monitor quality metrics (hallucination rate, latency) at each stage.");

      s = p.addSlide();
      addTwoCol(s, "Kubernetes & Serverless", "KUBERNETES (K8s)",
        [{ text: "Container orchestration", bold: true }, { text: "Pods, Services, Deployments" }, { text: "Horizontal Pod Autoscaler" }, { text: "Best: steady traffic, GPU workloads" }, { text: "Managed: AKS, EKS, GKE" }],
        "SERVERLESS",
        [{ text: "No infrastructure management", bold: true }, { text: "Pay per invocation" }, { text: "Auto-scale to zero" }, { text: "Best: variable traffic, APIs" }, { text: "Azure Functions, AWS Lambda" }],
        C.teal, C.orange, "Kubernetes: container orchestration with pods, services, deployments, horizontal pod autoscaler. Best for steady traffic and GPU workloads. Managed options: AKS, EKS, GKE. Serverless: no infra management, pay per invocation, auto-scale to zero. Best for variable traffic and API endpoints. Azure Functions, AWS Lambda, Azure Container Apps. Trade-off: K8s = control, Serverless = simplicity.");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "Containerize LLM apps with multi-stage Docker builds for reproducibility and portability", color: C.teal },
        { num: "2", text: "Kubernetes for steady/GPU workloads; Serverless for variable traffic and simplicity", color: C.orange },
        { num: "3", text: "Deployment patterns: canary (safest), blue-green (easy rollback), rolling (zero downtime)", color: C.purple },
        { num: "4", text: "GPU optimization: quantization, batching, KV caching, model parallelism", color: "3B82F6" },
        { num: "5", text: "Health checks, readiness probes, and graceful shutdown are essential for production", color: C.teal },
      ], "Five key takeaways on deployment strategies.");
    }
  },

  // MODULE 13
  {
    file: "course-content/part-5-fine-tuning-deployment/module-13-llmops/Module-13-LLMOps.pptx",
    label: "MODULE 13", name: "LLMOps", subtitle: "Operations for LLM Applications at Scale",
    agenda: [
      { num: "01", text: "LLMOps vs MLOps", color: C.teal },
      { num: "02", text: "AI Lifecycle & Experiment Tracking", color: C.orange },
      { num: "03", text: "Infrastructure & Deployment", color: C.purple },
      { num: "04", text: "Monitoring, Security & Cost", color: "3B82F6" },
    ],
    notes: "Module 13 covers LLMOps — the practices, tools, and processes for deploying and maintaining LLM apps in production. We compare LLMOps vs MLOps, cover the AI lifecycle, experiment tracking with MLflow, infrastructure setup, deployment strategies, monitoring, security, and cost optimization.",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addTwoCol(s, "LLMOps vs MLOps", "MLOPS",
        [{ text: "Custom-trained models", bold: true }, { text: "Model weights + training pipeline" }, { text: "Accuracy, F1, AUC metrics" }, { text: "Feature stores, labeled data" }, { text: "Retrain on new data" }],
        "LLMOPS",
        [{ text: "Pre-trained foundation models", bold: true }, { text: "Prompts, chains, agents, adapters" }, { text: "Hallucination, faithfulness, toxicity" }, { text: "Prompt templates, RAG corpora" }, { text: "Prompt tuning, RAG updates, model swaps" }],
        C.teal, C.orange, "LLMOps extends MLOps with LLM-specific concerns. MLOps: custom-trained models, weights + pipeline, accuracy/F1/AUC, feature stores, retrain on new data. LLMOps: pre-trained foundation models, prompts/chains/agents, hallucination/faithfulness/toxicity, prompt templates/RAG corpora, prompt tuning/RAG updates/model swaps. Core artifacts shift from model weights to prompt templates and orchestration logic.");

      s = p.addSlide();
      addFeatureGrid(s, "AI Lifecycle & Experiment Tracking", [
        { icon: "D", color: C.teal, title: "Design", desc: "Use case selection, architecture design, constraint mapping." },
        { icon: "B", color: C.orange, title: "Build", desc: "Prompt engineering, RAG pipelines, chain composition, agent logic." },
        { icon: "E", color: C.purple, title: "Evaluate", desc: "Offline evals, online A/B testing, RAGAS, LangSmith." },
        { icon: "M", color: "3B82F6", title: "Monitor", desc: "Latency, cost, quality, safety. Continuous feedback loop." },
      ], "The AI lifecycle: Design (use case, architecture, constraints) → Build (prompt eng, RAG, chains, agents) → Evaluate (offline evals, online A/B) → Deploy (canary, blue-green) → Monitor (latency, cost, quality, safety) → Feedback loop. Experiment tracking with MLflow: log parameters, metrics, prompt templates, and model artifacts for reproducibility.");

      s = p.addSlide();
      addKPICards(s, "LLMOps Key Concepts", "Tools and practices for production LLM apps", [
        { value: "Registry", label: "Model Registry", desc: "Track model versions, metadata, lineage (MLflow, Azure ML)", accent: C.teal },
        { value: "A/B", label: "A/B Testing", desc: "Compare model versions or prompt variants on live traffic", accent: C.orange },
        { value: "Guard", label: "Guard Rails", desc: "Input/output validation, content filtering, safety classifiers", accent: C.purple },
        { value: "Feature", label: "Feature Store", desc: "Manage RAG chunks, embedding indexes, prompt templates", accent: "3B82F6" },
      ], "Key LLMOps concepts: Model Registry (version tracking, stage management), Experiment Tracking (log prompts, params, metrics — MLflow), Pipeline Orchestration (automate data → inference → eval → deploy), Feature Store (RAG chunks, embedding indexes), A/B Testing (live traffic comparison), Guard Rails (input/output validation).");

      s = p.addSlide();
      addFeatureGrid(s, "Cost Optimization Strategies", [
        { icon: "R", color: C.teal, title: "Model Routing", desc: "Route simple queries to cheaper models (GPT-3.5), complex to GPT-4." },
        { icon: "C", color: C.orange, title: "Semantic Caching", desc: "Cache responses for similar queries. 30-60% cost reduction." },
        { icon: "B", color: C.purple, title: "Batch Processing", desc: "Batch non-real-time requests. Lower per-token cost." },
        { icon: "O", color: "3B82F6", title: "Open Source Models", desc: "Self-host smaller models for high-volume, low-complexity tasks." },
      ], "Cost optimization: Model routing (simple → cheap, complex → premium — 40-60% savings), Semantic caching (cache similar queries — 30-60% savings), Batch processing (lower per-token cost for non-real-time), Open-source models (self-host for high-volume tasks), Prompt optimization (reduce token usage), Token budget enforcement (per-user/org limits).");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "LLMOps extends MLOps with prompt management, token observability, and safety monitoring", color: C.teal },
        { num: "2", text: "AI lifecycle is iterative: Design → Build → Evaluate → Deploy → Monitor → repeat", color: C.orange },
        { num: "3", text: "Experiment tracking (MLflow) enables reproducibility across prompt and model versions", color: C.purple },
        { num: "4", text: "Cost optimization: model routing, semantic caching, batching, open-source models", color: "3B82F6" },
        { num: "5", text: "Security: prompt injection defense, PII protection, compliance (GDPR, SOC 2)", color: C.teal },
      ], "Five key takeaways on LLMOps.");
    }
  },

  // MODULE 14
  {
    file: "course-content/part-6-capstone/module-14-projects/Module-14-Capstone-Projects.pptx",
    label: "MODULE 14", name: "Capstone\nProjects", subtitle: "Production-Grade AI Applications",
    agenda: [
      { num: "01", text: "Project Methodology", color: C.teal },
      { num: "02", text: "Project 1: Book Recommender", color: C.orange },
      { num: "03", text: "Project 2: Customer Support", color: C.purple },
      { num: "04", text: "Project 3: Market Intelligence", color: "3B82F6" },
      { num: "05", text: "Project 4: Multi-Agent Researcher", color: C.teal },
      { num: "06", text: "Production Readiness Checklist", color: C.orange },
    ],
    notes: "Module 14 is the capstone — four production-grade projects that integrate everything from Modules 1-13. We cover the project lifecycle methodology, then walk through each project: Book Recommender (RAG), Customer Support Engine (LangChain agents), Market Intelligence Agent (MCP + tools), and Multi-Agent Researcher (LangGraph).",
    slides: (p) => {
      let s;
      s = p.addSlide();
      addTimeline(s, "Project Lifecycle Methodology", [
        { num: "1", title: "Discover", desc: "Requirements", color: C.teal },
        { num: "2", title: "Design", desc: "Architecture", color: C.orange },
        { num: "3", title: "Build", desc: "Implement", color: C.purple },
        { num: "4", title: "Test", desc: "Validate", color: "3B82F6" },
        { num: "5", title: "Deploy", desc: "Release", color: C.teal },
        { num: "6", title: "Monitor", desc: "Observe", color: C.orange },
      ], ["Stakeholder interviews", "ADR, tech selection", "2-week sprints", "Unit, eval, security", "Canary rollout", "Metrics, feedback"], "Seven-phase lifecycle: Discover (requirements, data audit, constraints) → Design (architecture, model selection, ADR) → Build (2-week sprints) → Test (unit, integration, LLM eval, security) → Deploy (canary rollout) → Monitor (latency, cost, quality) → Iterate (feedback loop). Each project follows this methodology.");

      s = p.addSlide();
      addFeatureGrid(s, "Capstone Projects Overview", [
        { icon: "B", color: C.teal, title: "Book Recommender", desc: "RAG over 500K book descriptions. Semantic search + metadata filtering." },
        { icon: "C", color: C.orange, title: "Customer Support", desc: "LangChain agent with tools. Ticket classification, FAQ, escalation." },
        { icon: "M", color: C.purple, title: "Market Intelligence", desc: "MCP integration. Real-time data from multiple enterprise sources." },
        { icon: "R", color: "3B82F6", title: "Multi-Agent Researcher", desc: "LangGraph workflow. Research → analyze → synthesize → report." },
      ], "Four capstone projects integrating all course modules. 1) Book Recommender: RAG pipeline over 500K descriptions with Azure AI Search. 2) Customer Support Engine: LangChain agent with CRM, knowledge base, and ticketing tools. 3) Market Intelligence Agent: MCP servers integrating CRM, financial APIs, and news feeds. 4) Multi-Agent Researcher: LangGraph with researcher, analyst, writer agents in a cyclic workflow.");

      s = p.addSlide();
      addKPICards(s, "Production Readiness Checklist", "Before going live, verify these", [
        { value: "✓", label: "Evaluation", desc: "RAGAS scores pass thresholds, human eval complete", accent: C.teal },
        { value: "✓", label: "Security", desc: "Prompt injection tested, PII redaction verified", accent: C.orange },
        { value: "✓", label: "Reliability", desc: "Fallbacks, retries, circuit breakers, health checks", accent: C.purple },
        { value: "✓", label: "Observability", desc: "Logging, tracing, metrics dashboards, alerting", accent: "3B82F6" },
      ], "Production readiness checklist: 1) Evaluation — RAGAS scores pass thresholds, human eval complete. 2) Security — prompt injection tested, PII redaction verified, guardrails active. 3) Reliability — fallbacks, retries, circuit breakers, health checks. 4) Observability — logging, tracing (OpenTelemetry), dashboards, alerting. 5) Cost — token budgets enforced, model routing configured. 6) Compliance — GDPR, SOC 2, audit trail.");

      s = p.addSlide();
      addTakeaways(s, "Key Takeaways", [
        { num: "1", text: "Follow a disciplined lifecycle: Discover → Design → Build → Test → Deploy → Monitor → Iterate", color: C.teal },
        { num: "2", text: "Each capstone project integrates multiple modules: RAG, agents, MCP, LangGraph", color: C.orange },
        { num: "3", text: "Production readiness: evaluation, security, reliability, observability, cost, compliance", color: C.purple },
        { num: "4", text: "Architecture Decision Records (ADRs) document key technical choices and trade-offs", color: "3B82F6" },
        { num: "5", text: "Sprint-based implementation with continuous evaluation ensures quality at every stage", color: C.teal },
      ], "Five key takeaways from the capstone module.");
    }
  },
];

// ──────────────────────────────────────────────
// GENERATE ALL PRESENTATIONS
// ──────────────────────────────────────────────
async function generateAll() {
  for (const mod of modules) {
    const pres = new pptxgen();
    pres.layout = "LAYOUT_16x9";
    pres.title = mod.name.replace(/\n/g, " ");

    // Slide 1: Title + Agenda
    let s1 = pres.addSlide();
    addTitleAgenda(s1, mod.name, mod.subtitle, mod.label, mod.agenda,
      `Welcome to ${mod.label}. ${mod.notes}`);

    // Module-specific slides
    mod.slides(pres);

    // Final slide: Takeaways (already included in module slides)
    // Thank You
    const nextIdx = modules.indexOf(mod) + 1;
    const nextMod = nextIdx < modules.length ? modules[nextIdx] : null;
    const sLast = pres.addSlide();
    addThankYou(sLast,
      nextMod ? `Module ${nextIdx + 1} — ${nextMod.name.replace(/\n/g, " ")}` : "Course Complete!",
      `This concludes ${mod.label}. Students should review the concepts, interview questions, and quiz materials before proceeding.`
    );

    const outputPath = path.join("D:/Jay Rathod/Tutorials/Applied AI", mod.file);
    await pres.writeFile({ fileName: outputPath });
    console.log(`✅ ${mod.label}: ${outputPath}`);
  }
  console.log("\n🎉 All presentations generated!");
}

generateAll().catch(console.error);
