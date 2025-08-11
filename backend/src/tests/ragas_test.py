import json
import re
from collections import Counter

from ragas import EvaluationDataset, SingleTurnSample, evaluate


def simple_bleu_score(reference, candidate):
    """Tính BLEU score đơn giản cho 1-gram"""
    ref_words = reference.lower().split()
    cand_words = candidate.lower().split()

    if not ref_words or not cand_words:
        return 0.0

    # Count overlapping words
    ref_counter = Counter(ref_words)
    cand_counter = Counter(cand_words)

    overlap = sum((ref_counter & cand_counter).values())
    total_cand_words = len(cand_words)

    if total_cand_words == 0:
        return 0.0

    precision = overlap / total_cand_words

    # Simple brevity penalty
    ref_len = len(ref_words)
    cand_len = len(cand_words)

    if cand_len > ref_len:
        bp = 1.0
    else:
        bp = cand_len / ref_len if ref_len > 0 else 0.0

    return precision * bp


def simple_rouge_score(reference, candidate):
    """Tính ROUGE-1 score đơn giản"""
    ref_words = set(reference.lower().split())
    cand_words = set(candidate.lower().split())

    if not ref_words:
        return 0.0

    overlap = len(ref_words & cand_words)
    return overlap / len(ref_words)


def semantic_similarity_score(reference, candidate):
    """Tính similarity dựa trên keyword overlap"""
    # Extract important keywords (remove common words)
    common_words = {
        "của",
        "là",
        "có",
        "được",
        "và",
        "trong",
        "với",
        "cho",
        "khi",
        "đã",
        "sẽ",
        "này",
        "đó",
        "một",
        "các",
        "về",
        "từ",
        "để",
        "tại",
        "bạn",
        "chúng",
        "tôi",
        "anh",
        "em",
        "không",
        "mà",
        "đi",
        "lại",
        "như",
        "theo",
        "nó",
        "họ",
        "cũng",
        "đều",
        "nếu",
        "vì",
        "khi",
        "mà",
        "nào",
        "đây",
        "đó",
        "gì",
        "thì",
        "hay",
        "nhưng",
        "hoặc",
        "mỗi",
        "cả",
        "nhiều",
        "ít",
        "lớn",
        "nhỏ",
    }

    ref_words = [
        word
        for word in reference.lower().split()
        if word not in common_words and len(word) > 2
    ]
    cand_words = [
        word
        for word in candidate.lower().split()
        if word not in common_words and len(word) > 2
    ]

    ref_set = set(ref_words)
    cand_set = set(cand_words)

    if not ref_set:
        return 1.0 if not cand_set else 0.0

    overlap = len(ref_set & cand_set)
    union = len(ref_set | cand_set)

    if union == 0:
        return 1.0

    return overlap / union


def coverage_score(reference, candidate):
    """Tính tỷ lệ thông tin quan trọng được cover"""
    # Find numbers, prices, and important terms
    ref_numbers = re.findall(r"\d+", reference)
    cand_numbers = re.findall(r"\d+", candidate)

    ref_upper = re.findall(r"[A-Z][A-Z]+", reference)  # Brand names
    cand_upper = re.findall(r"[A-Z][A-Z]+", candidate)

    total_important = len(ref_numbers) + len(ref_upper)
    if total_important == 0:
        return 1.0

    covered_numbers = len(set(ref_numbers) & set(cand_numbers))
    covered_upper = len(set(ref_upper) & set(cand_upper))

    return (covered_numbers + covered_upper) / total_important


# Read data from JSON file
def load_json_as_evaluation_dataset(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Không tìm thấy file {json_path}")
        return None

    # Create samples list for ragas
    samples = []
    for item in data:
        sample = SingleTurnSample(
            user_input=item["question"],
            response=re.sub(r"[\n\t\\*]", "", item["answer"]),
            reference=item["ground_truth"],
            retrieved_contexts=item["context"],
        )
        samples.append(sample)

    return EvaluationDataset(samples=samples)


# Path to test data file
json_path = r"E:\Python\Chatbot-RAG\backend\test_ragas.json"

# Load dataset
dataset = load_json_as_evaluation_dataset(json_path)

if dataset is None:
    print("Không thể tải dataset. Kiểm tra đường dẫn file.")
    exit(1)

print("🚀 Bắt đầu đánh giá tổng hợp với Ragas...")

# Evaluate with available Ragas metrics
try:
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        context_relevancy,
        faithfulness,
    )

    print("📊 Đang chạy Ragas evaluation...")

    metrics = [
        faithfulness,
        answer_relevancy,
        context_relevancy,
        context_recall,
        context_precision,
    ]

    results = evaluate(dataset=dataset, metrics=metrics)

    print("✅ Ragas evaluation hoàn tất!")

    # Convert to DataFrame
    df = results.to_pandas()
    print(f"📈 Processed {len(df)} samples")

except Exception as e:
    print(f"⚠️ Lỗi Ragas evaluation: {e}")
    df = None

# Evaluate custom metrics
print("\n🔧 Đang chạy custom metrics...")

custom_scores = {
    "bleu_score": [],
    "rouge_score": [],
    "semantic_similarity": [],
    "coverage_score": [],
    "exact_match_custom": [],
}

for i, sample in enumerate(dataset):
    reference = sample.reference
    candidate = sample.response

    # Calculate scores
    bleu = simple_bleu_score(reference, candidate)
    rouge = simple_rouge_score(reference, candidate)
    semantic = semantic_similarity_score(reference, candidate)
    coverage = coverage_score(reference, candidate)
    exact = 1.0 if reference.strip().lower() == candidate.strip().lower() else 0.0

    custom_scores["bleu_score"].append(bleu)
    custom_scores["rouge_score"].append(rouge)
    custom_scores["semantic_similarity"].append(semantic)
    custom_scores["coverage_score"].append(coverage)
    custom_scores["exact_match_custom"].append(exact)

# Calculate average
avg_scores = {
    metric: sum(scores) / len(scores) for metric, scores in custom_scores.items()
}

print("\n📊 --- Kết Quả Đánh Giá Tổng Hợp ---")
print("=" * 50)

if df is not None:
    print("🔹 Ragas Metrics:")
    for col in df.columns:
        if col not in ["user_input", "response", "reference", "retrieved_contexts"]:
            score = df[col].mean()
            print(f"   {col}: {score:.4f}")

print("\n🔹 Custom Metrics:")
for metric, score in avg_scores.items():
    emoji = (
        "🎯"
        if metric == "exact_match_custom"
        else "📝"
        if "bleu" in metric or "rouge" in metric
        else "🧠"
        if "semantic" in metric
        else "📋"
    )
    print(f"   {emoji} {metric}: {score:.4f}")

print("\n🔍 --- Detailed Analysis of Top 3 Samples ---")
print("=" * 50)

for i in range(min(3, len(dataset))):
    sample = dataset[i]
    print(f"\n📌 Sample {i + 1}:")
    print(f"❓ Câu hỏi: {sample.user_input}")
    print(f"✅ Ground truth: {sample.reference}")
    print(
        f"🤖 Response: {sample.response[:150]}{'...' if len(sample.response) > 150 else ''}"
    )

    print("📊 Scores:")
    print(f"   BLEU: {custom_scores['bleu_score'][i]:.3f}")
    print(f"   ROUGE: {custom_scores['rouge_score'][i]:.3f}")
    print(f"   Semantic: {custom_scores['semantic_similarity'][i]:.3f}")
    print(f"   Coverage: {custom_scores['coverage_score'][i]:.3f}")

print("\n📈 --- Phân Loại Chất Lượng Responses ---")
print("=" * 50)

excellent = sum(1 for score in custom_scores["semantic_similarity"] if score > 0.7)
good = sum(1 for score in custom_scores["semantic_similarity"] if 0.4 < score <= 0.7)
fair = sum(1 for score in custom_scores["semantic_similarity"] if 0.2 < score <= 0.4)
poor = sum(1 for score in custom_scores["semantic_similarity"] if score <= 0.2)

total = len(custom_scores["semantic_similarity"])

print(f"🌟 Excellent (>0.7): {excellent}/{total} ({excellent / total * 100:.1f}%)")
print(f"✅ Good (0.4-0.7): {good}/{total} ({good / total * 100:.1f}%)")
print(f"⚠️ Fair (0.2-0.4): {fair}/{total} ({fair / total * 100:.1f}%)")
print(f"❌ Poor (≤0.2): {poor}/{total} ({poor / total * 100:.1f}%)")

print("\n🎉 --- Đánh Giá Hoàn Tất ---")
print("=" * 50)
print("💡 Gợi ý cải tiến:")
print("1. 🔧 Tối ưu prompts để tăng semantic similarity")
print("2. 📚 Cải thiện retrieval context cho RAG")
print("3. 🎯 Fine-tune model cho domain điện thoại")
print("4. 🌐 Sử dụng embedding models tiếng Việt")
print("5. ⚡ Thử nghiệm với các LLM mạnh hơn")
