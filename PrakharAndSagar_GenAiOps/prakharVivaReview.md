# PS1 : Viva Review
Points I got stuck in: Attention, Augmentation, Feed Forward Layers

## RAG (Retrieval Augmented Generation)
It’s an architecture to improve the performance of llms, and reduce hallucinations, by using external resources, including pdfs, web documents, etc. In retrieval, (taking the rag assignment using the pdf as an example), we basically split the pdf into chunks, and also add an overlap, so that we do not lose context. Then, the retriever algorithm (example: bm25), ranks the top k most relevant chunks. In augmentation, we basically add the user prompt to the context, and store the resultant as the final prompt. And then, in generation, we use an llm, to generate a response based on the augmented final prompt.

## LLM
It’s basically a neural network (transformer), that predicts the next word, based on the prompt, and the output it has predicted so far. Attention in a very simple sense, just figures out the amount of importance it should give each word in the input. Like, each token assigns a number to every other token, with how important they are to it. Feed forward networks are basically a mix of 2 linear transformations (based on the weights determined while training), and a non linear function like relu sandwiched between them.
