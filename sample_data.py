"""Grounded sample single-video analyses so the dashboard can be explored with zero API calls."""
from __future__ import annotations

from analytics_service import build_dashboard_analytics
from transcript_service import format_timestamp


def _build_gpt_sample() -> dict:
    metadata = {
        "id": "wjZofJX0v4M",
        "title": "But what is a GPT? Visual intro to transformers | Chapter 5, Deep Learning",
        "channel": "3Blue1Brown",
        "description": (
            "Visual introduction to the Transformer architecture powering Generative Pre-trained Transformers (GPT). "
            "Covers tokenization, high-dimensional word embeddings, attention layers, multi-layer perceptrons, "
            "unembedding, and softmax temperature sampling."
        ),
        "published_at": "2024-04-01T15:00:00Z",
        "thumbnail": "https://i.ytimg.com/vi/wjZofJX0v4M/maxresdefault.jpg",
        "duration": "PT27M14S",
        "duration_seconds": 1634,
        "view_count": 9420000,
        "like_count": 312000,
        "comment_count": 8450,
        "metadata_source": "sample_showcase",
        "url": "https://www.youtube.com/watch?v=wjZofJX0v4M",
    }

    raw_segments = [
        (0, 28, "GPT stands for Generative Pre-trained Transformer. The first two words are self-explanatory: generative means the model generates new text, and pre-trained means it learned patterns from massive amounts of data beforehand."),
        (28, 42, "The real invention that sparked the current boom in AI is the final word: Transformer, a specific neural network architecture introduced by researchers at Google in 2017."),
        (70, 52, "In this visual walkthrough, our goal is to follow data step by step as it flows through a Transformer so you have a concrete mental model of what happens inside ChatGPT or any large language model."),
        (122, 58, "Step one is breaking input text into little pieces called tokens. For text, tokens are commonly words, word fragments, or punctuation marks, each mapped to a fixed vocabulary index."),
        (180, 65, "Every token is initially associated with a high-dimensional vector via an embedding matrix. In GPT-3, each embedding vector has 12,288 dimensions, where geometric directions encode semantic meaning."),
        (245, 70, "Words with similar meanings land near each other in this embedding space, and classic vector directions—like gender, plurality, or royal titles—emerge naturally during training."),
        (315, 72, "Crucially, a token vector starts out context-free: the word 'mole' has the exact same initial vector whether the sentence refers to an animal, chemistry, or a spy. The network must refine vectors using surrounding tokens."),
        (387, 78, "The sequence of vectors passes through alternating Attention blocks and Multi-Layer Perceptron blocks. Think of Attention as letting vectors communicate with one another to pass context."),
        (465, 84, "For example, adjectives like 'fluffy' and 'blue' update the vector for 'creature' through the attention mechanism, shifting its coordinates in 12,288-dimensional space toward a more specific concept."),
        (549, 88, "Meanwhile, the Multi-Layer Perceptron block does not mix tokens together. Instead, it processes each token vector in parallel, acting almost like asking a long series of learned factual questions."),
        (637, 82, "Every operation in deep learning ultimately comes down to giant matrix multiplications interleaved with simple non-linearities. In GPT-3, those weight matrices contain roughly 175 billion tunable parameters."),
        (719, 86, "Distinguishing weights from data is vital: the weights are the learned brains of the model fixed after training, while activations are fleeting vectors computed for the specific prompt you just typed."),
        (805, 90, "GPT-3 has a context size of 2,048 tokens, forming a 12,288 by 2,048 array flowing through 96 repeated layers of attention and MLP transformations."),
        (895, 92, "By the final layer, the very last vector in the sequence has absorbed relevant context from the entire preceding passage and is used to predict the single next token."),
        (987, 88, "An unembedding matrix multiplies that final vector to produce one raw score—called a logit—for every single token in the 50,257-token vocabulary."),
        (1075, 94, "To convert arbitrary real-numbered logits into valid probabilities between zero and one that sum to one, the model applies the softmax function using exponentials."),
        (1169, 95, "Softmax includes an optional dial called temperature. When temperature is zero, the model greedily picks the single highest-probability token every time, making outputs deterministic but repetitive."),
        (1264, 92, "Higher temperature flattens the probability distribution so less likely tokens get sampled occasionally, adding creative variety at the risk of incoherent drift if pushed too high."),
        (1356, 94, "Autoregressive generation works in a loop: sample one token from that distribution, append it to the input sequence, and run the Transformer again to predict the next token after that."),
        (1450, 96, "Why did Transformers replace recurrent networks? Because processing all tokens simultaneously in parallel across GPUs unlocked massive training scale instead of reading word by word sequentially."),
        (1546, 88, "In the next chapter, we will zoom right inside the query, key, and value matrices of self-attention to see the exact dot-product geometry driving context updates."),
    ]
    segments = [
        {"start": float(start), "duration": float(dur), "text": text, "formatted_time": format_timestamp(start)}
        for start, dur, text in raw_segments
    ]
    transcript = {
        "segments": segments,
        "language": "English",
        "language_code": "en",
        "is_generated": False,
    }
    analysis = {
        "tldr": "A geometric, ground-up explanation of how a Transformer turns raw prompt text into next-token probability distributions through embeddings, alternating Attention and MLP layers, unembedding logits, and temperature-scaled softmax.",
        "content_type": "Visual Deep Dive",
        "summary": (
            "Grant Sanderson demystifies the 'T' in GPT by tracing how an input prompt physically moves as numeric tensors "
            "through a Generative Pre-trained Transformer. Starting from sub-word tokenization and 12,288-dimensional semantic "
            "embeddings, the video contrasts the two core building blocks repeated across dozens of layers: Attention blocks "
            "(where tokens exchange context with one another) and Multi-Layer Perceptrons (where each vector is refined in "
            "parallel). Finally, it shows how the last vector is projected via an unembedding matrix into vocabulary logits and "
            "converted via temperature-adjusted softmax into a probability distribution for autoregressive text generation."
        ),
        "premise": (
            "Most explanations of large language models stop at vague metaphors like 'advanced autocomplete.' Understanding both "
            "their capabilities and limitations requires seeing the exact vector spaces, parameter matrices, and probability "
            "mechanics operating under the hood."
        ),
        "core_breakdown": (
            "Walks chronologically through the forward pass of GPT-3 (175B parameters): (1) Tokenization & initial context-free "
            "embeddings, (2) Contextualization via Attention + parallel refinement via MLPs across 96 layers, and (3) Final-token "
            "unembedding, logits, softmax temperature control, and autoregressive sampling."
        ),
        "topics": [
            "Transformer Architecture",
            "Tokenization & Sub-words",
            "High-Dimensional Embeddings",
            "Self-Attention Context Mixing",
            "Multi-Layer Perceptrons (MLP)",
            "Weights vs. Activations",
            "Unembedding & Logits",
            "Softmax & Temperature Sampling",
        ],
        "key_takeaways": [
            "Initial token embeddings encode word identity in high-dimensional space (12,288-D in GPT-3), where directions capture semantic relationships—but start completely context-free.",
            "Attention blocks are the only place where tokens directly communicate to disambiguate meaning (e.g., whether 'mole' means an animal, unit in chemistry, or undercover spy).",
            "Multi-Layer Perceptron (MLP) blocks process each token vector independently in parallel without cross-token mixing, storing the bulk of learned factual associations.",
            "Model weights (~175B numbers in GPT-3) remain static during inference, whereas activations are temporary vectors recomputed for each prompt's context window.",
            "The unembedding matrix maps the final layer's last vector to raw logits over all 50,257 vocabulary tokens, and softmax with temperature T controls determinism vs. creative diversity.",
            "Transformers superseded RNNs largely because parallel token processing maps cleanly onto modern GPU matrix hardware at massive scale.",
        ],
        "chapters": [
            {"start_time": "00:00", "title": "Deconstructing G-P-T & Architecture Goal", "summary": "Defines Generative, Pre-trained, and Transformer and frames the end-to-end data-flow walkthrough."},
            {"start_time": "02:02", "title": "Tokenization & 12,288-D Embedding Space", "summary": "Shows how text splits into tokens mapped to vectors whose directions encode semantic relationships."},
            {"start_time": "06:27", "title": "Attention vs. MLP Layer Alternation", "summary": "Explains how Attention passes context between tokens while MLPs refine individual vectors in parallel."},
            {"start_time": "10:37", "title": "175B Weights vs. Prompt Activations", "summary": "Separates static learned weight matrices from dynamic token activations inside the context window."},
            {"start_time": "16:27", "title": "Unembedding, Logits & Softmax Temperature", "summary": "Converts the final vector into vocabulary probabilities and illustrates temperature sampling."},
            {"start_time": "22:36", "title": "Autoregressive Loop & Parallel Scale", "summary": "Demonstrates repeated next-token generation and why GPU parallelism made Transformers dominant."},
        ],
        "timestamps": [
            {"time": "00:28", "explanation": "Why the 2017 Transformer paper from Google is the pivotal architectural breakthrough behind modern AI."},
            {"time": "03:00", "explanation": "Visualizing GPT-3's 12,288-dimensional embedding matrix and semantic vector arithmetic."},
            {"time": "05:15", "explanation": "The 'mole' polysemy example illustrating why raw embeddings must incorporate surrounding context."},
            {"time": "06:27", "explanation": "Core mental model: Attention lets vectors talk to each other; MLPs process each vector solo."},
            {"time": "11:59", "explanation": "Crucial distinction between fixed model weights (175B parameters) and per-prompt activations."},
            {"time": "16:27", "explanation": "How the unembedding matrix projects the final token state into 50,257 vocabulary logits."},
            {"time": "19:29", "explanation": "How temperature T=0 (greedy) vs. higher temperature reshapes the softmax distribution."},
            {"time": "24:10", "explanation": "Why parallel sequence processing gave Transformers a decisive training-speed edge over RNNs."},
        ],
        "action_items": [
            "Keep a clear separation between learned parameters (weights) and runtime prompt representations (activations) when reasoning about LLM memory and context limits.",
            "Lower generation temperature toward 0 for deterministic analytical tasks, and raise it moderately only when lexical variety is desired.",
            "Remember that prompt wording shapes the final token's vector coordinates—clearer preceding context directly sharpens next-token logits.",
            "Proceed to Chapter 6 (Self-Attention internals) to study Query, Key, and Value dot-product mechanics in detail.",
        ],
        "audience": "Software engineers, students, technical product builders, and curious learners who want a genuine mathematical and geometric intuition for how LLMs work without drowning in raw code.",
        "terminology": [
            {"term": "Token", "explanation": "A word fragment, word, or symbol serving as the atomic input/output unit indexed in the model's vocabulary."},
            {"term": "Embedding Matrix", "explanation": "Learned lookup table assigning each token ID an initial high-dimensional vector whose geometry reflects meaning."},
            {"term": "Attention Block", "explanation": "Transformer sub-layer allowing token vectors in the context window to exchange information and update meaning in context."},
            {"term": "MLP (Multi-Layer Perceptron)", "explanation": "Feed-forward sub-layer applied independently to each token vector using matrix multiplies and non-linearities."},
            {"term": "Logits", "explanation": "Unnormalized real-valued scores produced by the unembedding matrix for every possible next token prior to softmax."},
            {"term": "Softmax & Temperature", "explanation": "Normalization turning logits into probabilities summing to 1, scaled by temperature T to tune randomness."},
        ],
        "conclusion": "A GPT is ultimately a deep stack of matrix multiplications that progressively refines token vectors using surrounding context until the final vector cleanly predicts a probability distribution over the next token.",
    }
    analytics = build_dashboard_analytics(metadata, transcript, analysis)
    return {
        "id": "gpt-visual-intro",
        "label": "3Blue1Brown · Visual Intro to Transformers",
        "metadata": metadata,
        "analysis": analysis,
        "analytics": analytics,
        "transcript": {
            "language": transcript["language"],
            "language_code": transcript["language_code"],
            "is_generated": transcript["is_generated"],
            "segments": segments,
        },
        "telemetry": {
            "elapsed_ms": 12,
            "cached": True,
            "sample": True,
            "llm_calls": 0,
            "youtube_api_calls": 0,
            "provider": "sample",
            "model": "precomputed-grounded-brief",
        },
    }


def _build_karpathy_sample() -> dict:
    metadata = {
        "id": "zjkBMFhNj_g",
        "title": "[1hr Talk] Intro to Large Language Models",
        "channel": "Andrej Karpathy",
        "description": (
            "General-audience 1-hour introduction to Large Language Models: what an LLM actually is (two files: parameters + run code), "
            "pre-training vs. fine-tuning into an assistant, scaling laws, tool use, multimodal systems, System 1 vs. System 2 thinking, "
            "and LLM security challenges like jailbreaks and prompt injection."
        ),
        "published_at": "2023-11-23T17:30:00Z",
        "thumbnail": "https://i.ytimg.com/vi/zjkBMFhNj_g/maxresdefault.jpg",
        "duration": "PT59M48S",
        "duration_seconds": 3588,
        "view_count": 6180000,
        "like_count": 198000,
        "comment_count": 4910,
        "metadata_source": "sample_showcase",
        "url": "https://www.youtube.com/watch?v=zjkBMFhNj_g",
    }

    raw_segments = [
        (0, 120, "Welcome everyone. Today I want to give a comprehensive, self-contained mental model of Large Language Models—stripping away hype to look at what an LLM physically is."),
        (180, 160, "At the filesystem level, an open-weights model like Llama 2 70B is literally just two files: a 140-gigabyte parameters file of float16 numbers, and a ~500-line C or Python file that runs the neural network architecture."),
        (420, 180, "Running the model needs zero internet access once compiled; all the magic and cost lived in obtaining those specific 70 billion parameter values during pre-training."),
        (720, 210, "Stage one—pre-training—compresses roughly 10 terabytes of internet text across thousands of GPUs over weeks, spending millions of dollars to train a next-word predictor—essentially a lossy zip file of the internet."),
        (1080, 200, "A raw base model only dreams internet documents; if you ask it a question, it might reply with ten more quiz questions. Turning it into a helpful assistant requires stage two: supervised fine-tuning."),
        (1410, 195, "In fine-tuning, human contractors write ~100,000 high-quality question-and-answer conversations. Training on curated dialogues is cheap and quick compared to pre-training, unlocking the assistant persona."),
        (1740, 210, "Stage three often uses comparison labels—ranking multiple model responses—via RLHF so the model aligns better with human preferences, since judging answers is much easier for humans than writing ideal ones from scratch."),
        (2070, 215, "Scaling laws show a remarkably smooth, predictable curve: next-word prediction loss improves strictly as a power law of parameter count N and dataset token count D, showing no signs of hitting a hard wall."),
        (2400, 220, "Modern LLM systems increasingly act as an 'LLM OS' orchestrating peripherals: browsing the web for fresh context, running a Python interpreter for exact math, reading local files via RAG, and generating images or audio."),
        (2760, 210, "Today's LLMs only have System 1 fast, instinctive token-by-token generation—every token takes roughly constant compute. A major research frontier is System 2 reasoning: spending variable tree-of-thought time on hard problems."),
        (3120, 220, "Finally, LLM security is a cat-and-mouse game involving jailbreaks via roleplay or Base64 encoding, indirect prompt injection hidden inside untrusted web pages or documents, and training data poisoning."),
        (3420, 168, "Treat LLMs as an emerging computing paradigm—like early operating systems—combining compressed world knowledge, natural-language interfaces, tool orchestration, and brand-new security surfaces."),
    ]
    segments = [
        {"start": float(start), "duration": float(dur), "text": text, "formatted_time": format_timestamp(start)}
        for start, dur, text in raw_segments
    ]
    transcript = {
        "segments": segments,
        "language": "English",
        "language_code": "en",
        "is_generated": False,
    }
    analysis = {
        "tldr": "Andrej Karpathy frames an LLM concretely as two artifacts (learned weight parameters + compact inference code), breaks down the 3-stage training pipeline, and maps out the emerging 'LLM OS' era of tool use, System 2 reasoning, and prompt-injection security.",
        "content_type": "Keynote Lecture",
        "summary": (
            "In this one-hour technical briefing, Andrej Karpathy demystifies Large Language Models from bare-metal files up to "
            "agentic operating systems. He explains how multi-million-dollar pre-training compresses terabytes of internet text "
            "into a 'lossy zip file' base model, and how inexpensive fine-tuning + RLHF converts that document completer into an "
            "assistant. The second half charts where LLMs are headed: scaling laws, tool-augmented 'LLM OS' architectures, "
            "System 1 vs. System 2 deliberative reasoning, and critical security vulnerabilities like indirect prompt injection."
        ),
        "premise": (
            "People interact with ChatGPT daily without knowing where knowledge comes from, why models hallucinate math, or why "
            "untrusted web pages can hijack AI assistants."
        ),
        "core_breakdown": (
            "Divided into three parts: (1) Core mechanics—two-file anatomy, pre-training compression, SFT, and RLHF; "
            "(2) Capability frontiers—scaling laws, tool use ('LLM OS'), multimodality, and System 2 thinking; "
            "(3) Security—jailbreaks, indirect prompt injection, and data poisoning."
        ),
        "topics": [
            "Two-File LLM Anatomy",
            "Pre-training vs. Fine-tuning",
            "RLHF & Alignment",
            "Neural Scaling Laws",
            "LLM Operating System (LLM OS)",
            "System 1 vs. System 2 Reasoning",
            "Prompt Injection & Jailbreaks",
        ],
        "key_takeaways": [
            "An open-weights LLM at runtime is just two files: a giant parameter tensor file (e.g., 140 GB for 70B float16) and a few hundred lines of inference code.",
            "Pre-training costs 99% of the compute to build a 'lossy zip file' of internet knowledge, whereas supervised fine-tuning (SFT) cheaply shapes conversational behavior.",
            "RLHF leverages the fact that humans can rank candidate responses far more reliably than authoring gold-standard answers from scratch.",
            "Scaling laws predict next-token accuracy strictly from parameter count (N) and training data tokens (D) before training finishes.",
            "Think of an advanced assistant as an 'LLM OS' kernel coordinating browser search, code execution, memory/RAG, and multimodal I/O.",
            "Indirect prompt injection—malicious instructions embedded in retrieved web pages, PDFs, or emails—is one of the most serious unsolved LLM security risks.",
        ],
        "chapters": [
            {"start_time": "00:00", "title": "What an LLM Physically Is (Two Files)", "summary": "Breaks Llama-2-70B down into its raw parameter file and minimal inference code."},
            {"start_time": "12:00", "title": "Stage 1: Internet Pre-training Compression", "summary": "Shows how GPU clusters compress terabytes of web text into next-word prediction weights."},
            {"start_time": "18:00", "title": "Stages 2 & 3: Fine-Tuning & RLHF", "summary": "Explains how curated Q&A datasets and preference rankings turn base models into assistants."},
            {"start_time": "34:30", "title": "Scaling Laws & The Emerging LLM OS", "summary": "Covers predictable scaling curves and tool orchestration across search, Python, and RAG."},
            {"start_time": "46:00", "title": "System 1 vs. System 2 Deliberation", "summary": "Contrasts constant-compute token instincts with future tree-of-thought reasoning."},
            {"start_time": "52:00", "title": "Security: Jailbreaks & Prompt Injection", "summary": "Catalogs roleplay/encoding bypasses, indirect prompt injection, and data poisoning."},
        ],
        "timestamps": [
            {"time": "03:00", "explanation": "Llama 2 70B explained as two files: 140 GB of float16 weights + ~500 lines of C inference code."},
            {"time": "12:00", "explanation": "Why pre-training should be understood as 'lossy compression' of ~10 TB of internet text."},
            {"time": "23:30", "explanation": "How ~100K human-written conversations convert a document completer into a helpful assistant."},
            {"time": "34:30", "explanation": "Scaling laws: model loss is a smooth, predictable function of parameters (N) and dataset size (D)."},
            {"time": "40:00", "explanation": "The 'LLM OS' diagram mapping CPU, RAM (context window), disk (RAG), and tool peripherals."},
            {"time": "46:00", "explanation": "System 1 vs. System 2: why LLMs currently spend identical compute per token regardless of difficulty."},
            {"time": "52:00", "explanation": "Real-world demonstrations of Base64 jailbreaks and indirect prompt injection attacks."},
        ],
        "action_items": [
            "Offload exact arithmetic, data analysis, and fresh facts to external tools (code interpreter / search / RAG) instead of relying on parametric memory.",
            "Treat all external documents, transcripts, emails, and web pages fed into an LLM context window as untrusted input to defend against prompt injection.",
            "Prefer iterative fine-tuning and retrieval updates for recent domain facts rather than expecting expensive base pre-training to stay current.",
        ],
        "audience": "Product leaders, engineers, researchers, and technical executives looking for an authoritative, hype-free mental model of modern LLM capabilities, economics, and security.",
        "terminology": [
            {"term": "Base Model", "explanation": "Raw pre-trained next-token predictor trained on internet text before instruction fine-tuning."},
            {"term": "Supervised Fine-Tuning (SFT)", "explanation": "Second training stage swapping massive web corpora for smaller, curated human assistant dialogues."},
            {"term": "RLHF", "explanation": "Reinforcement Learning from Human Feedback—aligning outputs using human rankings of candidate responses."},
            {"term": "Scaling Laws", "explanation": "Empirical power-law relationship linking compute, model size, and dataset tokens to validation loss."},
            {"term": "LLM OS", "explanation": "Conceptual architecture where the LLM acts as a central kernel coordinating memory (context/RAG) and external tools."},
            {"term": "Prompt Injection", "explanation": "Security exploit where untrusted data ingested into context hijacks the model's instructions."},
        ],
        "conclusion": "LLMs are best understood not as chatbots, but as the kernel of a new computing paradigm uniting compressed human knowledge, tool execution, and natural-language orchestration.",
    }
    analytics = build_dashboard_analytics(metadata, transcript, analysis)
    return {
        "id": "karpathy-llm-intro",
        "label": "Andrej Karpathy · Intro to Large Language Models",
        "metadata": metadata,
        "analysis": analysis,
        "analytics": analytics,
        "transcript": {
            "language": transcript["language"],
            "language_code": transcript["language_code"],
            "is_generated": transcript["is_generated"],
            "segments": segments,
        },
        "telemetry": {
            "elapsed_ms": 14,
            "cached": True,
            "sample": True,
            "llm_calls": 0,
            "youtube_api_calls": 0,
            "provider": "sample",
            "model": "precomputed-grounded-brief",
        },
    }


SAMPLES: dict[str, dict] = {
    "gpt-visual-intro": _build_gpt_sample(),
    "karpathy-llm-intro": _build_karpathy_sample(),
}
