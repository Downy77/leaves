import math
import re
from collections import Counter

from app.models import DocumentChunk


TOKEN_PATTERN = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def compute_tfidf_scores(question: str, chunks: list[DocumentChunk]) -> list[tuple[DocumentChunk, float]]:
    query_tokens = tokenize(question)
    if not query_tokens or not chunks:
        return []

    query_counts = Counter(query_tokens)
    doc_tokens = [tokenize(chunk.content) for chunk in chunks]
    doc_freq: Counter[str] = Counter()

    for tokens in doc_tokens:
        for token in set(tokens):
            doc_freq[token] += 1

    total_docs = len(chunks)
    scores: list[tuple[DocumentChunk, float]] = []
    for chunk, tokens in zip(chunks, doc_tokens, strict=False):
        if not tokens:
            continue

        token_counts = Counter(tokens)
        score = 0.0
        for token, qtf in query_counts.items():
            if token not in token_counts:
                continue
            tf = token_counts[token] / len(tokens)
            idf = math.log((1 + total_docs) / (1 + doc_freq[token])) + 1
            score += qtf * tf * idf

        if score > 0:
            scores.append((chunk, score))

    return sorted(scores, key=lambda item: item[1], reverse=True)


def build_answer(question: str, matches: list[DocumentChunk]) -> str:
    if not matches:
        return (
            f"没有在知识库中找到与问题“{question}”足够相关的内容。"
            "请尝试换一种问法，或者先上传更相关的文档。"
        )

    summary_lines = [
        f"问题：{question}",
        "根据知识库检索到的内容，最相关的信息如下：",
    ]
    for index, chunk in enumerate(matches, start=1):
        summary_lines.append(f"{index}. 来源文件：{chunk.filename}")
        summary_lines.append(f"   片段内容：{chunk.content}")
    return "\n".join(summary_lines)
