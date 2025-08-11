from __future__ import annotations

import json
import os

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

embedding_model = SentenceTransformer('keepitreal/vietnamese-sbert')


class Embedding:
    def __init__(
        self,
        embedding_model: str,
    ):
        self.model = SentenceTransformer(embedding_model)

    def get_embedding(self, doc: list[str]):

        # Check if doc is empty or not a list
        if not doc or not isinstance(doc, list):
            print('Input is not a valid list of strings.')
            return []

        embedding = [
            self.model.encode(
                text.replace('###', '').replace('\n', '').replace('<br>', ''),
            ).tolist()
            for text in doc if text.strip()
        ]

        return embedding

    def encode(self, docs: list[str]):
        try:
            embeddings = self.get_embedding(
                doc=docs,
            )
            return embeddings
        except Exception as e:
            raise ValueError(
                f'Failed to get embeddings. Error details: {e}',
            ) from e


class Route():
    def __init__(
        self,
        name: str = None,
        samples: list = [],
    ):

        self.name = name
        self.samples = samples


class SemanticRouter():
    def __init__(self, embedding):
        self.embedding = embedding

    def get_embedding_route(self, routes):
        routesEmbedding = {}

        for route in routes:
            routesEmbedding[
                route.name
            ] = self.embedding.encode(route.samples)
        return routesEmbedding

    def get_routes(self):
        return self.routes

    def guide(self, query, routesEmbeddings):
        queryEmbedding = self.embedding.encode([query])
        scores = []

        # Calculate the cosine similarity of the query embedding with the sample embeddings of the router.
        for route_name in routesEmbeddings:
            score = np.mean(
                cosine_similarity(
                    queryEmbedding, routesEmbeddings[route_name],
                ).flatten(),
            )
            scores.append((score, route_name))

        scores.sort(reverse=True)
        return scores[0]


class ChitchatProdcutsSentimentRoute:
    def get_semanticRouter(self):
        # @title Query samples
        productRoute = Route(
            name='products',
            samples=[
                'Bạn có sẵn iPhone mới nhất không?',
                'Giá của Samsung Galaxy S21 là bao nhiêu?',
                'OnePlus 9 Pro có màu xanh không?',
                'Thông số kỹ thuật của Google Pixel 6 là gì?',
                'Huawei P50 Pro có sẵn ở cửa hàng của bạn không?',
                'iPhone 13 có những màu gì?',
                'Có giảm giá nào cho Samsung Galaxy Note 20 không?',
                'Sony Xperia 1 III có sẵn không?',
                'Cửa hàng của bạn có Google Pixel mới nhất không?',
                'Có chương trình khuyến mãi nào cho OnePlus Nord không?',
                'Dung lượng lưu trữ của Samsung Galaxy S21 là bao nhiêu?',
                'iPhone SE 2022 có sẵn không?',
                'Sự khác biệt về giá giữa iPhone 12 và 13 là gì?',
                'Motorola Edge 20 có sẵn không?',
                'Google Pixel 6 Pro có sẵn ở cửa hàng của bạn không?',
                'Bạn có bán Xiaomi Mi 11 không?',
                'Có chương trình ưu đãi nào cho Samsung Galaxy Z Fold 3 không?',
                'Oppo Find X3 Pro có sẵn không?',
                'Các tính năng của iPhone 13 Pro là gì?',
                'LG Wing có sẵn không?',
                'Nokia 8.3 5G có sẵn không?',
                'Asus ROG Phone 5 có sẵn không?',
                'Bạn có Realme GT không?',
                'Vivo X60 Pro có sẵn không?',
                'Bạn có Honor 50 không?',
                'Tuổi thọ pin của Samsung Galaxy A52 là bao nhiêu?',
                'ZTE Axon 30 có sẵn không?',
                'Bạn có BlackBerry KEY2 không?',
                'Kích thước màn hình của iPhone 13 Mini là bao nhiêu?',
                'Bạn có TCL 20 Pro 5G không?',
                'Nokia XR20 có sẵn ở cửa hàng của bạn không?',
                'Giá của Samsung Galaxy S20 FE là bao nhiêu?',
                'Bạn có iPhone 12 Pro Max không?',
                'Redmi Note 10 Pro có sẵn không?',
                'Sự khác biệt giữa iPhone 12 và iPhone 13 là gì?',
                'Bạn có Sony Xperia 5 II không?',
                'Thời gian bảo hành của Samsung Galaxy S21 là bao lâu?',
                'Google Pixel 5a có sẵn không?',
                'Bạn có OnePlus 8T không?',
                'Giá của iPhone 13 Pro Max là bao nhiêu?',
                'Samsung Galaxy Z Flip 3 có sẵn không?',
                'Thông số kỹ thuật của Oppo Reno6 Pro là gì?',
                'Bạn có Vivo V21 không?',
                'Motorola Moto G100 có sẵn không?',
                'Bạn có Huawei Mate 40 Pro không?',
                'Realme 8 Pro có sẵn ở cửa hàng của bạn không?',
                'Asus Zenfone 8 có sẵn không?',
                'LG Velvet có sẵn không?',
                'Dung lượng lưu trữ của iPhone 12 là bao nhiêu?',
                'Bạn có Honor Magic 3 không?',
                'Xiaomi Mi 11 Ultra có sẵn không?',
                'Có chương trình khuyến mãi nào cho iPhone 12 không?',
                'Dung lượng pin của Samsung Galaxy Note 20 là bao nhiêu?',
                'Sony Xperia 10 III có sẵn không?',
                'Thông số kỹ thuật của Xiaomi Mi 10T Pro là gì?',
                'Bạn có bán Huawei Nova 7i không?',
                'Oppo Reno5 có sẵn ở cửa hàng của bạn không?',
                'Giá của Samsung Galaxy A72 là bao nhiêu?',
                'Bạn có Google Pixel 4a không?',
                'OnePlus 8 có những màu gì?',
                'Thông tin về bảo hành của iPhone 11 là gì?',
                'Redmi K40 Pro có sẵn không?',
                'Nokia 5.4 có sẵn ở cửa hàng của bạn không?',
                'Asus ROG Phone 3 có sẵn không?',
                'Thông số kỹ thuật của Samsung Galaxy A32 là gì?',
                'Bạn có Sony Xperia L4 không?',
                'Vivo Y20s có sẵn không?',
                'Giá của Huawei P40 là bao nhiêu?',
                'Bạn có iPhone XR không?',
                'Oppo A93 có sẵn ở cửa hàng của bạn không?',
                'Thông tin về bảo hành của Google Pixel 3 là gì?',
                'Realme 7 Pro có sẵn không?',
                'Bạn có bán Xiaomi Poco X3 không?',
                'OnePlus Nord N10 có sẵn không?',
                'Thông số kỹ thuật của iPhone 11 Pro Max là gì?',
                'Bạn có Sony Xperia 1 II không?',
                'Huawei Y7a có sẵn ở cửa hàng của bạn không?',
                'Giá của Samsung Galaxy M51 là bao nhiêu?',
                'Oppo A73 có sẵn không?',
                'Thông tin về bảo hành của iPhone 8 là gì?',
                'Vivo V20 có sẵn không?',
                'Asus Zenfone 7 Pro có sẵn không?',
                'Thông số kỹ thuật của Nokia 3.4 là gì?',
                'Bạn có bán OnePlus 7T không?',
                'Samsung Galaxy A52s có sẵn không?',
                'Thông tin về bảo hành của Google Pixel 2 là gì?',
                'Realme C15 có sẵn ở cửa hàng của bạn không?',
                'Giá của Xiaomi Redmi 9 là bao nhiêu?',
                'Bạn có iPhone 7 Plus không?',
                'Thông số kỹ thuật của Oppo Find X2 là gì?',
                'Sony Xperia 5 có sẵn không?',
                'Huawei P30 Lite có sẵn không?',
                'Thông tin về bảo hành của Samsung Galaxy A21s là gì?',
                'Vivo Y50 có sẵn không?',
                'Asus ROG Phone 2 có sẵn ở cửa hàng của bạn không?',
                'Thông số kỹ thuật của iPhone SE 2020 là gì?',
                'Bạn có bán OnePlus 6T không?',
                'Samsung Galaxy Note 10 có sẵn không?',
                'Giá của Xiaomi Mi 9 là bao nhiêu?',
                'Thông tin về bảo hành của Oppo A52 là gì?',
                'Realme X50 Pro có sẵn không?',
                'Bạn có Nokia 6.2 không?',
                'Sony Xperia L3 có sẵn không?',
                'Huawei Mate 30 Pro có sẵn ở cửa hàng của bạn không?',
                'Thông số kỹ thuật của Samsung Galaxy S10 là gì?',
                'Bạn có bán Vivo V19 không?',
                'OnePlus Nord N100 có sẵn không?',
                'Thông tin về bảo hành của iPhone XS là gì?',
                'Oppo Reno4 có sẵn không?',
                'Giá của Xiaomi Redmi Note 9 là bao nhiêu?',
                'Thông số kỹ thuật của Nokia 2.4 là gì?',
                'Bạn có Sony Xperia 10 II không?',
                'Samsung Galaxy M31 có sẵn ở cửa hàng của bạn không?',
                'Thông tin về bảo hành của Huawei Y6p là gì?',
                'Vivo Y12 có sẵn không?',
                'Giá của OnePlus 7 Pro là bao nhiêu?',
                'Bạn có bán Oppo Find X2 Pro không?',
                'Thông số kỹ thuật của iPhone 6s là gì?',
                'Sony Xperia 8 có sẵn không?',
                'Samsung Galaxy A71 có sẵn không?',
                'Thông tin về bảo hành của Nokia 1.3 là gì?',
                'Realme 6 có sẵn ở cửa hàng của bạn không?',
                'Huawei P40 Pro có sẵn không?',
                'Thông số kỹ thuật của Vivo V17 Pro là gì?',
                'Bạn có bán Xiaomi Mi 8 không?',
                'OnePlus 6 có sẵn không?',
                'Giá của Oppo Reno3 là bao nhiêu?',
                'Thông tin về bảo hành của Samsung Galaxy A11 là gì?',
                'Vivo Y30 có sẵn không?',
                'Giá của Huawei Nova 5T là bao nhiêu?',
                'Bạn có bán Nokia 7.2 không?',
                'Thông số kỹ thuật của iPhone 7 là gì?',
                'Sony Xperia 1 có sẵn không?',
                'Samsung Galaxy S20 có sẵn ở cửa hàng của bạn không?',
                'Thông tin về bảo hành của Xiaomi Mi A3 là gì?',
                'Oppo A53 có sẵn không?',
                'Giá của Vivo V15 là bao nhiêu?',
                'Bạn có bán Huawei Y9a không?',
                'Thông số kỹ thuật của Nokia 4.2 là gì?',
                'Sony Xperia 5 III có sẵn không?',
                'Samsung Galaxy A12 có sẵn không?',
                'Thông tin về bảo hành của Realme 5i là gì?',
                'Vivo Y11 có sẵn không?',
                'Giá của OnePlus 5T là bao nhiêu?',
                'Bạn có bán Oppo F17 không?',
                'Thông số kỹ thuật của iPhone 6 là gì?',
            ],
        )

        # Chitchat query samples
        chitchatRoute = Route(
            name='chitchat',
            samples=[
                'Thời tiết hôm nay như thế nào?',
                'Ngoài trời nóng bao nhiêu?',
                'Ngày mai có mưa không?',
                'Nhiệt độ hiện tại là bao nhiêu?',
                'Bạn có thể cho tôi biết điều kiện thời tiết hiện tại không?',
                'Cuối tuần này có nắng không?',
                'Nhiệt độ hôm qua là bao nhiêu?',
                'Đêm nay trời sẽ lạnh đến mức nào?',
                'Ai là tổng thống đầu tiên của Hoa Kỳ?',
                'Chiến tranh thế giới thứ hai kết thúc vào năm nào?',
                'Bạn có thể kể cho tôi về lịch sử của internet không?',
                'Tháp Eiffel được xây dựng vào năm nào?',
                'Ai đã phát minh ra điện thoại?',
                'Tên của bạn là gì?',
                'Bạn có tên không?',
                'Tôi nên gọi bạn là gì?',
                'Ai đã tạo ra bạn?',
                'Bạn bao nhiêu tuổi?',
                'Bạn có thể kể cho tôi một sự thật thú vị không?',
                'Bạn có biết bất kỳ câu đố thú vị nào không?',
                'Màu sắc yêu thích của bạn là gì?',
                'Bộ phim yêu thích của bạn là gì?',
                'Bạn có sở thích nào không?',
                'Ý nghĩa của cuộc sống là gì?',
                'Bạn có thể kể cho tôi một câu chuyện cười không?',
                'Thủ đô của Pháp là gì?',
                'Dân số thế giới là bao nhiêu?',
                'Có bao nhiêu châu lục?',
                "Ai đã viết 'Giết con chim nhại'?",
                'Bạn có thể cho tôi một câu nói của Albert Einstein không?',
                'Bạn có thể nói cho tôi biết thời gian hiện tại không?',
                'Mặt trăng có xa Trái Đất không?',
                'Biển Đông có bao nhiêu hòn đảo?',
                'Khi nào là lễ Giáng Sinh?',
                'Tại sao bầu trời có màu xanh?',
                'Ai là người giàu nhất thế giới?',
                'Nước nào lớn nhất trên thế giới?',
                'Địa chỉ của Nhà Trắng là gì?',
                'Bạn có biết đọc sách nào hay không?',
                'Ai là cha đẻ của máy tính?',
                'Vịnh Hạ Long thuộc tỉnh nào?',
                'Tại sao lá cây có màu xanh?',
                'Bộ phim nào đoạt giải Oscar gần đây nhất?',
                'Nhà vật lý học nổi tiếng nhất là ai?',
                'Chúng ta có bao nhiêu bộ phận cơ thể?',
                'Cá mập lớn nhất trên thế giới là gì?',
                'Thế giới này có bao nhiêu quốc gia?',
                'Nhân vật lịch sử nào bạn ngưỡng mộ nhất?',
                'Bạn có biết bài hát nào hay không?',
                'Lớp học đông nhất bạn từng biết có bao nhiêu học sinh?',
                'Tại sao nước biển có vị mặn?',
                'Ngày Tết Nguyên Đán năm nay là khi nào?',
                'Làm sao để nấu món phở ngon?',
                'Thành phố nào lớn nhất ở Việt Nam?',
                'Sự kiện lịch sử nào quan trọng nhất trong thế kỷ 20?',
                'Múi giờ của Việt Nam là gì?',
                'Người phát minh ra bóng đèn là ai?',
                'Châu Âu có bao nhiêu quốc gia?',
                'Sông dài nhất thế giới là gì?',
                'Tại sao loài người lại phát minh ra lửa?',
                'Bộ phim hoạt hình yêu thích của bạn là gì?',
                'Bạn có thể giúp tôi tìm hiểu về động vật không?',
                'Công nghệ nào đang thay đổi thế giới?',
                'Làm sao để học ngoại ngữ nhanh chóng?',
                'Thành phố nào là thủ đô của Nhật Bản?',
                'Bộ phim hoạt hình nào nổi tiếng nhất?',
                'Bạn có biết công thức làm bánh mì không?',
                'Làm sao để giữ gìn sức khỏe tốt?',
                'Người nổi tiếng nào bạn yêu thích?',
                'Bạn có thể kể về cuộc sống trên Sao Hỏa không?',
                'Thành phố nào đẹp nhất trên thế giới?',
                'Bạn có thể giúp tôi làm bài tập về nhà không?',
                'Cuộc chiến nào quan trọng nhất trong lịch sử nhân loại?',
                'Ai là tác giả của truyện Harry Potter?',
                'Bạn có thể cho tôi một mẹo học tập không?',
                'Thành phố nào có nhiều dân cư nhất trên thế giới?',
                'Làm sao để nấu món ăn Việt Nam ngon?',
                'Tại sao chúng ta cần uống nước?',
                'Bạn có thể kể một câu chuyện kinh dị không?',
                'Tại sao mùa đông lại lạnh?',
                'Làm sao để trở nên giỏi toán?',
                'Thành phố nào có nhiều du khách nhất?',
                'Ai là người phát minh ra internet?',
                'Bạn có thể kể một câu chuyện cổ tích không?',
                'Làm sao để chơi cờ vua giỏi?',
                'Tại sao biển lại có màu xanh?',
                'Ai là nhạc sĩ nổi tiếng nhất thế giới?',
                'Làm sao để tiết kiệm tiền hiệu quả?',
                'Bạn có biết bài hát nổi tiếng nào không?',
                'Tại sao cần phải bảo vệ môi trường?',
                'Ai là người tạo ra Facebook?',
                'Bạn có thể kể một câu chuyện tình yêu không?',
                'Làm sao để vượt qua kỳ thi tốt nghiệp?',
                'Thành phố nào có nhiều bảo tàng nhất?',
                'Tại sao trời mưa?',
                'Bạn có thể giúp tôi lên kế hoạch du lịch không?',
                'Ai là người nổi tiếng trong lĩnh vực khoa học?',
                'Làm sao để học giỏi tiếng Anh?',
                'Tại sao chúng ta cần phải ngủ?',
                'Bạn có thể kể một câu chuyện hài hước không?',
                'Tại sao cá lại sống dưới nước?',
                'Ai là người phát minh ra máy bay?',
                'Bạn có biết tác giả nổi tiếng nào không?',
                'Làm sao để quản lý thời gian hiệu quả?',
                'Thành phố nào có nhiều cây xanh nhất?',
                'Tại sao chúng ta cần phải làm việc?',
                'Bạn có thể kể một câu chuyện khoa học viễn tưởng không?',
                'Tại sao chúng ta lại có giấc mơ?',
                'Bạn có thể giúp tôi tìm hiểu về lịch sử Việt Nam không?',
                'Ai là nhà văn nổi tiếng nhất thế giới?',
                'Làm sao để học giỏi môn vật lý?',
                'Tại sao cây cần ánh sáng mặt trời?',
                'Bạn có thể kể một câu chuyện ngụ ngôn không?',
                'Tại sao chúng ta có ngày và đêm?',
                'Bạn có thể giúp tôi tìm hiểu về thiên nhiên không?',
                'Ai là người phát minh ra điện thoại di động?',
                'Làm sao để trở thành người giỏi giao tiếp?',
                'Tại sao chúng ta cần phải ăn uống đủ chất?',
                'Bạn có thể kể một câu chuyện trinh thám không?',
                'Thành phố nào có nhiều di sản văn hóa nhất?',
                'Tại sao con người cần phải hít thở?',
                'Bạn có thể giúp tôi tìm hiểu về vũ trụ không?',
                'Ai là người phát minh ra xe đạp?',
                'Làm sao để học giỏi môn toán?',
                'Tại sao băng tuyết lại trắng?',
                'Bạn có thể kể một câu chuyện cổ tích Việt Nam không?',
                'Tại sao con người cần phải giao tiếp?',
                'Bạn có thể giúp tôi tìm hiểu về lịch sử thế giới không?',

            ],
        )

        embedding = Embedding(os.environ['EMBEDDING_MODEL'])

        semanticRouter = SemanticRouter(
            embedding, routes=[productRoute, chitchatRoute],
        )
        return semanticRouter

    def get_json_routesEmbedding(self, path: str):
        with open(path) as f:
            routesEmbedding = json.load(f)
        return routesEmbedding
