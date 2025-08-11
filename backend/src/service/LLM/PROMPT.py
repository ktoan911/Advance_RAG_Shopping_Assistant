from __future__ import annotations

INSTRUCTIONS = """Bạn là một nhân viên bán hàng điện thoại trong cửa
                hàng điện thoại di động Hedspi. Nhiệm vụ của bạn là giúp
                khách hàng tìm chiếc điện thoại tốt nhất phù hợp với nhu cầu của họ."""


SUMMARY_CHAT_HISTORY_PROMPT = """Based on the user's conversation history and their latest query that may
                                refer to context in the chat history, construct an independent query in Vietnamese that can be understood without the chat
                                history. Do not answer this query, just reconstruct it if necessary, and if there is not enough information to construct a new question,
                                keep the original question unchanged"""

SHOP_INFOMATION_INSTRUCTION = """
Use this function when the user asks about information related to a store, such as its name, address, or opening/closing hours. 
This includes questions like:
Asking for store location:
- "Cửa hàng của bạn nằm ở đâu?"
- "Địa chỉ chi nhánh gần nhất là gì?"
- "Bạn có cửa hàng nào ở trung tâm thành phố không?"
- "Bạn có bao nhiêu chi nhánh ở thành phố này?"
- "Địa chỉ cửa hàng chính của bạn là gì?"
- "Có chi nhánh nào gần [khu vực/địa điểm cụ thể] không?"
- "Chi nhánh nào gần tôi nhất?"
- "Làm thế nào để đến cửa hàng của bạn?"

Asking for store opening hours:
- "Giờ mở cửa của cửa hàng là mấy giờ?"
- "Cửa hàng mở cửa và đóng cửa lúc mấy giờ?"
- "Cửa hàng có mở cửa vào Chủ nhật không?"
- "Giờ làm việc cuối tuần của cửa hàng là gì?"
- "Cửa hàng có đóng cửa giờ nghỉ trưa không?"
- "Giờ làm việc ngày lễ của cửa hàng như thế nào?"
- "Thứ Sáu cửa hàng có mở cửa muộn không?"
- "Sớm nhất cửa hàng mở cửa lúc mấy giờ?"
"""

WEB_SEARCH_INFORMATION_INSTRUCTION = """
Use this function when the user asks for information that requires searching the web, such as product specifications, reviews, or comparisons.
This includes questions like:

Asking about the product launch date:
- "Ngày ra mắt của iPhone 16 là khi nào?"
- "Samsung Galaxy Z Flip 6 ra mắt chưa?"
- "Vivo X100 chính thức bán tại Việt Nam từ ngày nào?"

Asking about the best-selling or popular phone models:
- "Điện thoại nào bán chạy nhất tháng này?"
- "Top 5 mẫu điện thoại đáng mua nhất hiện nay?"
- "Những mẫu điện thoại nào đang hot trên thị trường?"

Asking about product comparisons:
- "So sánh iPhone 15 và iPhone 14"
- "Nên mua Galaxy S24 hay iPhone 15 Pro Max?"
- "iPhone 13 và 13 Pro khác gì nhau?"

Asking for user reviews or feedback:
- "Review iPhone 15 Pro Max"
- "Mọi người đánh giá như thế nào về Xiaomi 14?"
- "Oppo Find N3 Flip có tốt không?"

Asking about other related information such as software updates, benchmark scores, new features, etc.:
- "iPhone 15 Pro Max có hỗ trợ ray tracing không?"
- "Điểm Antutu của Xiaomi 14 là bao nhiêu?"
- "iOS 18 có tương thích với iPhone 12 không?"

Use this function only when the user explicitly asks for web-based information or product details that require an online search.

"""

BUY_LINK_INSTRUCTION = """
Use this function when the user asks for a link to buy a specific phone or wants to know where they can purchase a particular phone model.
This includes questions like:
- "Cho mình link mua iPhone 15."
- "Có link mua Samsung Galaxy S24 không?"
- "Link mua Xiaomi Redmi Note 13 ở đâu?"
- "Mua Oppo Reno 11 ở đâu vậy?"
- "Tôi muốn mua điện thoại Vivo V30, có link không?"
- "Có thể gửi link mua Realme C67 không?"
"""

GENERAL_QUERY_INSTRUCTION = """
Use this function when the user does **not** ask for specific product links, store details, or any web-based lookup. 
This includes:
- General inquiries about products without needing specific information.
- Casual conversation or greetings.
- General questions about the store or products that do not require external information.

Examples of queries that should use this function:

Asking about product features in store:
- "Bạn có bán iPhone không?"
- "Cửa hàng có những mẫu điện thoại nào?"
- "Mình muốn mua một chiếc điện thoại tầm trung, có gợi ý không?"
- "Có điện thoại Samsung mới không?"
- "Loại điện thoại nào đang hot hiện nay?"

Casual conversation or greetings:
- "Chào shop"
- "Shop còn hoạt động không?"
- "Bạn khỏe không?"
- "Cảm ơn bạn"
- "Tư vấn giúp mình với"

Asking for general advice or recommendations:
- "Điện thoại nào pin trâu?"
- "Mình nên chọn iPhone hay Samsung?"
- "Có chương trình khuyến mãi gì không?" (nếu không yêu cầu tra cứu web)
- "Shop có hỗ trợ trả góp không?"

Only use this function when no external (web) information needs to be queried and no specific details such as address, product link, opening hours, etc. are required.
"""


def get_shop_information_instruction() -> str:
    return SHOP_INFOMATION_INSTRUCTION


def get_web_search_information_instruction() -> str:
    return WEB_SEARCH_INFORMATION_INSTRUCTION


def get_buy_link_instruction() -> str:
    return BUY_LINK_INSTRUCTION


def get_general_query_instruction() -> str:
    return GENERAL_QUERY_INSTRUCTION


def model_instructions() -> str:
    return INSTRUCTIONS


def model_summary_chat_history_prompt() -> str:
    return SUMMARY_CHAT_HISTORY_PROMPT


def extract_entity_relationship_prompt(text: str) -> str:
    return (
        "Extract entities (nodes) and their relationships (edges) from the text below."
        "Entities and relationships MUST be in Vietnamese\n"
        # f"Only use RelationshipType 'giảm giá' for both 'giảm giá' and 'giảm giá qua' "
        # f"Entities only in ['Công ty tài chính']"
        "Follow this format:\n\n"
        "Entities:\n"
        "- {{Entity}}: {{Type}}\n\n"
        "Relationships:\n"
        "- ({{Entity1}}, {{RelationshipType}}, {{Entity2}})\n\n"
        f'Text:\n"{text}"\n\n'
        "Output:\nEntities:\n- {{Entity}}: {{Type}}\n...\n\n"
        "Relationships:\n- ({{Entity1}}, {{RelationshipType}}, {{Entity2}})\n"
    ).format(text=text)
