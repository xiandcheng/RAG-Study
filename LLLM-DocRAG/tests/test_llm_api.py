import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

messages = [
    {"role": "system", "content": "你是一名专业的人工智能助手。"},
    {"role": "user", "content": "请简单介绍什么是 LoRA。"}
]

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=messages
)

print(response.choices[0].message.content)
print("-"*30)
print(response)

# ChatCompletion(
#     id='2420d7b3-ec83-4395-9792-eb546702c99a',
#     choices=[
#         Choice(
#             finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(
#                 content="LoRA（Low-Rank Adaptation，低秩适配）是一种**参数高效微调方法**，主要用于大语言模型、扩散模型等大模型的定制化训练。\n\n它的核心思想是：**冻结预训练模型的原有权重，只在部分层中插入少量可训练的低秩矩阵**。例如原来权重为 \\(W\\)，LoRA 不直接更新 \\(W\\)，而是学习一个增量：\n\\[\nW' = W + \\Delta W = W + BA\n\\]\n其中 \\(A\\)、\\(B\\) 是两个小矩阵，秩 \\(r\\) 远小于原权重维度，因此可训练参数量大幅减少。\n\nLoRA 的优点是：\n- 显存和计算开销小，普通显卡也能微调大模型；\n- 训练出的适配器文件很小，便于存储和分享；\n- 可以为不同任务训练不同 LoRA，按需加载；\n- 推理时可以把 LoRA 权重合并回原模型，不增加额外延迟。\n\n简单说，LoRA 就是**用很小的“外挂补丁”来调整大模型行为，而不改动或重训整个模型**。",
#                 refusal=None,
#                 role='assistant',
#                 annotations=None,
#                 audio=None,
#                 function_call=None,
#                 tool_calls=None,
#                 reasoning_content='我们需要回答用户中文问题：“你是一名专业的人工智能助手。请简单介绍什么是 LoRA。”需要简单介绍 LoRA。我们要用中文回答。需要专业、简洁。LoRA 是 Low-Rank Adaptation，低秩适配，一种参数高效微调方法。用于大模型微调，冻结预训练权重，在 Transformer  层中注入可训练低秩矩阵，通常对 Attention 的 Q/K/V/O 或线性层加 A、B 矩阵，B*A 低秩，前向 h = W0 x + ΔW x = W0 x + BA x，缩放 α/r。训练只更新 A/B，大幅减少可训练参数和显存，保持原模型性能，便于多任务切换，推理时可合并回原权重。常用于 Stable Diffusion、LLM 微调。也可以提优点与局限。用户要求“简单介绍”，所 以不要过长。可能 2-3 段。确保准确。LoRA: Low-Rank Adaptation of Large Language Models, Microsoft 2021. 低秩假设：适配过程中权重变化具有低内在秩。训练：初始化 A 高斯，B 零，ΔW=BA，rank r << d。推理无额外延迟如果合并。也可与 QLoRA 等结合。用通俗语言。最后总结。注意“你是一名专业的人工智能助手”只是角色。我 们应该直接回答。可以包括公式。简单介绍即可。不超过 300 字？ Desired oververbosity 5. 可以稍微详细。\n\n需要确保中文术语：低秩适配（Low-Rank Adaptation，LoRA）。冻结预训练模型权重，插入低秩可训练矩阵，减少参数量。训练目标只更新这些矩阵。可合并。适用：大语言模型、扩散模型微调。优点：省显存、省计算、存储小、可插拔。局限：效果取决于任务/秩，可能不如全量微调，推理合并后无额外延迟但多适配器切换需加载。\n\n用简洁格式。可以写标题。既然问“简单介绍”，直接开始。'
#             )
#         )
#     ],
#     created=1791793293,
#     model='deepseek-flash',
#     object='chat.completion',
#     metadata=None,
#     moderation=None,
#     service_tier=None,
#     system_fingerprint='aeb56401ca74e127821c4f9126dcb669',
#     usage=CompletionUsage(
#         completion_tokens=668,
#         prompt_tokens=44,
#         total_tokens=712,
#         completion_tokens_details=CompletionTokensDetails(
#             accepted_prediction_tokens=None,
#             audio_tokens=None,
#             reasoning_tokens=432,
#             rejected_prediction_tokens=None,
#             text_tokens=None
#         ),
#         prompt_tokens_details=PromptTokensDetails(
#             audio_tokens=None,
#             cache_write_tokens=None,
#             cached_tokens=0,
#             image_tokens=None,
#             text_tokens=None
#         ),
#         prompt_cache_hit_tokens=0,
#         prompt_cache_miss_tokens=44
#     )
# )
