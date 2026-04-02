# TaxStreem - Intelligent Transaction Grouper

## Approach

I chose Option A, LLM-Powered Approach.

The assessment specified a CPU-only solution, which immediately made Option B 
and C is less practical, embedding models like sentence-transformers are 
computationally heavy and significantly slower without GPU acceleration. 
For a small dataset of 16 transactions, the overhead of running embeddings 
locally would not be justified.

The core problem here is semantic similarity, understanding that "Uber trip" 
and "uber ride lagos" means the same thing, despite looking completely different 
as strings. This is exactly what LLMs are built for. Python then handles all 
the post-processing logic, parsing, validation, and summary calculation, 
keeping the LLM responsible only for what it does best.

I used Groq with the `llama-3.3-70b-versatile` model. I initially evaluated 
Gemini 2.0 Flash but encountered a consistent rate limiting on the free tier due 
to regional restrictions in Nigeria. Groq provides a free, reliable API with 
no such restrictions. 

## Prompt Design

The core strategy was a clear division of responsibility: let the LLM 
understand meaning, let Python handle counting, calculating, and validating.

The first prompt asked the LLM to do too much: group transactions, calculate 
the summary, and populate the ungrouped list. This caused hallucinations: 
transactions appearing in both a group and the ungrouped list, with summary 
counts that didn't match the actual output.

How it was fixed:
Before: LLM groups + calculates summary + populates ungrouped
After: LLM only groups and Python calculates everything else

I also added a markdown stripper in Python because the LLM occasionally 
wraps its response in ```json code fences. I handled it in code rather than 
adding more instructions to the prompt.


## Assumptions

Input is always a clean list of strings, no nulls, numbers, or nested objects
Transactions are in English or use brand names recognisable to a globally trained LLM
Every transaction belongs to at least one meaningful category; nothing is truly ungroupable.

The LLM has sufficient knowledge of Nigerian companies like Paystack, Flutterwave, MTN, and Airtel from its training data. This holds for well-known brands, but may fail for unknown local businesses

## Trade-offs

What the solution gets wrong:
Broken JSON: If the LLM returns malformed JSON, the solution crashes with a JSONDecodeError. It fails loudly and does not recover.

Scale: The solution sends all transactions in a single prompt. This works for small datasets, but would fail for large inputs because LLMs have a context window limit. 

Unknown local businesses: The LLM groups well-known brands correctly because they appear in its training data. An unknown local Nigerian business, like "Iya Basira Shop," would be guessed at rather than classified confidently. A domain-specific merchant database would fix this.
No retry logic: If Groq is unavailable, the solution crashes immediately with no fallback or retry.

Non-determinism: LLMs are not deterministic; running the same input twice may produce slightly different group labels or confidence levels. 

This makes automated testing of the full pipeline difficult, which is why the unit tests focus on the parsing and validation logic rather than the LLM output itself.

## Evaluation Strategy
The system was designed so that evaluation can be done practically and efficiently on the immediate output:

Automated Schema Validation: pytest unit tests ensure the output always strictly conforms to the JSON schema, catches missing transactions, and prevents duplicate groupings. This mathematically guarantees the integrity of the output.

Confidence-Based Spot Checking: The prompt forces the LLM to assign a confidence score ("high", "medium", "low") to each group. To evaluate the model's semantic accuracy, instead of reading every single line, a reviewer can just spot-check the 'low' confidence groups and whatever didn't get grouped.

Summary Metrics: The Python script programmatically calculates a summary of total_groups and ungrouped_count. A high ungrouped count immediately acts as a signal that the prompt or model might need tuning for that specific batch of data.


## Cost Estimation
Using the Groq llama-3.3-70b-versatile pricing (approximate):
Input tokens: ~$0.59 per 1M tokens.
Output tokens: ~$0.79 per 1M tokens.

For 1,000 transactions:
Prompt + Input Context ≈ 15,000 tokens ($0.0088)
Generated JSON Output ≈ 20,000 tokens ($0.0158)
Total Estimated Cost: ~$0.024 per 1,000 transactions.

### Insight
This translates to:
~$14 per 1 million transactions
This indicates that the approach is cost-effective for large-scale transaction processing.


## How to Run

### Prerequisites
Python 3.10+
Groq API key

### Clone the Repository
git clone <repo-url>
cd ai_ml_task

### Create Virtual Environment 
python -m venv .venv

#### Activate it
Windows:
.venv\Scripts\activate
Mac/Linux
source .venv/bin/activate

### Install Dependencies
pip install -r requirements.txt

### Set Environment Variables
Create a .env file in the root directory:
GROQ_API_KEY=your_actual_api_key_here

### Run the Application
python -m src.main 

### Run Tests
python -m pytest tests/test_grouper.py -v









