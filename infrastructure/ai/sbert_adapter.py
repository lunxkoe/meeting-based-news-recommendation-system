from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Optional
import torch

# [Singleton Pattern] 모델 전역 변수
sbert_model = None

def get_sbert_model():
    global sbert_model
    if sbert_model is None:
        print("[GPU Worker] S-BERT 모델 로드 중 (paraphrase-multilingual-MiniLM-L12-v2)...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        sbert_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device=device)
        print(f"[GPU Worker] 모델 로드 완료 (Device: {device})")
    return sbert_model

class SbertAdapter:
    def calculate_similarity(
        self, 
        summary_meeting: str, 
        news_items: List[Dict[str, Optional[str]]],
        top_k: int = 5
    ) -> List[Dict[str, Optional[str]]]:
        
        # 1. 모델 로드
        model = get_sbert_model()
        if not model:
            print("[Error] 모델 로드 실패. 기본 뉴스 반환.")
            return news_items[:top_k]

        # 유효한 뉴스 필터링
        valid_items = [item for item in news_items if item.get('original')]
        if not valid_items:
            return []

        print(f"\n[S-BERT] 분석 시작: 회의록 요약본 vs 뉴스 {len(valid_items)}개")

        # 2. 임베딩 (Vectorization)
        meeting_embedding = model.encode(summary_meeting, convert_to_tensor=True)
        corpus_texts = [item['original'] for item in valid_items]
        corpus_embeddings = model.encode(corpus_texts, convert_to_tensor=True)
        
        # 3. 코사인 유사도 계산
        # cosine_scores는 1차원 텐서 (크기: 뉴스 개수)
        cosine_scores = util.cos_sim(meeting_embedding, corpus_embeddings)[0]

        # ------------------------------------------------------------------
        # [Log 1] 전체 뉴스 유사도 출력
        # ------------------------------------------------------------------
        print("-" * 60)
        print(f"[S-BERT Debug] 전체 {len(valid_items)}개 뉴스 유사도 점수:")
        print("-" * 60)
        
        # (점수, 인덱스) 쌍 생성
        scores_indices = list(zip(cosine_scores, range(len(valid_items))))
        
        for i, (score, idx) in enumerate(scores_indices):
            title = valid_items[idx].get('title', '제목 없음')
            # score.item()으로 텐서에서 실수값 추출
            print(f"  [{i+1:02d}] Score: {score.item():.4f} | Title: {title[:40]}...")

        # 4. 정렬 및 상위 Top-K 추출
        sorted_scores = sorted(scores_indices, key=lambda x: x[0], reverse=True)
        top_results = sorted_scores[:top_k]
        
        # 5. 최종 뉴스 리스트 구성
        top_indices = [idx for score, idx in top_results]
        selected_news = [valid_items[i] for i in top_indices]

        # ------------------------------------------------------------------
        # [Log 2] 선별된 Top-K 뉴스 유사도 출력
        # ------------------------------------------------------------------
        print("-" * 60)
        print(f"[S-BERT Debug] 최종 선별된 Top {len(selected_news)} 뉴스:")
        print("-" * 60)
        
        for rank, (score, idx) in enumerate(top_results):
            title = valid_items[idx].get('title', '제목 없음')
            print(f"  [Rank {rank+1}] Score: {score.item():.4f} | Title: {title}")
        print("-" * 60)
        print(f"[S-BERT] 분석 완료.\n")

        return selected_news